import os
import re
from google import genai
from app.rag import answer_from_knowledge_base
from app.tools import get_ticket_status
from dotenv import load_dotenv

# Wajib dipanggil sebelum inisialisasi genai.Client[span_3](start_span)[span_3](end_span)
load_dotenv()

# Inisialisasi client Gemini AI API
_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def extract_ticket_id(query: str) -> str:
    """
    Mengekstrak ticket_id dengan format 'TICKET-XXXX' dari teks query.
    """
    match = re.search(r'TICKET-\d+', query, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return ""


async def detect_intent(query: str) -> str:
    """
    Menentukan intent dari query user ('faq' atau 'ticket_status') menggunakan Gemini LLM.
    """
    # Deteksi cepat: jika mengandung kode ID tiket, langsung arahkan ke ticket_status
    if extract_ticket_id(query):
        return "ticket_status"

    prompt = f"""Klasifikasikan pertanyaan berikut ke dalam salah satu kategori intent:
- 'ticket_status': Permintaan mengecek status tiket, menanyakan tiket masalah/dukungan.
- 'faq': Pertanyaan kebijakan internal, informasi umum, instruksi/panduan, atau hal lainnya.

Jawab HANYA dengan satu kata persis: 'faq' atau 'ticket_status'.

Pertanyaan: {query}
Intent:"""

    try:
        response = _client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        result = response.text.strip().lower()
        
        if "ticket_status" in result or "ticket" in result:
            return "ticket_status"
        return "faq"
    except Exception:
        # Fallback sederhana berbasis keyword jika panggilan API ke LLM bermasalah
        query_lower = query.lower()
        if "tiket" in query_lower or "status" in query_lower:
            return "ticket_status"
        return "faq"


async def handle_query(query: str) -> dict:
    """
    Fungsi utama yang dipanggil oleh endpoint /ask.
    Menjalankan intent detection, lalu merutekan ke RAG atau tool call yang sesuai.
    """
    intent = await detect_intent(query)

    if intent == "ticket_status":
        ticket_id = extract_ticket_id(query)
        data = get_ticket_status(ticket_id)
        return {"status": "success", "intent": "ticket_status", "data": data}

    elif intent == "faq":
        data = await answer_from_knowledge_base(query)
        return {"status": "success", "intent": "faq", "data": data}

    else:
        return {"status": "error", "intent": "unknown", "data": "Maaf, saya tidak memahami permintaan Anda."}
