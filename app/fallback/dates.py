import re

# ---------------------------------------- 

def guess_dates_from_ocr(text: str):
    def find(label_patterns):
        for pat in label_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    issued = find([
        r"Date Issued[:\s]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
        r"Invoice Date[:\s]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
        r"\bDate[:\s]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
    ])
    due = find([
        r"Due Date[:\s]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
        r"Payment Due[:\s]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
    ])
    return issued, due
