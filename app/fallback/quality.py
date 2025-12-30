import re

def is_low_quality_ocr(text: str) -> bool:
    if not text:
        return True

    t = text.strip()

    # Too short AND no numbers → bad
    if len(t) < 40 and not re.search(r"\d", t):
        return True

    # Mostly symbols / garbage
    alnum_ratio = sum(c.isalnum() for c in t) / max(len(t), 1)
    if alnum_ratio < 0.35:
        return True

    # No invoice-like keywords AND no numbers → suspicious
    keywords = [
        "invoice", "receipt", "total", "bill", "due", "date", "amount", "$"
    ]
    if not any(k in t.lower() for k in keywords) and not re.search(r"\d", t):
        return True

    return False
