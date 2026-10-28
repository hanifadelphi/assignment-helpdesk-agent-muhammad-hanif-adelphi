# IT Helpdesk AI Assistant — End-to-End RAG & AI Agent

Aplikasi **IT Helpdesk AI Assistant** berbasis **FastAPI** yang mengintegrasikan alur **RAG (Retrieval-Augmented Generation)** untuk menjawab pertanyaan kebijakan internal/FAQ dan **Mini-Agent Tool Calling** untuk mengecek status tiket secara otomatis dalam satu backend API terpadu.

---

## 1. Problem Statement & Objective Use Case

- **Objective**: Membangun prototype backend API AI Helpdesk internal untuk tim People & IT Operations yang dapat secara otomatis membedakan dan menangani dua jenis permintaan pengguna (informasi kebijakan vs aksi pengecekan data spesifik) dalam satu sistem terpadu.
- **Dua Jenis Permintaan User**:
  1. **Pertanyaan Informasi / Kebijakan Umum (`faq`)**:
     - *Deskripsi*: Pertanyaan umum seputar kebijakan HR, People Ops, dan IT Support.
     - *Contoh*: `"Berapa jatah cuti tahunan saya?"` atau `"Bagaimana cara reset password VPN?"`
     - *Penanganan*: Ditangani oleh **RAG System** (Semantic Search berbasis FAISS Vector Indexing + Gemini AI Embeddings & LLM).
  2. **Pengecekan Data Spesifik (`ticket_status`)**:
     - *Deskripsi*: Permintaan aksi langsung untuk memeriksa status tiket dukungan teknis berdasarkan ID tiket.
     - *Contoh*: `"Tolong cek status tiket TICKET-0042 milik saya"`
     - *Penanganan*: Ditangani oleh **Tool Calling** (membaca data `data/mock_tickets.csv` secara presisi).
- **Batasan & Asumsi**:
  - Penanganan status tiket terbatas pada pencarian data mock dalam file `data/mock_tickets.csv`.
  - Penanganan FAQ mengandalkan dokumen `data/it_helpdesk_knowledge_base.csv`.
  - Indeks FAISS dibangun saat *startup* aplikasi dan tersimpan secara *in-memory*.

---

## 2. Desain Workflow Aplikasi

### Alur Sistem
```text
User Request (POST /ask)
       │
       ▼
   [Router Module (app/router.py)]
   ├── Extracted ticket_id / Intent == 'ticket_status'
   │       └──► [Tool Call Path (app/tools.py)] ──► Query mock_tickets.csv ──► Return JSON Detail Tiket
   │
   └── Intent == 'faq'
           └──► [RAG System Path (app/rag.py)] ──► FAISS Semantic Search ──► Prompt Engineering ──► Gemini LLM ──► Return Answer Text
```

### Kriteria Pembeda Intent
- **Intent `ticket_status`**: Terdeteksi jika query mengandung pola unik ID tiket `TICKET-XXXX` berbasis Regular Expression (`r'TICKET-\d+'`) atau kata kunci eksplisit seperti `"cek tiket"` / `"status tiket"`.
- **Intent `faq`**: Terdeteksi untuk seluruh pertanyaan informasi umum, kebijakan HR/IT, panduan operasional, maupun pertanyaan di luar cakupan (*out-of-scope*).

---

## 3. Struktur Project

```text
it-helpdesk-assignment/
├── app/
│   ├── __init__.py       # Marker Python package
│   ├── main.py           # Entry point FastAPI, berisi endpoint /ask & /health
│   ├── router.py         # Intent detection + routing ke RAG atau tool call
│   ├── rag.py            # Modul RAG: embedding, FAISS, semantic search, LLM answer
│   └── tools.py          # Modul tool call: pengecekan status tiket
├── data/
│   ├── it_helpdesk_knowledge_base.csv   # Knowledge base FAQ untuk RAG
│   └── mock_tickets.csv                 # Data mock status tiket
├── Dockerfile            # Konfigurasi containerization Docker
├── .env.example          # Template environment variable (tanpa API Key asli)
├── requirements.txt      # Daftar dependensi Python
└── README.md             # Dokumentasi proyek
```

