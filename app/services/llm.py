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
from app.fallback.quality import is_low_quality_ocr  # ✅ keep quality


# --------------------------------------------
# ----------- Text Extraction -----------
# --------------------------------------------

def extract_invoice_fields(ocr_text: str, ocr_raw: str = "") -> dict:

    """
    Strategy:
    1) Prefer raw OCR when available
    2) If OCR is very poor → skip LLM, use heuristics only
    3) Else → LLM extraction + controlled fallbacks
    """
    source_text = (ocr_raw or ocr_text or "").strip()

    # If OCR empty
    if not source_text:
        return {
            "supplier_name": None,
            "customer_name": None,
            "date_issued": None,
            "due_date": None,
            "total_amount": None,
            "warning": "Empty OCR text"
        }

    # ---------- If OCR is too noisy → skip LLM ----------
    if is_low_quality_ocr(source_text):
        issued, due = guess_dates_from_ocr(source_text)
        tot = guess_total_from_ocr(source_text)
        cust = guess_customer_from_ocr(source_text)

        return {
            "supplier_name": None,
            "customer_name": cust if cust else None,
            "date_issued": issued if issued else None,
            "due_date": due if due else None,
            "total_amount": tot if tot is not None else None,
            "warning": "OCR too noisy, skipped LLM extraction"
        }

    # ---------- LLM Extraction ----------
    prompt = f"""
{llm_prompt}

OCR TEXT:
{prune_ocr_text(source_text)}
""".strip()

    payload = {
        "model": settings.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Output must only be valid JSON. No extra text."},
            {"role": "user", "content": prompt[:1600]},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 160,  # higher so JSON doesn’t cut
            "num_ctx": 2048
        },
    }

    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"

    r = httpx.post(url, json=payload, timeout=600)
    r.raise_for_status()

    raw = (r.json().get("message", {}).get("content") or "").strip()

    try:
        data = json.loads(raw)

    except json.JSONDecodeError:
        # If model breaks JSON → fallback to heuristics
        issued, due = guess_dates_from_ocr(source_text)
        tot = guess_total_from_ocr(source_text)
        cust = guess_customer_from_ocr(source_text)

        return {
            "supplier_name": None,
            "customer_name": cust if cust else None,
            "date_issued": issued if issued else None,
            "due_date": due if due else None,
            "total_amount": tot if tot is not None else None,
            "warning": "Model did not return valid JSON (fallback used)"
        }

# ------------------------------------
# FALLBACKS (ONLY IF MISSING)
# ------------------------------------

    # -------- Date Fallbacks --------
    issued, due = guess_dates_from_ocr(source_text)

    if not data.get("date_issued") and issued:
        data["date_issued"] = issued

    if not data.get("due_date") and due:
        data["due_date"] = due

    # -------- Fallback for customer_name --------
    if not data.get("customer_name"):
        cust = guess_customer_from_ocr(source_text)
        if cust:
            data["customer_name"] = cust

    # -------- Fallback for total_amount --------
    if data.get("total_amount") is None:
        tot = guess_total_from_ocr(source_text)
        if tot is not None:
            data["total_amount"] = tot

    # -------- Guard Hallucinations (your existing guard) --------
    data = guard_llm_output(data, source_text)

    return data


# ----------- Context Q/A --> Chat Bot -----------

def answer_from_context(prompt: str) -> str:
    payload = {
        "model": settings.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Answer must use the given context only."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 200},
    }

    url = settings.OLLAMA_BASE_URL.rstrip("/") + "/api/chat"
    r = httpx.post(url, json=payload, timeout=300)
    r.raise_for_status()

    return r.json()["message"]["content"].strip()
