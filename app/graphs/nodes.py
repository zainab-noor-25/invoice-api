import time

from app.db.vectordb import get_index
from app.graphs.schema import GraphState

from app.services.ocr import run_ocr
from app.services.llm import extract_invoice_fields
from app.services.chunking import chunk_text
from app.services.embeddings import embed_text

# ----------------------------------------

# ---------- OCR ----------

from app.services.ocr import run_ocr

def step_ocr(state):
    try:
        ocr_out = run_ocr(state["file_path"])
        state["ocr_text"] = ocr_out.get("best_text", "")
        state["ocr_raw"] = ocr_out.get("raw_text", "")
        state["ocr_processed"] = ocr_out.get("processed_text", "")
    except Exception as e:
        state["error"] = f"OCR failed: {e}"
    return state


# ---------- Extraction ----------

def step_extract(state: GraphState) -> GraphState:
    if state.get("error"):
        return state
    
    try:
        t0 = time.time()
        out = extract_invoice_fields(state.get("ocr_text") or "", state.get("ocr_raw") or "")
        print("extract: done in", round(time.time() - t0, 2), "sec")
        state["fields"] = out if isinstance(out, dict) else {}

    except Exception as e:
        state["error"] = f"LLM failed: {e}"

    return state

# ----------  Chunking + Embedding ----------

def step_chunk_embed(state: GraphState) -> GraphState:
    if state.get("error"):
        return state

    try:
        ocr_text = (state.get("ocr_text") or "").strip()
        if not ocr_text:
            state["chunks_inserted"] = 0
            return state

        print("chunk_embed: starting")

        chunks = chunk_text(ocr_text, size=1500, overlap=150)
        
        print("chunk_embed: total chunks =", len(chunks))

        docs = []
        t0 = time.time()

        index = get_index()
        vectors = []

        for c in chunks:
            emb = embed_text(c["text"])

            vid = f"{state['invoice_id']}::{c['chunk_id']}"

            vectors.append((
                vid,
                emb,
                {
                    "invoice_id": state["invoice_id"],
                    "chunk_id": c["chunk_id"],
                    "text": c["text"],
                    **(c.get("meta") or {}),
                }
            ))

        if vectors:
            index.upsert(vectors=vectors)

        state["chunks_inserted"] = len(vectors)

    except Exception as e:
        state["error"] = f"Chunk/Embed failed: {type(e).__name__}: {e}"

    return state

# ---------- Router ----------

def router(state: GraphState) -> str:
    return "fail" if state.get("error") else "ok"