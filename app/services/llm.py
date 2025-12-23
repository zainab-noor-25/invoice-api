import json
import httpx
from app.config.config import settings

# --------------------------------------------

# ----------- Text Extraction -----------

def extract_invoice_fields(ocr_text: str) -> dict:
    prompt = f"""
Extract invoice fields from OCR text.
Return ONLY valid JSON. No explanations.

Fields:
- supplier_name
- customer_name
- invoice_date (YYYY-MM-DD)
- total_amount (number only)

Use null if missing.

OCR TEXT:
{ocr_text[:1500]}
""".strip()

    payload = {
        "model": settings.CHAT_MODEL,  # e.g. qwen3:4b or qwen2.5:7b-instruct
        "messages": [
            {"role": "system", "content": "You output only valid JSON. No extra text."},
            {"role": "user", "content": prompt[:1200]},
        ],
        "stream": False,
        "options": {"temperature": 0, 
                    "num_predict": 120,
                    "num_ctx": 2048},
    }

    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"

    r = httpx.post(url, json=payload, timeout=600)
    r.raise_for_status()

    raw = r.json()["message"]["content"].strip()

    import time
    t0 = time.time()
    print(">> POST", url)
    r = httpx.post(url, json=payload, timeout=600)
    print(">> DONE in", round(time.time() - t0, 2), "sec")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Model did not return valid JSON", "raw": raw[:800]}

