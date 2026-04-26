RAB Analyzer Kalsel
===================

Aplikasi ini adalah alat bantu profesional untuk menganalisis Rencana Anggaran Biaya (RAB) proyek, membandingkannya dengan database harga lokal Kalimantan Selatan, dan mencari potensi penghematan.

## Struktur Folder:
- `app.py` : Skrip utama UI Streamlit
- `database.py` : Skrip inisialisasi database SQLite lokal Kalsel dengan 100+ item
- `utils.py` : Skrip logika analisis dan pembuatan PDF
- `requirements.txt` : Daftar library Python yang dibutuhkan
- `sample_rab.csv` : Contoh file untuk Anda coba tes upload

## Cara Instalasi dan Menjalankan di Windows (Langkah Pemula):

1. **Install Python**
   Pastikan Anda sudah menginstall Python (minimal versi 3.8+). Download dari python.org.
   Saat instalasi, pastikan mencentang "Add Python to PATH".

2. **Buka Command Prompt (CMD) atau Terminal**
   Masuk ke folder tempat file ini berada:
   ```cmd
   cd "c:\Agent RAB Analyzer"
   ```

3. **Install Library yang Dibutuhkan**
   Ketik perintah berikut dan tekan Enter:
   ```cmd
   pip install -r requirements.txt
   ```
   (Tunggu proses download selesai, butuh koneksi internet).

4. **Jalankan Aplikasi**
   Setelah instalasi selesai, jalankan perintah ini:
   ```cmd
   streamlit run app.py
   ```

5. **Buka Browser**
   Secara otomatis browser Anda (Chrome/Edge) akan terbuka dan menampilkan aplikasi (biasanya di http://localhost:8501).

## Cara Uji Coba:
1. Di menu kiri, pilih "Dashboard Analisis".
2. Pada bagian Upload File, masukkan file `sample_rab.csv`.
3. Tunggu proses loading, dan lihat hasil visualisasinya!

---
Dibuat menggunakan Python & Streamlit.
