import re
from typing import Any, Dict, Optional

BAD_NAMES = {"client", "customer", "bill to", "ship to", "attention", "attn", "none", "null", "n/a", "na"}

def _has_name_evidence(text: str, value: Optional[str]) -> bool:
    if not value:
        return False

    v = value.lower().strip()
    t = text.lower()

    # direct substring
    if v in t:
        return True

    # relaxed token match (any meaningful word)
    tokens = [tok for tok in re.split(r"\W+", v) if len(tok) >= 4]
    hits = sum(1 for tok in tokens if tok in t)

    return hits >= 1 or v.replace(" ", "") in t.replace(" ", "")


def _has_amount_evidence(text: str, amount: Any) -> bool:
    if amount is None:
        return False

    t = text.replace(",", "").replace("$", "")
    a = str(amount).replace(",", "").replace("$", "")

    return a in t


def guard_llm_output(data: Dict[str, Any], ocr_text: str) -> Dict[str, Any]:
    """
    Remove hallucinated fields unless there's evidence in OCR text.
    Does NOT overwrite values with new guesses; only nulls bad ones.
    """
    src = (ocr_text or "").strip()
    if not src:
        return {
            "supplier_name": None,
            "customer_name": None,
            "date_issued": None,
            "due_date": None,
            "total_amount": None,
        }

    # Guard names
    # Guard customer only (supplier headers are noisy in OCR)
    if data.get("customer_name") and not _has_name_evidence(src, data.get("customer_name")):
        data["customer_name"] = None

    # Guard totals
    if data.get("total_amount") is not None and not _has_amount_evidence(src, data["total_amount"]):
        data["total_amount"] = None

    return data
