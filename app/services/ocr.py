import os
import re
import cv2
import time
import numpy as np
import pytesseract
from app.config.config import settings

# --------------------------------------------

# ----------- Hard-set Tesseract executable path (Windows) -----------

pytesseract.pytesseract.tesseract_cmd = settings.OCR_ENGINE

# --------------------------------------------

DEBUG_DIR = os.path.join("invoices", "processed")
os.makedirs(DEBUG_DIR, exist_ok=True)

# ----------- Image Pre-processing -----------

def _preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    # 1) Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2) Upscale if small / pixelated
    h, w = gray.shape[:2]
    if max(h, w) < 1800:
        scale = 2.5
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # 3) Denoise (mild)
    gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

    # 4) Improve contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 5) Light sharpening
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]], dtype=np.float32)
    gray = cv2.filter2D(gray, -1, kernel)

    # 6) Threshold (Otsu)
    thres = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return thres

def _mild_preprocess(img: np.ndarray) -> np.ndarray:
    """Less aggressive: keeps details that Otsu sometimes kills."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape[:2]
    if max(h, w) < 1800:
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    return gray

# ----------- Scoring -----------

def _score_text(text: str) -> int:
    """
    Heuristic: prefer text containing invoice keywords + dates + totals.
    """
    t = (text or "").lower()
    score = 0

    for kw in ["invoice", "receipt", "bill to", "ship to", "total", "grand total", "due date", "date issued", "receipt date"]:
        if kw in t:
            score += 10

    score += 2 * len(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", t))
    score += min(len(text.strip()) // 100, 30)

    return score

# ----------- OCR -----------

def run_ocr(image_path: str, save_debug: bool = True) -> dict:
    abs_path = os.path.abspath(os.path.normpath(image_path))

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image not found: {abs_path}")

    img = cv2.imread(abs_path)
    if img is None:
        raise ValueError(f"OpenCV could not read image: {abs_path}")

    # Build 3 candidates (raw / mild / strong)
    raw_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mild_img = _mild_preprocess(img)
    strong_img = _preprocess_for_ocr(img)

    # OCR all
    cfg = r"--oem 3 --psm 4"
    raw_text = pytesseract.image_to_string(raw_gray, config=cfg)
    mild_text = pytesseract.image_to_string(mild_img, config=cfg)
    strong_text = pytesseract.image_to_string(strong_img, config=cfg)

    # Pick best by score
    best_text = raw_text
    best_img = raw_gray
    best_name = "raw"

    if _score_text(mild_text) > _score_text(best_text):
        best_text = mild_text
        best_img = mild_img
        best_name = "mild"

    if _score_text(strong_text) > _score_text(best_text):
        best_text = strong_text
        best_img = strong_img
        best_name = "strong"

    out_path = None
    latest_path = None

    # Save processed image (ALWAYS PNG)
    if save_debug:
        base = os.path.splitext(os.path.basename(abs_path))[0]
        ts = int(time.time())

        out_name = f"{base}_{best_name}_processed_{ts}.png"
        out_path = os.path.join(DEBUG_DIR, out_name)
        cv2.imwrite(out_path, best_img)

        latest_name = f"{base}_processed_latest.png"
        latest_path = os.path.join(DEBUG_DIR, latest_name)
        cv2.imwrite(latest_path, best_img)

    return {
        "best_text": best_text,
        "raw_text": raw_text,
        "processed_text": strong_text,     # keep this for debugging
        "mild_text": mild_text,            # extra debug (optional)
        "chosen_variant": best_name,       # raw / mild / strong
        "processed_image_path": out_path,
        "latest_image_path": latest_path,
    }
