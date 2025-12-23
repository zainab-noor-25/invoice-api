from app.services.llm import extract_invoice_fields

ocr_text = """
BRAND NAME
Invoice Date: 01/01/2020
Bill To: COMPANY NAME
Grand Total $535.00
"""

print("Calling Ollama...")
out = extract_invoice_fields(ocr_text)
print("Returned from Ollama.")
print(out)
