import os
import pandas as pd

# Menentukan path absolut ke data/mock_tickets.csv agar aman dipanggil dari mana saja
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_TICKETS_PATH = os.path.join(BASE_DIR, "data", "mock_tickets.csv")


def get_ticket_status(ticket_id: str) -> str:
    """
    Mencari status tiket berdasarkan ticket_id pada data mock_tickets.csv.
    Jika ticket_id tidak ditemukan, mengembalikan pesan informatif tanpa crash.
    """
    if not ticket_id or not ticket_id.strip():
        return "ID tiket tidak boleh kosong."

    clean_ticket_id = ticket_id.strip().upper()

    try:
        if not os.path.exists(MOCK_TICKETS_PATH):
            return f"Error: File database tiket tidak ditemukan di {MOCK_TICKETS_PATH}."

        df = pd.read_csv(MOCK_TICKETS_PATH)

        if 'ticket_id' not in df.columns:
            return "Error: Kolom 'ticket_id' tidak ditemukan dalam dataset."

        # Samakan format menjadi uppercase string agar pencarian tidak sensitif huruf besar/kecil
        df['ticket_id'] = df['ticket_id'].astype(str).str.strip().str.upper()

        # Filter baris yang cocok
        matched_row = df[df['ticket_id'] == clean_ticket_id]

        if not matched_row.empty:
            row = matched_row.iloc[0]

            # Mengambil nilai kolom dengan aman
            subject = row.get('subject', 'N/A')
            status = row.get('status', 'N/A')
            last_update = row.get('last_update', 'N/A')

            return (
                f"Status Tiket [{clean_ticket_id}]:\n"
                f"- Subjek: {subject}\n"
                f"- Status Saat Ini: {status}\n"
                f"- Pembaruan Terakhir: {last_update}"
            )
        else:
            return f"Tiket dengan ID '{clean_ticket_id}' tidak ditemukan dalam sistem. Mohon pastikan nomor tiket sudah benar (contoh: TICKET-0042)."

    except Exception as e:
        return f"Terjadi kesalahan saat mengecek status tiket: {str(e)}"
