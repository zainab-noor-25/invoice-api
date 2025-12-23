import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# ----------------------------------------

load_dotenv()

class Settings(BaseSettings):

    # ---------- App ----------

    APP_NAME: str = "Invoice-API"
    APP_ENV: str = "development"

    # ---------- Server ----------

    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = int(os.getenv("APP_PORT", "8001"))
    ALLOW_ORIGINS: str = ""

    # ---------- MongoDB Atlas ----------

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "invoice_api")

    # ---------- OCR ----------

    OCR_ENGINE: str = os.getenv("OCR_ENGINE", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

    # ---------- Embeddings ----------

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # ---------- LLM Model ----------

    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "qwen2.5:3b-instruct")    #3b

    ## ---------- Tried LLM Models ----------

    # CHAT_MODEL: str = "qwen2.5:3b-instruct"      #3b
    # CHAT_MODEL: str = "qwen2.5:7b-instruct"      #7b
    # CHAT_MODEL: str = "gemma2:2b-instruct"       #2b
    # CHAT_MODEL: str = "qwen3:4b"                 #4b

    # ---------- Tuning ----------

    TOP_K: int = 4
    MAX_RETRIES: int = 2
    CACHE_SIZE: int = 200
    CONNECTION_POOL_SIZE: int = 100
    KEEPALIVE_TIMEOUT: int = 60
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60

    # ---------- LangSmith ----------

    LANGCHAIN_TRACING_V2: str | None = None
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def allow_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOW_ORIGINS.split(",") if o.strip()]

settings = Settings()
