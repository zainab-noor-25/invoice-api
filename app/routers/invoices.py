import os
from bson import ObjectId
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException

# ----------- File Imports -----------

from app.db.mongo import invoices_col
from app.services.ocr import run_ocr
from app.services.llm import extract_invoice_fields
from app.utils.json_guard import safe_json_load

# --------------------------------------------

router = APIRouter()

UPLOAD_DIR = "invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------- Allowed File Types -----------

ALLOWED = {"image/png", "image/jpeg", "image/jpg"}

# ----------- Upload Router -----------

@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Only png/jpg/jpeg supported")

    # ----------- Save File -----------

    invoice_id = str(ObjectId())

    ext = ".png" if file.content_type == "image/png" else ".jpg"
    
    path = os.path.join(UPLOAD_DIR, f"{invoice_id}{ext}")

    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # ----------- OCR -----------

    ocr_text = run_ocr(path)

   # ----------- LLM -----------

    fields_raw = extract_invoice_fields(ocr_text)
    fields = fields_raw if isinstance(fields_raw, dict) else safe_json_load(fields_raw)

#     invoices_col.update_one(
#         {"_id": res.inserted_id},
#         {
#             "$set": {
#                 "fields": fields,
#                 "status": "fields_extracted"
#             }
#         }
# )

    # ----------- Store Metadata in Mongo DB -----------

    doc = {
        "_id": invoice_id,
        "file_name": file.filename,
        "content_type": file.content_type,
        "file_path": path,
        "status": "uploaded, 200, OK",
        "created_at": datetime.now(timezone.utc),
        "ocr_text": ocr_text,
        "fields": fields,
        # "fields": {
        #     "supplier_name": None,
        #     "customer_name": None,
        #     "invoice_date": None,
        #     "total_amount": None,
        # },
    }

    res = invoices_col.insert_one(doc)

    return {
            "invoice_id": str(res.inserted_id), 
            "status 1": "Uploaded & OCR done",
            "ocr_preview": ocr_text[:300],
            "status 2": "Fields_extracted",
            "fields": fields,
            }
