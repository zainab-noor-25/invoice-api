import json
import httpx

from app.config.config import settings
from app.prompts.llm_prompts import llm_prompt

from app.fallback.missing import guess_customer_from_ocr
from app.fallback.pruner import prune_ocr_text
from app.fallback.dates import guess_dates_from_ocr

# --------------------------------------------

# ----------- Text Extraction -----------

def extract_invoice_fields(ocr_text: str) -> dict:
    
    prompt = f""" 
        {llm_prompt}

    OCR TEXT:
        {prune_ocr_text(ocr_text)}

    """.strip()

    payload = {
        "model": settings.CHAT_MODEL,  # e.g. qwen3:4b or qwen2.5:7b-instruct
        "messages": [
            {"role": "system", "content": "You output only valid JSON. No extra text."},
            {"role": "user", "content": prompt[:1200]},
        ],
        "stream": False,
        "options": {"temperature": 0, 
                    "num_predict": 80,
                    "num_ctx": 1024},
    }

    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"

    r = httpx.post(url, json=payload, timeout=600)
    r.raise_for_status()

    raw = r.json()["message"]["content"].strip()

    try:
        data = json.loads(raw)

        # -------- Date Fallbacks --------
        issued, due = guess_dates_from_ocr(ocr_text)

        if not data.get("date_issued") and issued:
            data["date_issued"] = issued

        if not data.get("due_date") and due:
            data["due_date"] = due


        # -------- Fallback for customer_name --------
        if not data.get("customer_name"):
            guess = guess_customer_from_ocr(ocr_text)
            if guess:
                data["customer_name"] = guess

        return data

    except json.JSONDecodeError:
        return {"error": "Model did not return valid JSON", "raw": raw[:800]}


# ----------- Context Q/A --> Chat Bot -----------

def answer_from_context(prompt: str) -> str:
    payload = {
        "model": settings.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Answer using only the given context."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 200},
    }

    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"
    r = httpx.post(url, json=payload, timeout=300)
    r.raise_for_status()

    return r.json()["message"]["content"].strip()