---

## 4. Cara Menjalankan Aplikasi

### A. Secara Lokal (Tanpa Docker)
1. **Aktifkan Virtual Environment & Install Dependensi**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Mac / Linux
   # .\.venv\Scripts\Activate.ps1  # Windows
   pip install -r requirements.txt
   ```
2. **Konfigurasi Environment Variable**:
   Salin `.env.example` menjadi `.env` dan masukkan API Key Gemini Anda:
   ```bash
   cp .env.example .env
   ```
   Isi file `.env`:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualApiKeyHere
   ```
3. **Jalankan Server Uvicorn**:
   ```bash
   uvicorn app.main:app --reload
   ```
4. **Akses API Documentation**:
   Buka browser dan akses Swagger UI di `http://localhost:8000/docs`.

### B. Menggunakan Docker Container
1. **Build Docker Image**:
   ```bash
   docker build -t helpdesk-agent .
   ```
2. **Jalankan Docker Container**:
   ```bash
   docker run -p 8000:8000 --env-file .env helpdesk-agent
   ```
3. **Uji Endpoint**:
   Akses Swagger UI di `http://localhost:8000/docs` atau kirim request via cURL.

---

## 5. Hasil Pengujian (5 Skenario Uji Wajib)

| No | Skenario Uji | Input Query | Target Intent | Result Response Data | Observasi & Analisis |
|---|---|---|---|---|---|
| 1 | **RAG FAQ (Cuti)** | `"Berapa jatah cuti tahunan saya?"` | `faq` | `"Karyawan tetap mendapat jatah 12 hari cuti tahunan yang dapat diambil setelah masa kerja minimal 3 bulan."` | Router mengarahkan ke RAG path. FAISS menemukan chunk kebijakan cuti dan Gemini menyusun jawaban akurat. |
| 2 | **RAG FAQ (VPN)** | `"Bagaimana cara reset password VPN?"` | `faq` | `"Reset password VPN dapat dilakukan mandiri melalui portal self-service IT, atau menghubungi tim IT Support jika akun terkunci."` | Router mengarahkan ke RAG path. Informasi berhasil ditarik dari knowledge base. |
| 3 | **Tool Call (Valid ID)** | `"Status tiket TICKET-0042"` | `ticket_status` | `"Status Tiket [TICKET-0042]: Subjek: Akses VPN Terkunci \| Status Saat Ini: In Progress \| Pembaruan Terakhir: 2025-02-20"` | Regex berhasil mengekstrak `TICKET-0042` dan Tool Call membaca data `mock_tickets.csv`. |
| 4 | **Tool Call (Invalid ID)** | `"Cek status tiket TICKET-9999"` | `ticket_status` | `"Tiket dengan ID 'TICKET-9999' tidak ditemukan dalam sistem. Mohon pastikan nomor tiket sudah benar (contoh: TICKET-0042)."` | Sistem mengembalikan pesan informatif tanpa mengalami *crash* / 500 Error. |
| 5 | **Out of Domain / Ambigu** | `"Siapa presiden pertama Indonesia?"` | `faq` | `"Mohon maaf, saya tidak memiliki informasi tersebut dalam database saya. Silakan hubungi tim IT atau People Ops secara langsung..."` | Strict grounding prompt bekerja secara efektif mencegah LLM berhalusinasi pada pertanyaan di luar KB. |

---

## 6. Keterbatasan Sistem (Limitations)

1. **Deteksi Intent Berbasis Hybrid/Rule**: Router memprioritaskan pola `TICKET-XXXX` melalui regex. Pertanyaan yang sangat ambigu tanpa format ID tiket tertentu akan diproses oleh LLM fallback.
2. **FAISS In-Memory Indexing**: Indeks FAISS dibangun saat aplikasi *startup* dan disimpan di memori lokal. Untuk skala produksi besar, direkomendasikan memakai Vector DB eksternal (seperti Qdrant / Pinecone).
3. **Dataset Statis**: Data tiket dan knowledge base masih dibaca dari file CSV lokal.
