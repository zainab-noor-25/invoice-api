from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from app.config.config import settings
from app.routers.invoices import router as invoices_router

# --------------------------------------------

app = FastAPI(title=settings.APP_NAME)

# ----------- Settings from Config -----------

CHAT_MODEL = settings.CHAT_MODEL
TOP_K_DEFAULT = settings.TOP_K
MAX_RETRIES = settings.MAX_RETRIES
ALLOW_ORIGINS = settings.allow_origins_list


# ----------- Invoice Router -----------

app.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])

# ----------- / -----------

@app.get("/", response_class=PlainTextResponse)
def home():
    return "------ WELCOME to Invoice API ------ Hit /docs ------"


# ----------- /health -----------

@app.get("/health")
def health():
    return {"status": "ok", "name": settings.APP_NAME, "env": settings.APP_ENV, "host": settings.APP_HOST, "port": settings.APP_PORT,}
