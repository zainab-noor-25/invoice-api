from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.db.mongodb import invoices_col
from app.services.embeddings import embed_text
from app.services.retrieval import retrieve_chunks
from app.services.llm import answer_from_context

router = APIRouter()

FIELD_ALIASES = {
    "supplier name": "supplier_name",
    "supplier_name": "supplier_name",
    "vendor name": "supplier_name",

    "customer name": "customer_name",
    "customer_name": "customer_name",
    "client name": "customer_name",

    "invoice date": "date_issued",
    "issue date": "date_issued",
    "date issued": "date_issued",
    "date_issued": "date_issued",

    "due date": "due_date",
    "payment due": "due_date",
    "due_date": "due_date",

    "total amount": "total_amount",
    "total_amount": "total_amount",
    "total": "total_amount",
    "grand total": "total_amount",
    "total due": "total_amount",
}


@router.post("/chat")
def chat(invoice_id: str, question: str):
    # 1) Load invoice
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice_id")

    inv = invoices_col.find_one({"_id": oid})
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    fields = inv.get("fields") or {}

    q = question.strip().lower().replace("?", "").replace("  ", " ")

    # 2) If question maps to a known field, return it directly
    field_key = FIELD_ALIASES.get(q)
    if field_key:
        val = fields.get(field_key)
        return {
            "answer": val if val is not None else "Sorry, I did not find it in provided context.",
            "used_chunks": [],
            "source": "fields",
        }

    # 3) Otherwise do chunk-based RAG
    hits = retrieve_chunks(invoice_id, question)

    if not hits:
        return {"answer": "Sorry, I did not find it in provided context.", "used_chunks": []}

    context = "\n\n".join(h["text"] for h in hits)

    prompt = f"""
Answer ONLY using the context below.
If the answer is not in the context, say exactly:
Sorry, I did not find it in provided context.

CONTEXT:
{context}

QUESTION:
{question}
""".strip()

    answer = answer_from_context(prompt)

    return {
        "answer": answer,
        "used_chunks": [h["chunk_id"] for h in hits],
        "source": "chunks",
    }
