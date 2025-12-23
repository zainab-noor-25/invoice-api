from pymongo import MongoClient
from app.config.config import settings

# --------------------------------------------

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

# ----------- DB Columns -----------

invoices_col = db["invoices"]
chunks_col = db["invoice_chunks"]
