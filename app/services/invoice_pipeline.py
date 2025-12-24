import os
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import UploadFile, HTTPException

from app.db.mongo import invoices_col
from app.services.ocr import run_ocr
from app.services.llm import extract_invoice_fields
from app.utils.json_guard import safe_json_load
from app.utils.schemas import InvoiceFields

UPLOAD_DIR = "invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED = {"image/png", "image/jpeg", "image/jpg"}


def _build_path(invoice_id: str, content_type: str) -> str:
    ext = ".png" if content_type == "image/png" else ".jpg"
    return os.path.join(UPLOAD_DIR, f"{invoice_id}{ext}")


async def process_upload(file: UploadFile):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Only png/jpg/jpeg supported")

    invoice_oid = ObjectId()
    invoice_id = str(invoice_oid)

    path = _build_path(invoice_id, file.content_type)

    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # OCR
    ocr_text = run_ocr(path)

    # LLM
    fields_raw = extract_invoice_fields(ocr_text)
    fields_dict = fields_raw if isinstance(fields_raw, dict) else safe_json_load(fields_raw)

    # Pydantic validation
    fields_obj = InvoiceFields(**fields_dict)
    fields = fields_obj.model_dump()

    doc = {
        "_id": invoice_oid,
        "file_name": file.filename,
        "content_type": file.content_type,
        "file_path": path,
        "status": "fields_extracted",
        "created_at": datetime.now(timezone.utc),
        "ocr_text": ocr_text,
        "fields": fields,
    }

    invoices_col.insert_one(doc)

    return {
        "invoice_id": invoice_id,
        "status": "fields_extracted",
        "ocr_preview": ocr_text[:300],
        "fields": fields,
    }


def list_invoices(limit: int = 20):
    cur = invoices_col.find({}, {"ocr_text": 0}).sort("created_at", -1).limit(limit)
    items = []
    for d in cur:
        d["invoice_id"] = str(d.pop("_id"))
        items.append(d)
    return {"items": items}


def get_invoice(invoice_id: str):
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice_id")

    d = invoices_col.find_one({"_id": oid}, {"ocr_text": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Invoice not found")

    d["invoice_id"] = str(d.pop("_id"))
    return d


def reprocess_invoice(invoice_id: str):
    inv = get_invoice(invoice_id)
    path = inv["file_path"]

    ocr_text = run_ocr(path)

    fields_raw = extract_invoice_fields(ocr_text)
    fields_dict = fields_raw if isinstance(fields_raw, dict) else safe_json_load(fields_raw)

    fields_obj = InvoiceFields(**fields_dict)
    fields = fields_obj.model_dump()

    invoices_col.update_one(
        {"_id": ObjectId(invoice_id)},
        {
            "$set": {
                "ocr_text": ocr_text,
                "fields": fields,
                "status": "fields_extracted",
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return {"invoice_id": invoice_id, "status": "fields_extracted", "fields": fields}
