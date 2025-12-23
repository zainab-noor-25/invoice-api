# from io import BytesIO
from PIL import Image
import pytesseract
from app.config.config import settings

# --------------------------------------------

# ----------- Hard-set Tesseract executable path (Windows) -----------

pytesseract.pytesseract.tesseract_cmd = settings.OCR_ENGINE

# ----------- OCR -----------

def run_ocr(image_path: str) -> str:
    """Run OCR on invoice images and return extracted text."""
    img = Image.open(image_path).convert("RGB")
    text = pytesseract.image_to_string(img)
    return text.strip()

# def ocr_image_bytes(image_bytes: bytes) -> str:
#     """Run OCR on invoice image bytes and return extracted text."""
#     img = Image.open(BytesIO(image_bytes)).convert("RGB")
#     text = pytesseract.image_to_string(img)
#     return text.strip()
