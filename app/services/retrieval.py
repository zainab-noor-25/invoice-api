import numpy as np
from app.db.mongo import chunks_col

# ----------------------------------------

def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_chunks_local(invoice_id: str, query_embedding: list[float], k: int = 4):
    docs = list(chunks_col.find({"invoice_id": invoice_id}))
    scored = []

    for d in docs:
        score = cosine_similarity(query_embedding, d["embedding"])
        scored.append({
            "chunk_id": d["chunk_id"],
            "text": d["text"],
            "score": float(score)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]
