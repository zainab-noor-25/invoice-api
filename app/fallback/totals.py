import re
from typing import Optional

def guess_total_from_ocr(text: str) -> Optional[float]:
    if not text:
        return None

    t = text.replace(",", "")

    patterns = [
        r"amount\s+due\s*\(usd\)\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        r"grand\s+total\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
        r"total\s+due\s*\$?\s*([0-9]+(?:\.[0-9]{2})?)",
    ]

    for p in patterns:
        m = re.search(p, t, re.IGNORECASE)
        if m:
            return float(m.group(1))

    return None
