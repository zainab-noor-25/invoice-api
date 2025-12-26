def chunk_text(text: str, size: int = 800, overlap: int = 100):
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    chunks = []
    start = 0
    idx = 0
    n = len(text)

    while start < n:
        end = min(n, start + size)

        chunks.append({
            "chunk_id": idx,
            "text": text[start:end],
            "meta": {
                "char_start": start,
                "char_end": end,
                "source": "ocr"
            }
        })

        idx += 1

        # Sstop when hit the end
        if end >= n:
            break

        start = end - overlap

    return chunks
