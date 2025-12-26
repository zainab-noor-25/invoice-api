from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

# ---------------------------------------- 

# ---------- Invoice Fields ---------- 

class InvoiceFields(BaseModel):
    supplier_name: Optional[str] = None
    customer_name: Optional[str] = None
    
    date_issued: Optional[str] = None
    due_date: Optional[str] = None
    
    total_amount: Optional[float] = None

# ---------- Upload Response Fields ---------- 

class UploadResponse(BaseModel):
    invoice_id: str
    status: str
    ocr_preview: str
    fields: Optional[InvoiceFields] = None

# ---------- Invoice Response Fields ----------     

class InvoiceResponse(BaseModel):
    invoice_id: str
    file_name: str
    content_type: str
    status: Literal["uploaded", "ocr_done", "fields_extracted", "failed"]
    created_at: datetime
    fields: Optional[InvoiceFields] = None
    ocr_preview: Optional[str] = None

# ---------- Listing Fields ---------- 

class ListResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    skip: int
    limit: int
