import numpy as np
from app.db.vectordb import get_index
from app.services.embeddings import embed_text
from app.config.config import settings

# ----------------------------------------

def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_chunks(invoice_id: str, question: str, top_k: int = None):
    top_k = top_k or settings.TOP_K

    q_emb = embed_text(question)
    index = get_index()

    res = index.query(
        vector=q_emb,
        top_k=top_k,
        include_metadata=True,
        filter={"invoice_id": {"$eq": invoice_id}}
    )

    chunks = []
    matches = res.get("matches", []) or []

    for m in matches:
        md = m.get("metadata") or {}
        chunks.append({
            "chunk_id": md.get("chunk_id"),
            "text": md.get("text", ""),
            "score": m.get("score", 0),
        })

    return chunks
