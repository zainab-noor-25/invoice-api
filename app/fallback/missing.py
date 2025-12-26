import re

def guess_customer_from_ocr(text: str):
    patterns = [
        r"(Bill To|Billed To|Customer|Client|Ship To)\s*[:\-]?\s*\n([^\n]{2,60})",
        r"(Bill To|Billed To|Customer|Client|Ship To)\s+([A-Za-z0-9&.,' -]{2,60})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(2).strip()
    return None
