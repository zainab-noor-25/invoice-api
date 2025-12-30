import os
import re
import numpy as np
import pytesseract
import pypdfium2 as pdfium
import pdfplumber

from app.config.config import settings

# --------------------------------------------
# Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = settings.OCR_ENGINE
# --------------------------------------------

def _clean_text(t: str) -> str:
    return re.sub(r"[ \t]+", " ", (t or "").replace("\x00", "")).strip()

def _pdf_text_first(pdf_path: str) -> str:
    """
    If PDF is text-based (not scanned), pdfplumber extracts clean text
    (better than OCR).
    """
    try:
        out = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:2]:  # first 1-2 pages usually enough
                txt = page.extract_text() or ""
                txt = _clean_text(txt)
                if txt:
                    out.append(txt)
        return "\n".join(out).strip()
    except Exception:
        return ""

def _render_pdf_page_to_rgb(pdf_path: str, page_index: int = 0, scale: float = 2.0) -> np.ndarray:
    """
    Render PDF page -> RGB numpy array using pypdfium2.
    scale=2.0 gives higher resolution for OCR.
    """
    pdf = pdfium.PdfDocument(pdf_path)
    if len(pdf) == 0:
        raise ValueError("PDF has 0 pages")

    page = pdf.get_page(page_index)
    bitmap = page.render(scale=scale)  # higher scale = sharper OCR
    pil_image = bitmap.to_pil()        # PIL image
    rgb = np.array(pil_image)          # (H, W, 3)
    page.close()
    pdf.close()
    return rgb

def run_ocr(file_path: str) -> dict:
    """
    PDF-only OCR:
    1) Try extract embedded text with pdfplumber
    2) If empty/too small => render page image using pdfium => OCR with tesseract
    """
    abs_path = os.path.abspath(os.path.normpath(file_path))
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")

    if not abs_path.lower().endswith(".pdf"):
        raise ValueError("run_ocr() expects a .pdf file now")

    # Text-based extraction first
    pdf_text = _pdf_text_first(abs_path)
    if len(pdf_text) >= 80:
        return {
            "best_text": pdf_text,
            "raw_text": pdf_text,
            "processed_text": pdf_text,
            "mode": "pdfplumber_text"
        }

    # Scanned PDF => render => OCR
    rgb = _render_pdf_page_to_rgb(abs_path, page_index=0, scale=2.0)

    # OCR on rendered page
    ocr_text = pytesseract.image_to_string(rgb, config=r"--oem 3 --psm 6")
    ocr_text = _clean_text(ocr_text)

    return {
        "best_text": ocr_text,
        "raw_text": ocr_text,
        "processed_text": ocr_text,
        "mode": "tesseract_on_rendered_pdf"
    }
