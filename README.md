# 🛣️ JalanKita

<div align="center">

![JalanKita Banner](https://img.shields.io/badge/JalanKita-AI%20Civic%20Platform-0369a1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-AI_Powered-4285f4?style=for-the-badge&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)

**Platform crowdsourcing pelaporan infrastruktur jalan berbasis Multimodal AI**  
*Transparan · Akuntabel · Frictionless*

[🚀 Quick Start](#-quick-start) · [📐 Arsitektur](#-arsitektur-sistem) · [✨ Fitur](#-fitur) · [🗺️ Workflow](#️-system-workflow) · [⚠️ Risiko](#️-ai-risk-assessment)

</div>

---

## 📖 Tentang JalanKita

JalanKita adalah platform inovasi AI yang mengatasi kegagalan tata kelola birokrasi tradisional dalam pemeliharaan infrastruktur publik. Dengan filosofi **Frictionless Participation**, warga hanya bertindak sebagai *sensor pasif* yang mengambil foto di lapangan, sementara seluruh beban administratif dikerjakan secara otonom oleh sistem AI di backend.

### 🎯 AI Value Moment
> *"Warga cukup ambil foto jalan rusak → AI mendeteksi kerusakan → AI menghitung RAB secara transparan → Laporan masuk ke komunitas publik"*

### 💡 Mengapa JalanKita?

| Masalah Konvensional | Solusi JalanKita |
|---|---|
| Proses pelaporan penuh hambatan birokrasi | Upload foto 1 klik, AI proses sisanya |
| Estimasi anggaran tidak transparan (rawan markup) | RAB otomatis AI, publik bisa verifikasi |
| Laporan tenggelam tanpa tindak lanjut | SLA tracker + auto-eskalasi |
| Ketimpangan infrastruktur urban vs rural | CSR Dashboard untuk pendanaan swasta |

---

## 🆕 Yang Baru di v2.0

Upgrade besar yang mempertahankan seluruh fungsi inti, ditambah kemampuan baru, **tanpa dependency tambahan** (semua memakai pustaka yang sudah dibundel Streamlit):

| Area | Peningkatan |
|---|---|
| 📊 **Dashboard Analitik** | Halaman baru: KPI (penyelesaian, kepatuhan SLA, RAB outstanding) + grafik distribusi status, keparahan, prioritas, tipe kerusakan, dan RAB per provinsi. |
| 🗺️ **Peta Sebaran** | Peta interaktif di Feed menampilkan titik laporan via koordinat GPS atau perkiraan pusat provinsi. |
| 🚦 **Skor Prioritas Otomatis** | Skor 0 sampai 100 yang memadukan keparahan + tekanan SLA + dukungan publik, dengan label Kritis/Tinggi/Sedang/Rendah dan opsi urut "Prioritas". |
| ⏱️ **SLA Dinamis** | Bug diperbaiki: hari berjalan kini dihitung otomatis dari timestamp (sebelumnya statis `0`). Target SLA mengikuti keparahan (Berat 3h · Sedang 7h · Ringan 14h). |
| 🧠 **AI Lebih Tangguh** | Parsing JSON tahan-banting, retry otomatis, dan **mode demo offline** (estimasi heuristik) sehingga app tetap jalan tanpa API key. |
| 📍 **Koordinat GPS** | Form laporan menerima koordinat dari Google Maps untuk pin peta yang presisi. |
| ⬇️ **Ekspor CSV** | Unduh laporan (terfilter atau seluruhnya) untuk dinas/mitra CSR. |
| 🗜️ **Kompresi Foto** | Foto otomatis di-resize (maks 1280px) & dikompres saat disimpan agar hemat storage. |
| 🔐 **Keamanan** | Password admin dapat di-set via env `ADMIN_PASSWORD` (tidak lagi hardcoded). |
| 🎨 **Desain Baru** | Sistem desain "asphalt + safety-amber on paper" (OKLCH, tema dipin via `.streamlit/config.toml` agar konsisten di light/dark OS), tipografi & kartu yang dikerjakan ulang. |
| 👤 **Akun & Login** | Daftar/Masuk/Keluar, password ter-hash, akun demo otomatis (`budi`/`budi123`, `admin`/`admin123`), gate autentikasi di semua halaman. |
| 🧑‍🤝‍🧑 **Mode Sosial** | Laporan kini "postingan" milik akun: avatar warna, **ikuti/unfollow**, **komentar**, dukungan, hitungan engagement, filter "yang saya ikuti". |
| 🪪 **Profil Pribadi** | Halaman profil: header + statistik (laporan, dukungan, pengikut), tab Laporan Saya, lini masa Aktivitas, dan Pengaturan (edit nama/bio/avatar/password). |
| 🔑 **Admin via Peran** | Penugasan & ubah status kini dibatasi ke akun ber-peran admin (menggantikan password admin lama). |

---

## 🌱 v3.0 · AI for Sustainable Future (BRIN AIDeaNation 2026)

Rilis ini menambahkan lapisan keberlanjutan, pengerasan keamanan, dan kesiapan
deployment tanpa menambah satu pun dependency baru (semua memakai pustaka standar
Python + Pillow).

### Lapisan Kecerdasan Keberlanjutan (`utils/sustainability.py`)

Menerjemahkan setiap kerusakan jalan yang dideteksi AI menjadi dampak iklim yang
dapat dipahami audiens non-teknis dalam hitungan detik:

| Kapabilitas | Penjelasan |
|---|---|
| 🔥 **Biaya Lingkungan** | Estimasi CO₂ dan bahan bakar yang terbuang setiap hari selama jalan dibiarkan rusak (siklus rem, perlambat, akselerasi ulang, dan pengalihan rute), lengkap dengan setara serapan pohon dan kerugian biaya BBM per tahun. |
| ♻️ **Rekomendasi Material** | Untuk tiap tipe kerusakan, sistem menyarankan metode perbaikan rendah karbon (aspal campur limbah plastik, cold in-place recycling, RAP, micro-surfacing) beserta persentase emisi yang dihindari versus aspal panas konvensional. |
| 🎯 **Pemetaan SDG** | Setiap laporan dikaitkan ke Tujuan Pembangunan Berkelanjutan yang didukung (SDG 3, 9, 11, 12, 13), lalu diagregasi di Dashboard untuk pelaporan ke pemerintah dan pendana. |

Seluruh angka adalah estimasi teknis dari faktor emisi publik dengan asumsi yang
ditampilkan transparan di UI (jumlah lalu lintas, faktor emisi CO₂/liter, serapan
pohon), bukan angka kotak hitam.

### Pengerasan Keamanan (`utils/security.py`)

| Kontrol | Implementasi |
|---|---|
| 🛡️ **Anti stored-XSS** | Seluruh teks buatan pengguna (nama, bio, lokasi, komentar, penugasan) di-escape sebelum dirender ke HTML, menutup celah injeksi skrip lewat komentar/bio. |
| 🔑 **Hashing kata sandi** | PBKDF2-HMAC-SHA256 (240k iterasi) menggantikan SHA-256 lama; hash lama tetap valid dan otomatis diupgrade saat login berikutnya. |
| ⛔ **Pembatasan login** | Maksimal 5 percobaan gagal per username sebelum penguncian sementara, ditegakkan lintas sesi di level proses server. |
| 🖼️ **Validasi unggahan** | Foto diperiksa ukuran (maks 8 MB), magic bytes, dan integritas dekode Pillow; ekstensi file tidak dipercaya begitu saja. |
| ⏲️ **Sesi kedaluwarsa** | Sesi menganggur otomatis berakhir setelah 8 jam. |
| 🔒 **Konfigurasi server** | XSRF aktif, CORS tertutup, batas unggah selaras validator, statistik penggunaan dimatikan (`.streamlit/config.toml`). |

### Responsible-AI: Privasi, Keaslian, Anti-Duplikat (`utils/privacy.py`, `utils/integrity.py`)

Mengubah dua baris "planned" pada tabel Risiko menjadi kontrol nyata:

| Kapabilitas | Penjelasan |
|---|---|
| 🔒 **Sensor privasi otomatis** | Sebelum foto tampil publik, model multimodal mendeteksi wajah dan pelat nomor, lalu Pillow memburamkannya. Aktif secara default di form laporan. |
| 🛡️ **Sinyal keaslian** | Metadata EXIF diperiksa (ada tidaknya, waktu, GPS) untuk memberi skor keaslian dan menandai foto yang berpotensi tangkapan layar atau unduhan. |
| 🧩 **Deteksi duplikat** | Perceptual hash (dHash) mengenali foto yang sama walau disimpan ulang; digabung cek kedekatan GPS untuk memperingatkan laporan ganda saat pengiriman. |
| 📍 **Klastering spasial** | Laporan dalam radius ~30 m dikelompokkan; feed menampilkan "N laporan di titik ini" sebagai sinyal prioritas yang lebih kuat. |

### Persistensi Data (`utils/db.py`)

Penyimpanan berpindah dari menulis ulang berkas JSON ke **SQLite** (pustaka standar,
tanpa dependency): tulis atomik dan transaksional yang aman saat banyak pengguna
beraksi bersamaan, dengan impor otomatis data JSON lama pada run pertama. API
penyimpanan tidak berubah sehingga seluruh logika lain tetap sama. Untuk
persistensi penuh di cloud, arahkan `JALANKITA_DB` ke volume permanen atau ganti
mesin ini dengan Postgres.

### Lokasi Presisi: GPS Otomatis + Wilayah Berjenjang (`utils/wilayah.py`)

| Kapabilitas | Penjelasan |
|---|---|
| 📍 **GPS otomatis dari foto** | Saat foto diunggah, koordinat GPS yang tertanam di metadata foto (lokasi asli pengambilan gambar) dibaca otomatis dan dipakai untuk titik peta. Bebas dependency; jika foto tanpa GPS, pengguna bisa mengisi manual. |
| 🗂️ **Kolom wilayah terstruktur** | Lokasi disimpan dalam kolom terpisah: Provinsi, Kabupaten/Kota, Kecamatan, Kelurahan/Desa, plus kode wilayah Kemendagri, sehingga pencarian dan kategori lokasi akurat. |
| ⛓️ **Dropdown berjenjang** | Memilih Provinsi memunculkan pilihan Kabupaten/Kota di dalamnya, lalu Kecamatan, lalu Kelurahan/Desa. Data lengkap 34 provinsi sampai ~80.000 kelurahan dibundel offline di `data/wilayah/`. |
| 🔎 **Filter feed berjenjang** | Feed komunitas menyaring per Provinsi lalu Kabupaten/Kota, konsisten dengan data terstruktur laporan. |

### Desain Responsif Penuh

Tipografi dan tata letak kini menyesuaikan otomatis ke semua ukuran layar memakai
`clamp()` fluida dan breakpoint mobile: kolom menumpuk, kartu dan metrik membungkus
rapi, navigasi mengalir di layar sempit. Diuji dari 375px (ponsel) hingga desktop.

### Kesiapan Deployment

- `requirements.txt` teruji pada Streamlit 1.57, tanpa dependency tambahan.
- `.env.example` dan `.streamlit/secrets.toml.example` sebagai templat rahasia (yang asli di-gitignore).
- Siap deploy ke Streamlit Community Cloud atau kontainer mana pun; mode demo membuat app tetap jalan tanpa API key.

---

## ✨ Fitur

### 📋 Halaman Laporan
- **Computer Vision Analysis**: Gemini Vision menganalisis foto dan mendeteksi tipe kerusakan, tingkat keparahan, estimasi dimensi, dan confidence level
- **RAB Generation**: LLM menghasilkan Rencana Anggaran Biaya lengkap dengan breakdown per item (material, tenaga kerja, peralatan)
- **Persistent Storage**: Laporan dan foto tersimpan sebagai file fisik lokal
- **Auto-detect Provinsi**: Sistem otomatis mendeteksi provinsi dari nama lokasi

### 🗺️ Feed Komunitas
- **Community Feed**: Semua laporan tampil publik dengan detail lengkap
- **Filter & Search**: Filter berdasarkan status, 38 provinsi, dan pencarian lokasi
- **Like/Upvote**: Warga dapat mendukung laporan untuk menaikkan prioritas
- **SLA Tracker**: Progress bar visual hari ke-N dari batas SLA
- **Status Management**: Ubah status: Menunggu → Prioritas Publik → CSR Dashboard → Selesai

### 📋 Progress & Penugasan
- **Admin Panel**: Login password-protected untuk admin Dinas PU
- **Assignment System**: Tugaskan laporan ke instansi/tim dengan catatan resmi
- **Progress Timeline**: Riwayat update kronologis dengan foto bukti pengerjaan
- **Community Updates**: Siapapun bisa menambahkan update progress + foto bukti

### 📊 Dashboard Analitik *(baru)*
- **KPI Eksekutif**: Total laporan, tingkat penyelesaian, jumlah melewati SLA, kepatuhan SLA, total & outstanding RAB
- **Visualisasi**: Grafik distribusi status, tingkat keparahan, prioritas, tipe kerusakan, dan estimasi RAB per provinsi
- **Tabel Detail + Skor Prioritas**: Tabel interaktif dengan progress bar skor prioritas
- **Ekspor CSV**: Unduh seluruh data laporan untuk pelaporan resmi

---

## 🗺️ System Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         JALANKITA SYSTEM                            │
│                                                                     │
│  FASE 1: INPUT                                                      │
│  ┌──────────────┐    ┌─────────────────────────────────────────┐   │
│  │   WARGA      │───▶│  Form Laporan                           │   │
│  │ (Pelapor)    │    │  • Nama pelapor                         │   │
│  └──────────────┘    │  • Lokasi jalan (auto-detect provinsi)  │   │
│                      │  • Upload foto kerusakan                │   │
│                      └──────────────┬──────────────────────────┘   │
│                                     │                               │
│  FASE 2: AI PROCESSING              ▼                               │
│                      ┌──────────────────────────────────────────┐  │
│                      │         GEMINI 2.5 FLASH                 │  │
│                      │                                          │  │
│                      │  Step 1: Computer Vision Analysis        │  │
│                      │  ┌────────────────────────────────────┐  │  │
│                      │  │ Input: Foto JPEG                   │  │  │
│                      │  │ Output: {                          │  │  │
│                      │  │   tipe_kerusakan,                  │  │  │
│                      │  │   tingkat_keparahan,               │  │  │
│                      │  │   estimasi_dimensi,                │  │  │
│                      │  │   confidence,                      │  │  │
│                      │  │   catatan                          │  │  │
│                      │  │ }                                  │  │  │
│                      │  └────────────────────────────────────┘  │  │
│                      │                  │                        │  │
│                      │  Step 2: RAB Generation                  │  │
│                      │  ┌────────────────────────────────────┐  │  │
│                      │  │ Input: hasil CV + lokasi           │  │  │
│                      │  │ Output: {                          │  │  │
│                      │  │   material (Rp),                   │  │  │
│                      │  │   tenaga_kerja (Rp),               │  │  │
│                      │  │   peralatan (Rp),                  │  │  │
│                      │  │   total (Rp),                      │  │  │
│                      │  │   breakdown[]                      │  │  │
│                      │  │ }                                  │  │  │
│                      │  └────────────────────────────────────┘  │  │
│                      └──────────────────┬───────────────────────┘  │
│                                         │                           │
│  FASE 3: STORAGE                        ▼                           │
│                      ┌──────────────────────────────────────────┐  │
│                      │         PERSISTENT STORAGE               │  │
│                      │                                          │  │
│                      │  uploads/report_RPT-XXX.jpg  ← foto      │  │
│                      │  data/reports.json           ← semua     │  │
│                      │                                data       │  │
│                      └──────────────────┬───────────────────────┘  │
│                                         │                           │
│  FASE 4: COMMUNITY                      ▼                           │
│                      ┌──────────────────────────────────────────┐  │
│                      │         FEED KOMUNITAS                   │  │
│                      │                                          │  │
│                      │  [Publik]          [Admin]               │  │
│                      │  • Lihat laporan   • Login panel         │  │
│                      │  • Like/upvote     • Assign ke instansi  │  │
│                      │  • Filter wilayah  • Tambah catatan      │  │
│                      │  • Update progress • Kelola status       │  │
│                      └──────────────────┬───────────────────────┘  │
│                                         │                           │
│  FASE 5: RESOLUSI                       ▼                           │
│                      ┌──────────────────────────────────────────┐  │
│                      │  STATUS LIFECYCLE                        │  │
│                      │                                          │  │
│                      │  Menunggu ──(7 hari)──▶ Prioritas Publik │  │
│                      │      │                        │          │  │
│                      │      │              [>100 likes / viral] │  │
│                      │      │                        │          │  │
│                      │  (30 hari)              Dinas PU         │  │
│                      │      │               menindaklanjuti     │  │
│                      │      ▼                        │          │  │
│                      │  CSR Dashboard                ▼          │  │
│                      │  (Pendanaan          ┌──────────────┐    │  │
│                      │   Swasta)            │   SELESAI ✅  │    │  │
│                      │                      └──────────────┘    │  │
│                      └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 🔄 Data Flow Diagram

```
Warga
  │
  │ upload foto + isi form
  ▼
app.py (Streamlit)
  │
  ├──[foto bytes]──▶ utils/gemini.py
  │                       │
  │              ┌────────┴─────────┐
  │              │  Gemini Vision   │
  │              │  analyze_image() │
  │              └────────┬─────────┘
  │                       │ JSON: deteksi
  │              ┌────────▼─────────┐
  │              │  Gemini Text     │
  │              │  generate_rab()  │
  │              └────────┬─────────┘
  │                       │ JSON: rab
  │              ◀────────┘
  │
  ├──[foto bytes]──▶ utils/storage.py
  │                  save_report_foto()
  │                  → uploads/report_RPT-XXX.jpg
  │
  └──[report dict]──▶ utils/storage.py
                      add_report()
                      → data/reports.json

pages/feed.py (Streamlit)
  │
  ├──▶ load_reports() ──▶ data/reports.json
  ├──▶ toggle_like()
  ├──▶ update_status()
  ├──▶ update_assignment()  [Admin only]
  └──▶ add_progress_update() → uploads/progress_RPT-XXX_*.jpg
```

---

## 📐 Arsitektur Sistem

### Stack Teknologi

| Layer | Teknologi | Fungsi |
|---|---|---|
| **UI Layer** | Streamlit 1.35+ | Antarmuka web interaktif |
| **App Logic** | Python 3.11+ | Orkestrasi alur kerja |
| **AI Layer** | Google Gemini 2.5 Flash | CV Analysis + RAB Generation |
| **Data Layer** | JSON + File System | Persistent storage lokal |

### Struktur File

```
Jalan Kita/
│
├── app.py                  # Halaman utama: form laporan + GPS + skor prioritas
│
├── pages/
│   ├── feed.py             # Feed komunitas + peta + ekspor CSV
│   └── dashboard.py        # Dashboard analitik (KPI + grafik) [baru]
│
├── utils/
│   ├── gemini.py           # AI client (CV + RAB): retry + mode demo offline
│   ├── storage.py          # JSON storage, SLA dinamis, skor prioritas, CSV
│   ├── analytics.py        # Agregasi data untuk dashboard
│   ├── geo.py              # Koordinat provinsi untuk peta
│   ├── ui.py               # CSS responsif, header, navigasi, komponen keberlanjutan
│   ├── auth.py             # Akun, PBKDF2, rate-limit login, sesi
│   ├── security.py         # Escape XSS, hashing, validasi unggahan [v3.0]
│   ├── sustainability.py   # CO₂/BBM terbuang, material hijau, SDG [v3.0]
│   ├── privacy.py          # Auto-blur wajah & pelat nomor [v3.0]
│   ├── integrity.py        # Keaslian EXIF, GPS foto, dedup, klastering [v3.0]
│   ├── db.py               # Mesin penyimpanan SQLite [v3.0]
│   └── wilayah.py          # Wilayah berjenjang provinsi→kelurahan [v3.0]
│
├── data/wilayah/           # Dataset administratif Indonesia (CSV, ~2.5 MB)
│   ├── provinces.csv · regencies.csv · districts.csv · villages.csv
│
├── data/
│   ├── seed_data.json      # 5 laporan dummy untuk demo
│   └── reports.json        # Database laporan (auto-generated)
│
├── uploads/                # Foto laporan & progress (auto-generated)
│   ├── report_RPT-XXX.jpg
│   └── progress_RPT-XXX_*.jpg
│
├── requirements.txt
└── .env                    # API key (jangan di-commit!)
```

### BEAM System Perspective

```
[Masyarakat (Pelapor)] ──▶ [Foto Kerusakan : Data]
                                    │
                                    ▼
                    [Image Preprocessing : Transformation]
                                    │
                                    ▼
                    [Deteksi Tingkat Kerusakan : Inference]
                            ▲
                            │ model connector
                    [CV Model YOLO/CNN : Statistical Model]

                    [Deteksi → Hasil Deteksi : Symbol]
                                    │
                                    ▼
                    [Generasi RAB & Narasi : Inference]
                            ▲
                            │ model connector
                    [LLM Gemini/OpenAI : Statistical Model]

                    [Generasi → Estimasi RAB : Symbol]
                                    │
                                    ▼
                    [Petugas Dinas PU : Actor]

Context: [Manajemen Infrastruktur Publik]
```

---

## ⚠️ AI Risk Assessment

| # | Risiko | Sumber | Konsekuensi | Kontrol |
|---|---|---|---|---|
| 1 | **Injeksi Laporan Palsu** | Foto Kerusakan (Input) | Sistem memproses foto editan/usang | ✅ Sinyal keaslian EXIF + perceptual-hash anti-duplikat + klastering spasial (`utils/integrity.py`) |
| 2 | **Kebocoran Data Sensitif** | Foto Kerusakan (Storage) | Wajah/plat nomor tersimpan tanpa samaran | ✅ Auto-blur wajah & pelat sebelum simpan (`utils/privacy.py`) |
| 3 | **Bias Representasi Geografis** | CV Model (Training Data) | Gagal deteksi kerusakan di pelosok | Dataset seimbang urban+rural; evaluasi kuartalan |
| 4 | **Service Dependency** *(baru ditemukan saat build)* | Gemini API | Seluruh fitur AI tidak bisa digunakan saat API down | Fallback message; model lokal *(planned)* |

---

## 🚀 Quick Start

### Prasyarat
- Python 3.11+
- Gemini API Key (gratis di [Google AI Studio](https://aistudio.google.com))

### Instalasi

```bash
# 1. Clone atau download project
cd "Jalan Kita"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Konfigurasi API key (opsional; tanpa ini app jalan di MODE DEMO)
# Edit file .env:
GEMINI_API_KEY=your_api_key_here
ADMIN_PASSWORD=password_admin_anda   # opsional

# 4. Jalankan aplikasi
streamlit run app.py
```

> 💡 **Mode Demo:** tanpa `GEMINI_API_KEY`, aplikasi tetap berfungsi penuh menggunakan estimasi heuristik (ditandai label "Mode Demo"). Ideal untuk mencoba alur tanpa biaya API.

### Buka di Browser

```
Halaman Laporan  →  http://localhost:8501
Feed Komunitas   →  http://localhost:8501/feed
Dashboard        →  http://localhost:8501/dashboard
```

### Admin Access

Peran admin menggunakan akun ber-role admin (demo: `admin` / `admin123`). Untuk
deployment, ubah kata sandi akun admin lewat halaman Pengaturan setelah login.

### Deploy ke Streamlit Community Cloud

1. Push repo ke GitHub (rahasia tidak ikut: `.env` dan `.streamlit/secrets.toml` sudah di-gitignore).
2. Buat app baru di [share.streamlit.io](https://share.streamlit.io), arahkan ke `app.py`.
3. Di menu **Secrets**, tempel isi mengikuti `.streamlit/secrets.toml.example`:
   ```toml
   GEMINI_API_KEY = "kunci_anda"
   ADMIN_PASSWORD = "kata_sandi_admin"
   ```
4. Deploy. Tanpa `GEMINI_API_KEY`, app tetap jalan dalam mode demo.

> Catatan: penyimpanan berbasis file (`data/`, `uploads/`) bersifat sementara di
> Streamlit Cloud. Untuk data yang persisten di produksi, hubungkan basis data
> eksternal (mis. Postgres/Supabase) sebagai langkah lanjutan.

---

## 📦 Dependencies

```txt
streamlit>=1.35.0
google-genai
Pillow>=10.0.0
python-dotenv>=1.0.0
```

---

## 🔮 Roadmap

### v1.0 (Prototipe, sekarang)
- [x] CV Detection dengan Gemini Vision
- [x] RAB Generation dengan LLM
- [x] Feed komunitas dengan persistent storage
- [x] Filter 38 provinsi + auto-detect
- [x] Admin panel + assignment system
- [x] Progress timeline + foto bukti

### v2.0 (MVP, planned)
- [ ] Live Photo Capturing (tolak galeri)
- [ ] Auto-blur wajah & plat nomor
- [ ] GPS + Reverse Geocoding otomatis
- [ ] SLA Auto-escalation ke Twitter/X
- [ ] CSR Dashboard untuk pendanaan swasta
- [ ] Spatial clustering (cek duplikasi dalam radius 10m)

### v3.0 (Production, planned)
- [ ] Autentikasi pengguna (NIK-based)
- [ ] Predictive maintenance (ML regresi)
- [ ] Mobile app (Flutter)
- [ ] Multi-tenant (multi-kota/provinsi)
- [ ] API publik untuk integrasi pemerintah

---

## 👤 Author

**Aditya Wahyu Wijanarko**  
25/574566/PPA/07251  
Master of Computer Science in Artificial Intelligence  
Universitas Gadjah Mada

---

## 📄 Lisensi

MIT License. Bebas digunakan untuk keperluan pendidikan dan penelitian.

---

<div align="center">
<sub>Built with ❤️ for better public infrastructure in Indonesia</sub>
</div>
# Jalan-Kita
