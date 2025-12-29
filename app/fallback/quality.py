def is_low_quality_ocr(text: str, min_chars: int = 80) -> bool:
    if not text:
        return True
    t = text.strip()
    # very short or mostly symbols = bad OCR
    if len(t) < min_chars:
        return True
    return False
