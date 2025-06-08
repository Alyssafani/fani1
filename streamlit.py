import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import google.generativeai as genai
import os

# Konfigurasi kunci API Gemini
# PERINGATAN: Menulis kunci API langsung dalam kode tidak disarankan untuk produksi.
# Gunakan variabel lingkungan atau manajemen rahasia yang aman untuk aplikasi yang disebarkan.
# genai.configure(api_key=os.environ["GEMINI_API_KEY"]) # Baris asli yang membaca dari variabel lingkungan
genai.configure(api_key="AIzaSyCWSQEkNkWbFY9AHwYGb1OKwyPt4McB7bY") # Kunci API diperbarui sesuai permintaan Anda

# Buat model Gemini
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Styling CSS Kustom untuk estetika Coquette ---
st.markdown(
    """
    <style>
    .reportview-container {
        background: #FFF0F5; /* Light pink background */
    }
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        background-color: #FFFFFF;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 2px solid #FFC0CB; /* Soft pink border */
    }
    h1 {
        color: #C06C84; /* Darker pink for headings */
        font-family: serif;
        text-align: center;
        font-size: 3em;
        margin-bottom: 0.5em;
    }
    h2 {
        color: #F67280; /* Medium pink for subheadings */
        font-family: serif;
        font-size: 2em;
        margin-top: 1.5em;
        margin-bottom: 1em;
    }
    h3 {
        color: #6C5B7B; /* Purple-ish for insights */
        font-family: sans-serif;
        font-size: 1.2em;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    .stFileUploader label {
        color: #C06C84;
        font-weight: bold;
    }
    .stSelectbox label, .stDateInput label {
        color: #F67280;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #FFC0CB; /* Coquette pink button */
        color: white !important;
        border-radius: 20px;
        border: none;
        padding: 10px 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #F8B195;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .stAlert {
        border-radius: 10px;
        background-color: #FEE7F2; /* Lighter pink for alerts */
        color: #C06C84;
    }
    .css-1d391kg { /* Target specific Streamlit elements for rounded corners */
        border-radius: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Judul Aplikasi ---
st.title("🎀 Dasbor Kampanye Media Sosial Coquette 🎀")
st.markdown("Unggah CSV Anda untuk memvisualisasikan wawasan media sosial dengan sentuhan menawan.")

# --- Unggah File CSV ---
uploaded_file = st.file_uploader("Unggah File CSV Anda", type=["csv"])

df = pd.DataFrame() # Inisialisasi DataFrame kosong

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # --- Pembersihan Data ---
        # Ubah 'Date' ke format datetime, tangani kesalahan konversi
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Isi 'Engagements' yang kosong dengan 0, konversi ke int
        df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce').fillna(0).astype(int)

        # Isi nilai yang hilang dengan 'Unknown' untuk kolom kategori
        for col in ['Platform', 'Sentiment', 'Media Type', 'Location']:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
            else: # Buat kolom jika tidak ada untuk menghindari KeyError
                df[col] = 'Unknown'

        # Hapus baris dengan tanggal yang tidak valid (NaN dari 'coerce')
        df.dropna(subset=['Date'], inplace=True)
        
        # Urutkan data berdasarkan tanggal
        df.sort_values(by='Date', inplace=True)

        st.success(f"Berhasil memuat {len(df)} catatan.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat atau membersihkan data: {e}")
        df = pd.DataFrame() # Reset DataFrame jika ada kesalahan

# Pastikan df bukan kosong sebelum melanjutkan
if not df.empty:
    # --- Filter Data ---
    st.header("📊 Filter Data")

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_platform = st.selectbox("Platform", options=["All"] + df['Platform'].unique().tolist())
    with col2:
        selected_sentiment = st.selectbox("Sentimen", options=["All"] + df['Sentiment'].unique().tolist())
    with col3:
        selected_media_type = st.selectbox("Jenis Media", options=["All"] + df['Media Type'].unique().tolist())

    col4, col5 = st.columns(2)
    with col4:
        selected_location = st.selectbox("Lokasi", options=["All"] + df['Location'].unique().tolist())
    with col5:
        min_date = df['Date'].min().to_pydatetime().date() if not df['Date'].empty else pd.Timestamp.now().date()
        max_date = df['Date'].max().to_pydatetime().date() if not df['Date'].empty else pd.Timestamp.now().date()
        
        date_range = st.date_input("Rentang Tanggal", value=(min_date, max_date) if not df['Date'].empty else (pd.Timestamp.now().date(), pd.Timestamp.now().date()))
        
        start_date = date_range[0]
        end_date = date_range[1] if len(date_range) > 1 else date_range[0]


    filtered_df = df.copy()
    if selected_platform != "All":
        filtered_df = filtered_df[filtered_df['Platform'] == selected_platform]
    if selected_sentiment != "All":
        filtered_df = filtered_df[filtered_df['Sentiment'] == selected_sentiment]
    if selected_media_type != "All":
        filtered_df = filtered_df[filtered_df['Media Type'] == selected_media_type]
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df['Location'] == selected_location]

    # Filter tanggal
    filtered_df = filtered_df[
        (filtered_df['Date'].dt.date >= start_date) &
        (filtered_df['Date'].dt.date <= end_date)
    ]

    st.subheader("Visualisasi & Wawasan")

    # Fungsi untuk mendapatkan wawasan dari LLM
    @st.cache_data(show_spinner="Menghasilkan wawasan dengan AI...")
    def get_llm_insight(prompt_text):
        try:
            response = model.generate_content(prompt_text)
            # LLM akan mengembalikan respons dalam format JSON dengan 'text' part.
            # Pastikan untuk mengaksesnya dengan benar
            return response.text
        except Exception as e:
            st.error(f"Gagal menghasilkan wawasan dari AI: {e}")
            return "Wawasan tidak dapat dihasilkan saat ini."

    # --- 1. Pie Chart: Sentiment Breakdown ---
    st.subheader("💖 Pecahan Sentimen")
    if not filtered_df.empty:
        sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        fig_sentiment = px.pie(sentiment_counts, values='Count', names='Sentiment',
                                title='Distribusi Sentimen Konten',
                                color_discrete_sequence=COQUETTE_COLORS)
        fig_sentiment.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        fig_sentiment.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_sentiment, use_container_width=True)
        insight_sentiment = get_llm_insight(
            f"Berikan 3 wawasan ringkas untuk grafik pecahan sentimen berdasarkan data ini: {sentiment_counts.to_dict('records')}. "
            "Setiap wawasan harus berupa poin-poin singkat yang dapat ditindaklanjuti."
        )
        st.markdown(f"### ✨ Wawasan:")
        st.markdown(insight_sentiment)
    else:
        st.info("Tidak ada data untuk menampilkan Pecahan Sentimen.")

    # --- 2. Line Chart: Engagement Trend over Time ---
    st.subheader("📈 Tren Engagement Seiring Waktu")
    if not filtered_df.empty:
        # Agregasi engagement per tanggal
        engagement_trend = filtered_df.groupby(filtered_df['Date'].dt.to_period('D'))['Engagements'].sum().reset_index()
        engagement_trend['Date'] = engagement_trend['Date'].dt.to_timestamp() # Kembali ke timestamp untuk Plotly
        fig_trend = px.line(engagement_trend, x='Date', y='Engagements',
                            title='Tren Engagement Harian',
                            line_shape='spline',
                            color_discrete_sequence=[COQUETTE_COLORS[0]])
        fig_trend.update_layout(xaxis_title="Tanggal", yaxis_title="Jumlah Engagement")
        st.plotly_chart(fig_trend, use_container_width=True)
        insight_trend = get_llm_insight(
            f"Berikan 3 wawasan ringkas untuk grafik tren engagement seiring waktu berdasarkan data ini: {engagement_trend.to_dict('records')}. "
            "Fokus pada periode puncak, lembah, dan pertumbuhan/penurunan."
        )
        st.markdown(f"### ✨ Wawasan:")
        st.markdown(insight_trend)
    else:
        st.info("Tidak ada data untuk menampilkan Tren Engagement.")

    # --- 3. Bar Chart: Platform Engagements ---
    st.subheader("📱 Engagement Platform")
    if not filtered_df.empty:
        platform_engagement = filtered_df.groupby('Platform')['Engagements'].sum().reset_index()
        platform_engagement = platform_engagement.sort_values(by='Engagements', ascending=False)
        fig_platform = px.bar(platform_engagement, x='Platform', y='Engagements',
                                title='Total Engagement per Platform',
                                color='Platform',
                                color_discrete_sequence=COQUETTE_COLORS)
        fig_platform.update_layout(xaxis_title="Platform", yaxis_title="Total Engagement")
        st.plotly_chart(fig_platform, use_container_width=True)
        insight_platform = get_llm_insight(
            f"Berikan 3 wawasan ringkas untuk grafik engagement platform berdasarkan data ini: {platform_engagement.to_dict('records')}. "
            "Soroti platform berkinerja terbaik dan terlemah."
        )
        st.markdown(f"### ✨ Wawasan:")
        st.markdown(insight_platform)
    else:
        st.info("Tidak ada data untuk menampilkan Engagement Platform.")

    # --- 4. Pie Chart: Media Type Mix ---
    st.subheader("🖼️ Campuran Jenis Media")
    if not filtered_df.empty:
        media_type_counts = filtered_df['Media Type'].value_counts().reset_index()
        media_type_counts.columns = ['Media Type', 'Count']
        fig_media_type = px.pie(media_type_counts, values='Count', names='Media Type',
                                title='Distribusi Jenis Media',
                                color_discrete_sequence=COQUETTE_COLORS)
        fig_media_type.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        fig_media_type.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_media_type, use_container_width=True)
        insight_media_type = get_llm_insight(
            f"Berikan 3 wawasan ringkas untuk grafik campuran jenis media berdasarkan data ini: {media_type_counts.to_dict('records')}. "
            "Identifikasi jenis media yang paling banyak digunakan dan sarankan optimasi."
        )
        st.markdown(f"### ✨ Wawasan:")
        st.markdown(insight_media_type)
    else:
        st.info("Tidak ada data untuk menampilkan Campuran Jenis Media.")

    # --- 5. Bar Chart: Top 5 Locations ---
    st.subheader("📍 5 Lokasi Teratas")
    if not filtered_df.empty:
        location_engagement = filtered_df.groupby('Location')['Engagements'].sum().reset_index()
        location_engagement = location_engagement.sort_values(by='Engagements', ascending=False).head(5)
        fig_location = px.bar(location_engagement, x='Location', y='Engagements',
                                title='Total Engagement per Lokasi (5 Teratas)',
                                color='Location',
                                color_discrete_sequence=COQUETTE_COLORS)
        fig_location.update_layout(xaxis_title="Lokasi", yaxis_title="Total Engagement")
        st.plotly_chart(fig_location, use_container_width=True)
        insight_location = get_llm_insight(
            f"Berikan 3 wawasan ringkas untuk grafik 5 lokasi teratas berdasarkan data ini: {location_engagement.to_dict('records')}. "
            "Fokus pada wilayah geografis yang paling terlibat."
        )
        st.markdown(f"### ✨ Wawasan:")
        st.markdown(insight_location)
    else:
        st.info("Tidak ada data untuk menampilkan 5 Lokasi Teratas.")

    # --- Ringkasan Strategi Kampanye ---
    st.header("📝 Ringkasan Strategi Kampanye")
    if not df.empty: # Gunakan df asli untuk ringkasan kampanye keseluruhan
        campaign_summary_text = get_llm_insight(
            f"Berdasarkan data kampanye media sosial berikut, berikan ringkasan strategi kampanye yang ringkas (ringkasan tindakan utama) dalam sekitar 3 poin. "
            f"Fokus pada kinerja keseluruhan, sentimen, dan efektivitas platform/jenis media. Data: {df.to_dict('records')}. "
            "Contoh summary: 1. Tingkatkan investasi pada Platform X karena tingginya engagement. 2. Kembangkan konten yang lebih positif untuk mengatasi sentimen negatif di area Y. 3. Diversifikasi penggunaan media Type Z untuk menjangkau audiens baru."
        )
        st.markdown(campaign_summary_text)
        st.session_state['campaign_summary_text'] = campaign_summary_text # Simpan di session state
        # Simpan wawasan juga di session state untuk PDF
        st.session_state['insights'] = {
            'sentiment': insight_sentiment,
            'engagementTrend': insight_trend,
            'platform': insight_platform,
            'mediaType': insight_media_type,
            'location': insight_location
        }
    else:
        st.info("Unggah data untuk melihat ringkasan strategi kampanye.")

    # --- Fitur Ekspor PDF ---
    st.header("📥 Ekspor ke PDF")

    # Fungsi untuk membuat PDF
    def create_pdf(summary_text, insights_dict):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 24)
        c.setFillColorRGB(0.75, 0.42, 0.52) # Darker pink
        c.drawCentredString(width/2.0, height - 50, "Dasbor Kampanye Media Sosial")

        y_position = height - 100
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0.96, 0.45, 0.5) # Medium pink
        c.drawString(50, y_position, "Ringkasan Strategi Kampanye:")
        y_position -= 20
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0.42, 0.36, 0.48) # Purple-ish
        # Split summary into lines to fit page width
        for line in summary_text.split('\n'):
            c.drawString(60, y_position, line.strip())
            y_position -= 15
        y_position -= 20

        # Add Insights
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0.96, 0.45, 0.5) # Medium pink
        c.drawString(50, y_position, "Wawasan Grafik:")
        y_position -= 20
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0.42, 0.36, 0.48) # Purple-ish

        chart_titles = {
            'sentiment': "Pecahan Sentimen",
            'engagementTrend': "Tren Engagement Seiring Waktu",
            'platform': "Engagement Platform",
            'mediaType': "Campuran Jenis Media",
            'location': "5 Lokasi Teratas"
        }

        for key, title in chart_titles.items():
            if insights_dict.get(key):
                c.setFont("Helvetica-BoldOblique", 14)
                c.drawString(60, y_position, f"- {title}:")
                y_position -= 15
                c.setFont("Helvetica", 12)
                for line in insights_dict[key].split('\n'):
                    # Check if line fits on current page
                    if y_position < 50: # Adjust threshold as needed
                        c.showPage()
                        c.setFont("Helvetica", 12)
                        y_position = height - 50 # New page starting position
                    c.drawString(70, y_position, line.strip())
                    y_position -= 15
                y_position -= 10 # Extra space after each chart insight

        c.save()
        return buffer.getvalue()

    if 'campaign_summary_text' in st.session_state and not filtered_df.empty:
        pdf_data = create_pdf(st.session_state['campaign_summary_text'], st.session_state['insights'])
        st.download_button(
            label="Unduh Ringkasan & Wawasan Dashboard (PDF)",
            data=pdf_data,
            file_name="social_media_dashboard_summary.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Unggah data dan tunggu ringkasan dan wawasan dihasilkan sebelum mengekspor PDF.")

else:
    st.info("Silakan unggah file CSV untuk memulai analisis.")



