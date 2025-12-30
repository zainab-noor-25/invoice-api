from typing import TypedDict, Optional

# ---------- Defination ----------

class GraphState(TypedDict, total=False):
    file_path: str
    invoice_id: str
    ocr_text: Optional[str]
    fields: Optional[dict]
    chunks_inserted: Optional[int]
    error: Optional[str]
