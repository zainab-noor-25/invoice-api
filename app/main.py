from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from app.config.config import settings
from app.routers.invoices import router as invoices_router
from app.utils.errors import RequestIdMiddleware, global_exception_handler
from app.routers.chat import router as chat_router

# --------------------------------------------

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(RequestIdMiddleware)
app.add_exception_handler(Exception, global_exception_handler)

# ----------- Settings from Config -----------

CHAT_MODEL = settings.CHAT_MODEL
TOP_K_DEFAULT = settings.TOP_K
MAX_RETRIES = settings.MAX_RETRIES
ALLOW_ORIGINS = settings.allow_origins_list

# ----------- Invoice Router -----------

app.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
app.include_router(chat_router, tags=["Chat"])


# ----------- / -----------

@app.get("/", response_class=PlainTextResponse)
def root():
    return "------ WELCOME to Invoice API ------ Hit /docs ------"

# ----------- /health -----------

@app.get("/health")
def health():
    return {"status": "ok", "name": settings.APP_NAME, "env": settings.APP_ENV, "host": settings.APP_HOST, "port": settings.APP_PORT,}

# ----------- Ollama Warmup -----------

from app.services.embeddings import embed_text
from app.services.llm import answer_from_context
import os

@app.on_event("startup")
def warmup_models():
    if os.getenv("ENABLE_WARMUP", "0") != "1":
        print("ℹ️ Warmup disabled")
        return

    try:
        embed_text("warmup")
        answer_from_context("Say OK")
        print("✅ Ollama warmup done")
    except Exception as e:
        print("⚠️ Warmup failed:", e)

