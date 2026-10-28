import os
import pandas as pd
import numpy as np
import faiss
from google import genai
from dotenv import load_dotenv

# Wajib dipanggil sebelum inisialisasi genai.Client[span_3](start_span)[span_3](end_span)
load_dotenv()

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Menggunakan absolute path agar aman dipanggil dari mana saja
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "data", "it_helpdesk_knowledge_base.csv")

_index = None
_documents = None
_df = None


def _get_embedding(text: str):
    """Mengubah teks menjadi vektor embedding menggunakan model text-embedding-004."""
    result = _client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return result.embeddings[0].values


def build_index():
    """
    Memuat knowledge base CSV, menggabungkan question & answer menjadi unit retrievable,
    serta membangun FAISS index yang disimpan ke variabel global.
    """
    global _index, _documents, _df

    if _index is not None and _documents is not None:
        return _index, _documents

    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        raise FileNotFoundError(f"File knowledge base tidak ditemukan di: {KNOWLEDGE_BASE_PATH}")

    _df = pd.read_csv(KNOWLEDGE_BASE_PATH, encoding='utf-8')

    # Menggabungkan kolom question dan answer menjadi satu unit retrievable
    _documents = _df.apply(
        lambda row: f"Pertanyaan: {row.get('question', '')} | Jawaban: {row.get('answer', '')}",
        axis=1
    ).tolist()

    # Generate embedding untuk seluruh dokumen
    embeddings = [_get_embedding(doc) for doc in _documents]
    emb_matrix = np.array(embeddings).astype('float32')

    # Inisialisasi FAISS Index FlatL2
    dimension = emb_matrix.shape[1]
    _index = faiss.IndexFlatL2(dimension)
    _index.add(emb_matrix)

    return _index, _documents


def semantic_search(query: str, top_k: int = 2):
    """
    Mencari dokumen FAQ paling relevan dari FAISS index berdasarkan kedekatan vektor.
    """
    global _index, _documents

    if _index is None or _documents is None:
        build_index()

    query_vector = np.array([_get_embedding(query)]).astype('float32')
    distances, indices = _index.search(query_vector, top_k)

    retrieved_docs = []
    for idx in indices[0]:
        if idx < len(_documents):
            retrieved_docs.append(_documents[idx])

    return retrieved_docs


async def answer_from_knowledge_base(query: str) -> str:
    """
    Menerima query intent 'faq', melakukan retrieval dari FAISS,
    dan menghasilkan jawaban terstruktur via Gemini LLM.
    """
    retrieved_docs = semantic_search(query, top_k=2)
    context_text = "\n".join(retrieved_docs)

    prompt = f"""Anda adalah IT & People Helpdesk AI Assistant internal perusahaan.
Jawab pertanyaan pengguna HANYA berdasarkan konteks pengetahuan yang disediakan di bawah ini.
Jika informasi tidak ada dalam konteks, katakan dengan sopan bahwa Anda tidak memiliki informasi tersebut dan sarankan pengguna untuk menghubungi tim IT/People Ops secara langsung. Jangan menebak jawaban.

=== KONTEKS KNOWLEDGE BASE ===
{context_text}

=== PERTANYAAN PENGGUNA ===
{query}

Jawaban:"""

    response = _client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text
