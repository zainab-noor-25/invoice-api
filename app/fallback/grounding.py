import re
from typing import Dict, Any, Optional

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def _contains(haystack: str, needle: str) -> bool:
    h = _norm(haystack)
    n = _norm(needle)
    if not n or len(n) < 3:
        return False
    return n in h

def _number_in_text(text: str, amount: Any) -> bool:
    if amount is None:
        return False
    try:
        a = float(amount)
    except Exception:
        return False
    # match 3000 / 3,000 / 3000.00 / $3,000.00
    patterns = [
        rf"\b{int(a):,}\b".replace(",", r"[,\s]?"),
        rf"\b{a:,.2f}\b".replace(",", r"[,\s]?"),
    ]
    t = text or ""
    return any(re.search(p, t) for p in patterns)

def should_skip_llm(ocr_text: str) -> bool:
    """
    If OCR looks like noise, extraction will hallucinate.
    """
    t = (ocr_text or "").strip()
    if len(t) < 80:
        return True
    letters = sum(ch.isalpha() for ch in t)
    weird = sum((not ch.isalnum()) and (not ch.isspace()) for ch in t)
    # too few letters or too many weird characters => noisy OCR
    if letters < 25:
        return True
    if weird / max(len(t), 1) > 0.25:
        return True
    return False

def ground_fields(data: Dict[str, Any], ocr_text: str) -> Dict[str, Any]:
    """
    Keep only values that appear in OCR (or are regex verifiable).
    If not grounded => set None so it doesn't lie.
    """
    text = ocr_text or ""

    out = dict(data or {})
    # supplier/customer must appear in OCR text
    if out.get("supplier_name") and not _contains(text, out["supplier_name"]):
        out["supplier_name"] = None

    if out.get("customer_name") and not _contains(text, out["customer_name"]):
        # Also block generic labels
        if _norm(out["customer_name"]) in {"client", "customer", "bill to", "ship to", "billed to"}:
            out["customer_name"] = None
        else:
            out["customer_name"] = None

    # dates: just ensure there is at least something date-like near keywords
    # (simple guard: if model gave date but OCR has no dates at all -> drop)
    has_any_date = bool(re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b", text))
    if out.get("date_issued") and not has_any_date:
        out["date_issued"] = None
    if out.get("due_date") and not has_any_date:
        out["due_date"] = None

    # total amount must appear
    if out.get("total_amount") is not None and not _number_in_text(text, out["total_amount"]):
        out["total_amount"] = None

    return out
