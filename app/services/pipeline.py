from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.services.ocr import run_ocr
from app.services.llm import extract_invoice_fields

class PipeState(TypedDict):
    file_path: str
    ocr_text: Optional[str]
    fields: Optional[dict]
    error: Optional[str]

def step_ocr(state: PipeState) -> PipeState:
    try:
        state["ocr_text"] = run_ocr(state["file_path"])
    except Exception as e:
        state["error"] = f"OCR failed: {e}"
    return state

def step_extract(state: PipeState) -> PipeState:
    if state.get("error"):
        return state
    try:
        out = extract_invoice_fields(state.get("ocr_text") or "")
        state["fields"] = out if isinstance(out, dict) else None
    except Exception as e:
        state["error"] = f"LLM failed: {e}"
    return state

def router(state: PipeState) -> str:
    return "fail" if state.get("error") else "ok"

graph = StateGraph(PipeState)
graph.add_node("ocr", step_ocr)
graph.add_node("extract", step_extract)

graph.set_entry_point("ocr")
graph.add_edge("ocr", "extract")
graph.add_conditional_edges("extract", router, {"ok": END, "fail": END})

PIPELINE = graph.compile()
