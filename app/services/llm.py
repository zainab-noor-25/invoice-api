import re
import json
import httpx

from app.config.config import settings
from app.prompts.llm_prompts import llm_prompt

from app.fallback.missing import guess_customer_from_ocr
from app.fallback.pruner import prune_ocr_text
from app.fallback.dates import guess_dates_from_ocr
from app.fallback.guard import guard_llm_output
from app.fallback.totals import guess_total_from_ocr
from app.fallback.quality import is_low_quality_ocr
from app.fallback.grounding import ground_fields, should_skip_llm


# --------------------------------------------

# ----------- Text Extraction -----------

def extract_invoice_fields(ocr_text: str, ocr_raw: str = "") -> dict:

    # Use raw if available (often better for dates/totals), otherwise best_text
    source_text = ocr_raw or ocr_text
    source_text = source_text or ""

    # ✅ HARD STOP: if OCR is garbage, don't call LLM (prevents hallucinations)
    # (you can choose either function; keep both for safety)
    if should_skip_llm(source_text) or is_low_quality_ocr(source_text):
        # still try regex fallbacks even if LLM skipped
        issued, due = guess_dates_from_ocr(source_text)
        tot = guess_total_from_ocr(source_text)
        cust = guess_customer_from_ocr(source_text)

        return {
            "supplier_name": None,
            "customer_name": cust if cust else None,
            "date_issued": issued if issued else None,
            "due_date": due if due else None,
            "total_amount": tot if tot else None,
            "warning": "OCR too noisy, skipped LLM extraction"
        }

    prompt = f"""
        {llm_prompt}

    OCR TEXT:
        {prune_ocr_text(source_text)}
    """.strip()

    payload = {
        "model": settings.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You output only valid JSON. No extra text."},
            {"role": "user", "content": prompt[:1200]},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 120,   # slightly higher to avoid cutting JSON
            "num_ctx": 2048       # more context reduces guessing
        },
    }

    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"

    r = httpx.post(url, json=payload, timeout=600)
    r.raise_for_status()

    raw = r.json()["message"]["content"].strip()

    try:
        data = json.loads(raw)

        # -------- Date Fallbacks --------
        issued, due = guess_dates_from_ocr(source_text)

        if not data.get("date_issued") and issued:
            data["date_issued"] = issued

        if not data.get("due_date") and due:
            data["due_date"] = due

        # -------- Fallback for customer_name --------
        if not data.get("customer_name"):
            guess = guess_customer_from_ocr(source_text)
            if guess:
                data["customer_name"] = guess

        # -------- Fallback for total_amount --------
        # NOTE: total_amount can be 0.0 so check "is None" not "not data.get"
        if data.get("total_amount") is None:
            tot = guess_total_from_ocr(source_text)
            if tot is not None:
                data["total_amount"] = tot

        # -------- Guard Hallucinations (your existing guard) --------
        data = guard_llm_output(data, source_text)

        # ✅ FINAL: grounding - drop any supplier/customer/total not found in OCR text
        data = ground_fields(data, source_text)

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
