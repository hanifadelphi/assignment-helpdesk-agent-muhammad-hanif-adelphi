import logging
from dotenv import load_dotenv

# Panggil load_dotenv paling awal[span_6](start_span)[span_6](end_span)
load_dotenv()

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.router import handle_query

# Konfigurasi logging untuk memantau error internal API
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("helpdesk_api")

app = FastAPI(
    title="IT Helpdesk Assistant API",
    description="Backend API End-to-End RAG & Mini-Agent",
    version="1.0.0"
)


class AskRequest(BaseModel):
    query: str = Field(..., description="Pertanyaan atau permintaan dari pengguna")


class AskResponse(BaseModel):
    status: str
    intent: str
    data: str


@app.get("/health")
async def health():
    """Endpoint sederhana untuk memastikan service berjalan."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Endpoint utama yang menerima query pengguna, meneruskannya ke router,
    serta menangani kegagalan LLM dan error tak terduga secara terstruktur.
    """
    # 1. Validasi input: memastikan query tidak kosong atau hanya berisi spasi
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query tidak boleh kosong atau hanya berisi karakter spasi."
        )

    try:
        # 2. Panggil alur utama router
        result = await handle_query(clean_query)

        # 3. Penanganan kondisi intent tidak dikenali / router mengembalikan status error
        if result.get("status") == "error":
            logger.warning(f"Unrecognized intent or process issue for query: '{clean_query}'")
            return AskResponse(
                status="error",
                intent=result.get("intent", "unknown"),
                data=result.get("data", "Maaf, sistem tidak dapat mengenali maksud permintaan Anda.")
            )

        return AskResponse(**result)

    except Exception as e:
        # 4. Penanganan kondisi ekstrim ketika LLM / API Gemini gagal merespons atau timeout
        logger.error(f"Internal system error during LLM processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada layanan AI Helpdesk: {str(e)}"
        )
