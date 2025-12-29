import re
from typing import Optional, Tuple
from datetime import datetime

# ---------------------------------------- 

def guess_dates_from_ocr(text: str):
    if not text:
        return None, None

    t = text.lower()

    issued = None
    due = None

    issued_patterns = [
        r"date\s*issued[:\s]*([0-9]{1,2}\s+\w+\s+[0-9]{4})",
        r"invoice\s+date[:\s]*([0-9]{1,2}\s+\w+\s+[0-9]{4})",
        r"date[:\s]*([0-9]{1,2}\s+\w+\s+[0-9]{4})",
    ]

    due_patterns = [
        r"due\s+date[:\s]*([0-9]{1,2}\s+\w+\s+[0-9]{4})",
        r"payment\s+due[:\s]*([0-9]{1,2}\s+\w+\s+[0-9]{4})",
    ]

    for p in issued_patterns:
        m = re.search(p, t)
        if m:
            issued = normalize_date(m.group(1))
            break

    for p in due_patterns:
        m = re.search(p, t)
        if m:
            due = normalize_date(m.group(1))
            break

    return issued, due



def normalize_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    try:
        # expects DD-MM-YYYY
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return date_str  # fallback: keep original
