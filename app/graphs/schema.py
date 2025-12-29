from typing import TypedDict, Optional

# ---------- Defination ----------

class GraphState(TypedDict, total=False):
    file_path: str
    invoice_id: str

    ocr_text: Optional[str]
    ocr_raw: Optional[str]
    ocr_processed: Optional[str]

    processed_image_path: Optional[str]
    latest_image_path: Optional[str]

    fields: Optional[dict]
    chunks_inserted: Optional[int]
    error: Optional[str]
