import httpx
from app.config.config import settings

def embed_text(text: str) -> list[float]:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    
    payload = {"model": settings.EMBEDDING_MODEL, "prompt": text}

    # 1) Try older endpoint: /api/embeddings
    try:
        r = httpx.post(f"{base}/api/embeddings", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return data["embedding"]
    except httpx.HTTPStatusError as e:
        # If it's NOT a 404, raise it (real error)
        if e.response.status_code != 404:
            raise

    # 2) Try newer endpoint: /api/embed
    payload2 = {"model": settings.EMBEDDING_MODEL, "input": text}
    
    r2 = httpx.post(f"{base}/api/embed", json=payload2, timeout=120)
    r2.raise_for_status()
    data2 = r2.json()
    
    if "embeddings" in data2:
        return data2["embeddings"][0]
    
    return data2["embedding"]
