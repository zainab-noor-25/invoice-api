from app.services.ocr import run_ocr

image_path = "./sample_invoices/5.PNG"

text = run_ocr(image_path)
print(text[:1200])
