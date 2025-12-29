import os
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import UploadFile, HTTPException

from app.db.mongo import invoices_col, chunks_col
from app.utils.schemas import InvoiceFields
from app.graphs.graph import GRAPH
from app.fallback.dates import normalize_date

# ---------------------------------------- 

UPLOAD_DIR = "invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------------------------------

ALLOWED = {"image/png", "image/jpeg", "image/jpg"}

# ---------- Path Def ----------

def _build_path(invoice_id: str, content_type: str) -> str:
    ext = ".png" if content_type == "image/png" else ".jpg"
    return os.path.join(UPLOAD_DIR, f"{invoice_id}{ext}")

# ---------- Upload ----------

async def process_upload(file: UploadFile):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Only png/jpg/jpeg supported")

    invoice_oid = ObjectId()
    invoice_id = str(invoice_oid)

    path = _build_path(invoice_id, file.content_type)

    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # 1) Insert initial invoice doc (processing)
    invoices_col.insert_one({
        "_id": invoice_oid,
        "file_name": file.filename,
        "content_type": file.content_type,
        "file_path": path,
        "status": "processing",
        "created_at": datetime.now(timezone.utc),
    })

    # 2) Run LangGraph pipeline (OCR + LLM + Chunk+Embed)
    try:
        result = GRAPH.invoke({"file_path": path, "invoice_id": invoice_id})
    except Exception as e:
        invoices_col.update_one(
            {"_id": invoice_oid},
            {"$set": {"status": "error", "error": str(e), "updated_at": datetime.now(timezone.utc)}},
        )
        raise HTTPException(status_code=500, detail=f"Pipeline crashed: {e}")

    # 3) Handle pipeline error
    if result.get("error"):
        invoices_col.update_one(
            {"_id": invoice_oid},
            {"$set": {"status": "error", "error": result["error"], "updated_at": datetime.now(timezone.utc)}},
        )
        raise HTTPException(status_code=500, detail=result["error"])

    ocr_text = result.get("ocr_text") or ""
    fields_raw = result.get("fields") or {}

    # 4) Pydantic validation
    fields_obj = InvoiceFields(**fields_raw)
    fields = fields_obj.model_dump()

    # normalize dates (optional but good)
    fields["date_issued"] = normalize_date(fields.get("date_issued"))
    fields["due_date"] = normalize_date(fields.get("due_date"))

    # 5) Update invoice doc with outputs
    invoices_col.update_one(
        {"_id": invoice_oid},
        {"$set": {
            "status": "fields_extracted",
            "ocr_text": ocr_text,
            "fields": fields,
            "chunks_inserted": result.get("chunks_inserted", 0),
            "processed_image_path": result.get("processed_image_path"),
            "latest_image_path": result.get("latest_image_path"),
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    return {
        "invoice_id": invoice_id,
        "status": "fields_extracted",
        "ocr_preview": ocr_text[:300],
        "fields": fields,
        "chunks_inserted": result.get("chunks_inserted", 0),
        "processed_image_path": result.get("processed_image_path"),
        "latest_image_path": result.get("latest_image_path"),
    }

# ---------- List All---------- 

def list_invoices(limit: int = 20):
    cur = invoices_col.find({}, {"ocr_text": 0}).sort("created_at", -1).limit(limit)
    items = []
    for d in cur:
        d["invoice_id"] = str(d.pop("_id"))
        items.append(d)
    return {"items": items}

# ---------- Get by ID ----------

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

# ---------- Reprocessing Same Invoice ----------

def reprocess_invoice(invoice_id: str):
    inv = get_invoice(invoice_id)
    path = inv["file_path"]

    # delete old chunks to avoid duplicacy
    chunks_col.delete_many({"invoice_id": invoice_id})

    # update invoice status
    invoices_col.update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {"status": "reprocessing", "updated_at": datetime.now(timezone.utc)}},
    )

    try:
        result = GRAPH.invoke({"file_path": path, "invoice_id": invoice_id})
    except Exception as e:
        invoices_col.update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": {"status": "error", "error": str(e), "updated_at": datetime.now(timezone.utc)}},
        )
        raise HTTPException(status_code=500, detail=f"Pipeline crashed: {e}")

    # For error
    if result.get("error"):
        invoices_col.update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": {"status": "error", "error": result["error"], "updated_at": datetime.now(timezone.utc)}},
        )
        raise HTTPException(status_code=500, detail=result["error"])

    ocr_text = result.get("ocr_text") or ""
    ocr_raw = result.get("ocr_raw") or ""
    ocr_processed = result.get("ocr_processed") or ""
    fields_raw = result.get("fields") or {}

    fields_obj = InvoiceFields(**fields_raw)
    fields = fields_obj.model_dump()

    fields["date_issued"] = normalize_date(fields.get("date_issued"))
    fields["due_date"] = normalize_date(fields.get("due_date"))

    invoices_col.update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {
            "ocr_text": ocr_text,
            "ocr_raw": ocr_raw,
            "ocr_processed": ocr_processed,
            "fields": fields,
            "status": "fields_extracted",
            "chunks_inserted": result.get("chunks_inserted", 0),
            "processed_image_path": result.get("processed_image_path"),
            "latest_image_path": result.get("latest_image_path"),
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    return {
        "invoice_id": invoice_id,
        "status": "fields_extracted",
        "fields": fields,
        "chunks_inserted": result.get("chunks_inserted", 0),
        "processed_image_path": result.get("processed_image_path"),
        "latest_image_path": result.get("latest_image_path"),
    }
