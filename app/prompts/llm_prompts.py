
llm_prompt = f"""
Extract invoice fields from OCR text.

Return ONLY valid JSON. No explanations.

Fields:

Return JSON with:

- supplier_name: the seller/vendor/company issuing the invoice (usually top header)
- supplier_name must be the seller/vendor company, not the top header person's name unless clearly labeled seller/vendor.

- customer_name: the buyer/client. Look for labels like "Bill To", "Billed To", "Ship To", "Customer", "Client", "Attention", "Attn".
  If the invoice contains a billing address but no explicit name, infer the company/person name from the first line of that block.

- customer_name must be the actual name, not words like "Client", "Bill To", "Ship To".
   If the OCR contains labels like “Client:” or “Bill to:” then customer_name must be the PERSON/COMPANY after it, not the label itself. Never output “Client”, “Bill To”, “Ship To” as names.


- date_issued (the invoice "Date Issued" / "Invoice Date" / "Date")
- due_date (the invoice "Due Date" / "Payment Due")

- total_amount: number only
- “total_amount must be the GRAND TOTAL / TOTAL DUE. Do NOT return subtotal.”

If multiple candidates, choose the most likely buyer name (Bill To > Ship To).

Dates must be in YYYY-MM-DD format.

If a field is missing, use null.

"""