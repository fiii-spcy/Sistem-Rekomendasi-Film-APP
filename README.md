# Sistem Klasifikasi & Pencarian Film - Streamlit App

Aplikasi Streamlit untuk klasifikasi dan pencarian film berdasarkan kondisi emosional.

## Struktur File

- `app.py` - Aplikasi Streamlit utama
- `index.py` - Handler untuk Vercel serverless functions
- `requirements.txt` - Dependencies Python
- `disney_movies_with_posters.csv` - Dataset film

## Catatan Penting untuk Deployment

### ⚠️ Vercel dan Streamlit

Streamlit memerlukan server yang berjalan secara persisten, sedangkan Vercel menggunakan fungsi serverless yang stateless. Ini membuat deployment Streamlit langsung ke Vercel menjadi tidak ideal.

### Opsi Deployment yang Disarankan:

1. **Streamlit Cloud** (Paling Mudah - GRATIS)
   - Kunjungi https://streamlit.io/cloud
   - Connect repository GitHub Anda
   - Deploy otomatis

2. **Railway** (Alternatif Bagus)
   - Kunjungi https://railway.app
   - Deploy dari GitHub
   - Gratis dengan batasan tertentu

3. **Render** (Alternatif)
   - Kunjungi https://render.com
   - Pilih "Web Service"
   - Gunakan command: `streamlit run app.py --server.port=$PORT`

### Jika Tetap Ingin Menggunakan Vercel:

Untuk Vercel, pertimbangkan untuk mengkonversi aplikasi menjadi REST API dengan FastAPI atau Flask, kemudian buat frontend terpisah.

## Instalasi Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Requirements

Semua dependencies tercantum di `requirements.txt`.

