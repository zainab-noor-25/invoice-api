
from langgraph.graph import StateGraph, END
from app.graphs.schema import GraphState
from app.graphs.nodes import step_ocr, step_extract, step_chunk_embed, router

# ----------------------------------------

# ---------- Nodes ----------

graph = StateGraph(GraphState)
graph.add_node("ocr", step_ocr)
graph.add_node("extract", step_extract)
graph.add_node("chunk_embed", step_chunk_embed)

# ---------- Edges ----------

graph.set_entry_point("ocr")
graph.add_edge("ocr", "extract")
graph.add_conditional_edges("extract", router, {"ok": "chunk_embed", "fail": END})
graph.add_conditional_edges("chunk_embed", router, {"ok": END, "fail": END})

# ---------- Complie ----------

GRAPH = graph.compile()
