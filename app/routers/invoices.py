from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.invoice_pipeline import (
    process_upload, get_invoice, list_invoices, reprocess_invoice  # , remove_invoice
)
router = APIRouter()

ALLOWED = {"image/png", "image/jpeg", "image/jpg"}

@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=400, detail="Only png/jpg/jpeg supported")
    return await process_upload(file)

@router.get("/")
def invoices_list(limit: int = 20):
    return list_invoices(limit)

@router.get("/{invoice_id}")
def invoice_detail(invoice_id: str):
    return get_invoice(invoice_id)

@router.post("/{invoice_id}/reprocess")
def invoice_reprocess(invoice_id: str):
    return reprocess_invoice(invoice_id)

# @router.delete("/{invoice_id}")
# def delete_invoice(invoice_id: str):
#     return remove_invoice(invoice_id)

