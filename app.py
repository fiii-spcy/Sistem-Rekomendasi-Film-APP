import pandas as pd
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import os

# =============================================================
# === KONFIGURASI STREAMLIT ===
# =============================================================
st.set_page_config(
    page_title="Sistem Klasifikasi & Pencarian Film",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================
# === DEFINISI PEMETAAN DAN MODEL TRAINING ===
# =============================================================

def map_genre_to_class(genre, title):
    """
    Memetakan genre/judul film ke salah satu dari 5 kelas emosional/genre utama.
    """
    g = str(genre).lower()
    t = str(title).lower()
    
    # Kelas 1: COMEDY / KEGEMBIRAAN
    if 'comedy' in g or 'musical' in g or 'animation' in g:
        return 1, "lucu bahagia komedi tawa senang gembira pesta"  
    # Kelas 2: ACTION / ADVENTURE / KEMARAHAN
    elif 'action' in g or 'adventure' in g or 'fantasy' in g:
        return 2, "perang marah tembak aksi pertarungan petualangan berani"
    # Kelas 3: DRAMA / EMOSIONAL / SEDIH/SAKIT HATI
    elif 'drama' in g or 'romantic' in g: 
        return 3, "sedih nangis emosi hati drama romantis sakit galau"
    # Kelas 4: HORROR / MYSTERY / TAKUT/CEMAS
    elif 'horror' in g or 'mystery' in g or 'thriller' in g:
        return 4, "takut cemas misteri tegang horor hantu gelap"
    # Kelas 5: FAMILY / LAINNYA / NETRAL
    else:
        return 5, "keluarga netral pendidikan sejarah biografi"

KELAS_MAP = {
    1: "COMEDY / KEGEMBIRAAN",
    2: "ACTION / ADVENTURE / KEMARAHAN",
    3: "DRAMA / EMOSIONAL / SEDIH/SAKIT HATI",
    4: "HORROR / MYSTERY / TAKUT/CEMAS",
    5: "FAMILY / LAINNYA / NETRAL"
}
KELAS_LABELS = list(KELAS_MAP.values())

# =============================================================
# === LOAD DATA DAN TRAIN MODEL (CACHED) ===
# =============================================================

@st.cache_data
def load_data():
    """Memuat data film dari CSV."""
    csv_path = "disney_movies_with_posters.csv"
    # Coba beberapa lokasi file
    possible_paths = [
        csv_path,
        f"../{csv_path}",
        f"./{csv_path}",
        os.path.join(os.path.dirname(__file__), csv_path),
        os.path.join(os.path.dirname(__file__), "..", csv_path)
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path).copy()
            if 'poster_url' not in df.columns:
                df['poster_url'] = None
            return df
    
    st.error("File 'disney_movies_with_posters.csv' tidak ditemukan!")
    return None

@st.cache_resource
def train_knn_multiclass_classifier(df):
    """Melatih model KNN Klasifikasi Multikelas dan memuat data film."""
    if df is None:
        return None, None, None, None, None
    
    # Buat copy untuk menghindari modifikasi DataFrame asli
    df_processed = df.copy()
    
    results = df_processed.apply(lambda row: map_genre_to_class(row['genre'], row['movie_title']), axis=1, result_type='expand')
    df_processed['target_class'] = results[0]
    df_processed['keyword_boost'] = results[1]

    df_processed['features'] = df_processed['genre'].fillna('') + " " + df_processed['movie_title'].fillna('') + " " + df_processed['keyword_boost']
    df_processed['features'] = df_processed['features'].str.lower()
    df_processed['movie_title_lower'] = df_processed['movie_title'].fillna('').str.lower()

    X = df_processed['features']
    y = df_processed['target_class']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    tfidf = TfidfVectorizer(stop_words='english')
    X_train_tfidf = tfidf.fit_transform(X_train)
    
    K = 7 
    knn_model = KNeighborsClassifier(n_neighbors=K, metric='cosine')
    knn_model.fit(X_train_tfidf, y_train)
    
    # Kembalikan DataFrame yang sudah diproses juga
    return knn_model, tfidf, X_test, y_test, df_processed

# =============================================================
# === FUNGSI HELPER ===
# =============================================================

def load_image_from_url(url):
    """Mengunduh dan memuat gambar dari URL."""
    try:
        if pd.isna(url) or not url:
            return None
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        return None

def display_poster(url, width=150):
    """Menampilkan poster film."""
    img = load_image_from_url(url)
    if img:
        st.image(img, width=width)
    else:
        st.image(Image.new('RGB', (width, int(width*1.5)), color='gray'), width=width)

@st.cache_data(ttl=3600)  # Cache selama 1 jam
def get_movie_details_from_tmdb(movie_title, release_year=None, genre=None):
    """
    Mengambil detail film dari TMDB API.
    Note: TMDB API memerlukan API key. Fungsi ini akan mencoba fetch jika ada API key,
    atau menggunakan deskripsi generik berdasarkan genre dan title.
    """
    try:
        # Cek apakah ada TMDB API key (opsional)
        tmdb_api_key = os.environ.get('TMDB_API_KEY', '')
        
        if tmdb_api_key:
            # Extract year dari release_date jika ada
            if release_year is None or (isinstance(release_year, str) and '-' in str(release_year)):
                try:
                    release_year = int(str(release_year).split('-')[0])
                except:
                    release_year = None
            
            # Search movie di TMDB
            search_url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": tmdb_api_key,
                "query": movie_title,
                "language": "en-US"
            }
            if release_year:
                params["year"] = release_year
            
            response = requests.get(search_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    movie = data['results'][0]
                    movie_id = movie.get('id')
                    
                    if movie_id:
                        # Get detailed info
                        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
                        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
                        
                        details_response = requests.get(details_url, params={"api_key": tmdb_api_key, "language": "en-US"}, timeout=5)
                        credits_response = requests.get(credits_url, params={"api_key": tmdb_api_key, "language": "en-US"}, timeout=5)
                        
                        details = details_response.json() if details_response.status_code == 200 else {}
                        credits = credits_response.json() if credits_response.status_code == 200 else {}
                        
                        cast_list = []
                        if credits.get('cast'):
                            cast_list = [actor['name'] for actor in credits['cast'][:5]]
                        
                        return {
                            'overview': details.get('overview', movie.get('overview', '')),
                            'cast': cast_list,
                            'rating': details.get('vote_average', movie.get('vote_average', 0)),
                            'runtime': details.get('runtime', 0),
                            'release_date': details.get('release_date', movie.get('release_date', '')),
                            'tagline': details.get('tagline', ''),
                            'popularity': details.get('popularity', movie.get('popularity', 0))
                        }
    except Exception as e:
        pass  # Fall through to default description
    
    # Fallback: Generate description berdasarkan genre dan title
    genre_str = str(genre) if genre else "Disney"
    genre_lower = genre_str.lower()
    
    # Generate deskripsi berdasarkan genre
    if 'comedy' in genre_lower or 'musical' in genre_lower:
        overview = f"'{movie_title}' adalah film Disney yang penuh dengan tawa, musik, dan kegembiraan. Film ini menghadirkan cerita yang menghibur dengan karakter-karakter yang menggemaskan dan lagu-lagu yang tak terlupakan."
        cast_examples = ["Karakter utama yang penuh semangat", "Karakter pendukung yang lucu", "Karakter antagonis yang unik"]
    elif 'action' in genre_lower or 'adventure' in genre_lower:
        overview = f"'{movie_title}' membawa penonton ke dalam petualangan epik yang penuh aksi dan keberanian. Film ini menampilkan perjalanan heroik dengan tantangan yang menegangkan."
        cast_examples = ["Pahlawan utama yang berani", "Teman setia", "Penjahat yang menantang"]
    elif 'drama' in genre_lower or 'romantic' in genre_lower:
        overview = f"'{movie_title}' adalah kisah emosional yang menyentuh hati. Film ini mengisahkan tentang cinta, persahabatan, dan perjalanan hidup yang penuh makna."
        cast_examples = ["Karakter utama yang penuh perasaan", "Karakter romantis", "Karakter pendukung yang setia"]
    elif 'horror' in genre_lower or 'mystery' in genre_lower or 'thriller' in genre_lower:
        overview = f"'{movie_title}' adalah film yang penuh misteri dan ketegangan. Film ini menghadirkan cerita yang menegangkan dengan plot twist yang mengejutkan."
        cast_examples = ["Karakter utama yang berani", "Karakter misterius", "Karakter antagonis yang menakutkan"]
    else:
        overview = f"'{movie_title}' adalah film Disney klasik yang menghadirkan cerita yang menghibur dan menginspirasi. Film ini cocok untuk ditonton bersama keluarga dengan pesan moral yang positif."
        cast_examples = ["Karakter utama yang menginspirasi", "Karakter pendukung yang setia", "Karakter yang bijaksana"]
    
    return {
        'overview': overview,
        'cast': cast_examples,
        'rating': 7.5,  # Default rating
        'runtime': 90,  # Default runtime
        'release_date': '',
        'tagline': f"Kisah tak terlupakan dari {movie_title}",
        'popularity': 0
    }

def format_runtime(minutes):
    """Format runtime dari menit ke jam dan menit."""
    if not minutes or minutes == 0:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"

def display_movie_card(movie, show_details=True):
    """Menampilkan card film dengan informasi lengkap."""
    with st.container():
        # Ambil detail tambahan
        release_year = None
        if pd.notna(movie.get('release_date')):
            try:
                release_year = int(str(movie['release_date']).split('-')[0])
            except:
                pass
        
        genre = movie.get('genre', '')
        movie_details = get_movie_details_from_tmdb(movie['movie_title'], release_year, genre) if show_details else None
        
        # Layout: Poster di kiri, Info di kanan
        col_poster, col_info = st.columns([1, 2])
        
        with col_poster:
            display_poster(movie['poster_url'], width=200)
        
        with col_info:
            st.markdown(f"### 🎬 {movie['movie_title']}")
            
            # Info dasar
            info_cols = st.columns(3)
            with info_cols[0]:
                if pd.notna(movie.get('genre')):
                    st.markdown(f"**Genre:** {movie['genre']}")
            with info_cols[1]:
                if pd.notna(movie.get('release_date')):
                    st.markdown(f"**Rilis:** {movie['release_date']}")
            with info_cols[2]:
                predicted_label = KELAS_MAP.get(movie.get('target_class'), 'N/A')
                st.markdown(f"**Kategori:** {predicted_label}")
            
            # Rating dan Runtime
            if movie_details and movie_details.get('rating', 0) > 0:
                rating_cols = st.columns(3)
                with rating_cols[0]:
                    st.markdown(f"⭐ **Rating:** {movie_details['rating']:.1f}/10")
                with rating_cols[1]:
                    if movie_details.get('runtime', 0) > 0:
                        st.markdown(f"⏱️ **Durasi:** {format_runtime(movie_details['runtime'])}")
                with rating_cols[2]:
                    if pd.notna(movie.get('mpaa_rating')):
                        st.markdown(f"**Rating:** {movie['mpaa_rating']}")
            
            # Deskripsi
            if movie_details and movie_details.get('overview'):
                with st.expander("📖 Deskripsi Film", expanded=False):
                    st.write(movie_details['overview'])
            
            # Cast
            if movie_details and movie_details.get('cast') and len(movie_details['cast']) > 0:
                with st.expander("👥 Pemeran & Karakter", expanded=False):
                    cast_list = movie_details['cast']
                    # Cek apakah ini nama aktor (pendek) atau deskripsi karakter (panjang)
                    first_item = cast_list[0] if cast_list else ""
                    if len(first_item) < 50 and not any(keyword in first_item.lower() for keyword in ['karakter', 'yang', 'penuh', 'utama']):
                        # Ini nama aktor dari API
                        cast_text = " • ".join(cast_list)
                        st.write(cast_text)
                    else:
                        # Ini deskripsi karakter (fallback)
                        for char_desc in cast_list:
                            st.write(f"• {char_desc}")
            
            # Tagline
            if movie_details and movie_details.get('tagline'):
                st.info(f"💬 *{movie_details['tagline']}*")
            
            # Box Office (jika ada)
            box_office_info = []
            if pd.notna(movie.get('total_gross')):
                try:
                    gross = float(movie['total_gross'])
                    if gross > 0:
                        box_office_info.append(f"💰 **Box Office:** ${gross:,.0f}")
                except:
                    pass
            
            if pd.notna(movie.get('inflation_adjusted_gross')):
                try:
                    adj_gross = float(movie['inflation_adjusted_gross'])
                    if adj_gross > 0:
                        box_office_info.append(f"📈 **Disesuaikan Inflasi:** ${adj_gross:,.0f}")
                except:
                    pass
            
            if box_office_info:
                st.markdown(" | ".join(box_office_info))
        
        st.markdown("---")

# =============================================================
# === MAIN APP ===
# =============================================================

# Load data
df_movies_raw = load_data()

if df_movies_raw is None:
    st.stop()

# Train model (ini akan mengembalikan DataFrame yang sudah diproses)
knn_model, tfidf_vectorizer, X_test_eval, y_test_eval, df_movies = train_knn_multiclass_classifier(df_movies_raw)

if knn_model is None:
    st.error("Gagal melatih model!")
    st.stop()

# =============================================================
# === UI STREAMLIT ===
# =============================================================

# Header
st.title("🎬 Sistem Klasifikasi & Pencarian Film")
st.markdown("---")

# Sidebar untuk evaluasi
with st.sidebar:
    st.header("📊 Evaluasi Model")
    if st.button("📈 Tampilkan Plot Visualisasi", type="primary"):
        st.session_state.show_plots = True
    
    if st.button("🔄 Reset Plot"):
        st.session_state.show_plots = False

# Tabs untuk dua mode
tab1, tab2 = st.tabs(["🎭 Mode 1: Klasifikasi Emosional", "🔍 Mode 2: Pencarian Judul"])

# =============================================================
# === TAB 1: KLASIFIKASI EMOSIONAL ===
# =============================================================

with tab1:
    st.header("Klasifikasi Emosional / Psikologis")
    st.markdown("Masukkan kondisi psikologis/emosi Anda untuk mendapatkan rekomendasi film.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_input(
            "Ketik Kondisi Psikologis/Emosi:",
            placeholder="Contoh: sedih, bahagia, takut, marah...",
            key="emotion_input"
        )
    
    with col2:
        st.write("")  # Spacing
        predict_button = st.button("🔮 PREDIKSI", type="primary", use_container_width=True)
    
    if predict_button or user_input:
        if not user_input or not user_input.strip():
            st.warning("⚠️ Masukkan kondisi psikologis/emosi Anda.")
        else:
            with st.spinner("Memprediksi dan mencari rekomendasi..."):
                user_vector = tfidf_vectorizer.transform([user_input.lower().strip()])
                predicted_class = knn_model.predict(user_vector)[0]
                predicted_label = KELAS_MAP.get(predicted_class, "TIDAK DIKETAHUI")
                
                st.success(f"**PREDIKSI KELAS:** {predicted_label}")
                
                recommended_movies = df_movies[df_movies['target_class'] == predicted_class]
                
                if not recommended_movies.empty:
                    num_to_sample = min(3, len(recommended_movies))
                    random_movies = recommended_movies.sample(n=num_to_sample)
                    
                    st.subheader("🎬 Film Rekomendasi:")
                    st.markdown("---")
                    
                    # Tampilkan film dengan card lengkap
                    for idx, (index, movie) in enumerate(random_movies.iterrows()):
                        display_movie_card(movie, show_details=True)
                else:
                    st.warning("Tidak ada film yang ditemukan untuk kelas ini.")

# =============================================================
# === TAB 2: PENCARIAN JUDUL ===
# =============================================================

with tab2:
    st.header("Pencarian Berdasarkan Judul Film")
    st.markdown("Cari film berdasarkan judul atau kata kunci.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_input = st.text_input(
            "Ketik Judul Film/Kata Kunci:",
            placeholder="Contoh: Snow White, Pinocchio...",
            key="title_input"
        )
    
    with col2:
        st.write("")  # Spacing
        search_button = st.button("🔍 CARI FILM", type="primary", use_container_width=True)
    
    if search_button or search_input:
        if not search_input or not search_input.strip():
            st.warning("⚠️ Masukkan judul film atau kata kunci.")
        else:
            with st.spinner("Mencari film..."):
                results = df_movies[df_movies['movie_title_lower'].str.contains(search_input.lower().strip(), na=False)]
                
                if results.empty:
                    st.error(f"Film dengan judul/kata kunci '{search_input}' tidak ditemukan.")
                else:
                    st.success(f"🎯 Ditemukan **{len(results)}** film")
                    st.markdown("---")
                    
                    # Tampilkan hasil dengan card lengkap (maksimal 5 hasil)
                    for idx, (index, row) in enumerate(results.head(5).iterrows()):
                        display_movie_card(row, show_details=True)

# =============================================================
# === PLOT VISUALISASI (dalam sidebar atau expander) ===
# =============================================================

if st.session_state.get('show_plots', False):
    st.sidebar.markdown("---")
    
    with st.expander("📊 Visualisasi Kinerja Model", expanded=True):
        st.subheader("Hasil Evaluasi Model KNN Klasifikasi Multikelas")
        
        with st.spinner("Menghitung metrik dan membuat plot..."):
            X_test_tfidf = tfidf_vectorizer.transform(X_test_eval)
            y_pred = knn_model.predict(X_test_tfidf)
            
            cm = confusion_matrix(y_test_eval, y_pred, labels=list(KELAS_MAP.keys()))
            accuracy = knn_model.score(X_test_tfidf, y_test_eval)
            
            st.metric("Akurasi Model (Overall)", f"{accuracy:.4f}")
            
            # Plot 1: Aktual vs Prediksi
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            ax1.scatter(range(len(y_test_eval)), y_test_eval, color='green', label='Aktual (y_test)', alpha=0.6)
            ax1.scatter(range(len(y_pred)), y_pred, marker='x', color='red', label='Prediksi (y_pred)', alpha=0.6)
            ax1.set_yticks(list(KELAS_MAP.keys()))
            ax1.set_yticklabels(KELAS_LABELS)
            ax1.set_title('Aktual vs Prediksi Kelas Film')
            ax1.set_xlabel('Indeks Sampel Data Testing')
            ax1.set_ylabel('Kelas Prediksi')
            ax1.grid(True, alpha=0.5)
            ax1.legend()
            plt.tight_layout()
            st.pyplot(fig1)
            
            # Plot 2: Confusion Matrix
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Reds', cbar=True, ax=ax2,
                        xticklabels=KELAS_LABELS, yticklabels=KELAS_LABELS)
            ax2.set_title(f'Confusion Matrix (Heatmap) {len(KELAS_MAP)}x{len(KELAS_LABELS)}')
            ax2.set_xlabel('Prediksi')
            ax2.set_ylabel('Aktual')
            plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            plt.tight_layout()
            st.pyplot(fig2)
            
            # Tampilkan confusion matrix sebagai tabel
            st.subheader("Matriks Kebingungan (Tabel)")
            cm_df = pd.DataFrame(cm, index=KELAS_LABELS, columns=KELAS_LABELS)
            st.dataframe(cm_df, use_container_width=True)

