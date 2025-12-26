# from io import BytesIO
import cv2
import pytesseract
from PIL import Image
from app.config.config import settings

# --------------------------------------------

# ----------- Hard-set Tesseract executable path (Windows) -----------

pytesseract.pytesseract.tesseract_cmd = settings.OCR_ENGINE

# ----------- OCR -----------

def run_ocr(image_path: str) -> str:
    """Run OCR on invoice images and return extracted text."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # denoise + threshold
    gray = cv2.medianBlur(gray, 3)
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thr, config=config)

    return text

# def ocr_image_bytes(image_bytes: bytes) -> str:
#     """Run OCR on invoice image bytes and return extracted text."""
#     img = Image.open(BytesIO(image_bytes)).convert("RGB")
#     text = pytesseract.image_to_string(img)
#     return text.strip()
