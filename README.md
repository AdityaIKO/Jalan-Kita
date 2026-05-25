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
├── app.py                  # Halaman utama: form laporan
│
├── pages/
│   └── feed.py             # Feed komunitas
│
├── utils/
│   ├── gemini.py           # Gemini API client (CV + RAB)
│   └── storage.py          # JSON storage + file management
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
| 1 | **Injeksi Laporan Palsu** | Foto Kerusakan (Input) | Sistem memproses foto editan/usang | Live Photo Capturing; validasi output AI |
| 2 | **Kebocoran Data Sensitif** | Foto Kerusakan (Storage) | Wajah/plat nomor tersimpan tanpa samaran | Auto-blur preprocessing *(planned)* |
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

# 3. Konfigurasi API key
# Edit file .env:
GEMINI_API_KEY=your_api_key_here

# 4. Jalankan aplikasi
streamlit run app.py
```

### Buka di Browser

```
Halaman Laporan  →  http://localhost:8501
Feed Komunitas   →  http://localhost:8501/feed
```

### Admin Access

Password default admin: `admin123`

> ⚠️ Ganti password di `utils/storage.py` baris `ADMIN_PASSWORD` sebelum deployment

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

### v1.0 (Prototipe — sekarang)
- [x] CV Detection dengan Gemini Vision
- [x] RAB Generation dengan LLM
- [x] Feed komunitas dengan persistent storage
- [x] Filter 38 provinsi + auto-detect
- [x] Admin panel + assignment system
- [x] Progress timeline + foto bukti

### v2.0 (MVP — planned)
- [ ] Live Photo Capturing (tolak galeri)
- [ ] Auto-blur wajah & plat nomor
- [ ] GPS + Reverse Geocoding otomatis
- [ ] SLA Auto-escalation ke Twitter/X
- [ ] CSR Dashboard untuk pendanaan swasta
- [ ] Spatial clustering (cek duplikasi dalam radius 10m)

### v3.0 (Production — planned)
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

MIT License — bebas digunakan untuk keperluan pendidikan dan penelitian.

---

<div align="center">
<sub>Built with ❤️ for better public infrastructure in Indonesia</sub>
</div>
# Jalan-Kita
