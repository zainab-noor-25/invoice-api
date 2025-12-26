
def prune_ocr_text(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    keep = []

    keywords = (
        "invoice", "bill to", "bill for", "billed to", "ship to",
        "total", "amount", "subtotal", "tax",
        "date", "invoice date", "vendor", "supplier"
    )

    for l in lines:
        if any(k in l.lower() for k in keywords):
            keep.append(l)

    # fallback if pruning too aggressive
    if len(keep) < 10:
        return "\n".join(lines[:40])

    return "\n".join(keep[:40])
