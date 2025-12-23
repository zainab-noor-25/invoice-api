from dotenv import load_dotenv
import os

load_dotenv()  # reads .env from project root

print("APP_ENV       =", os.getenv("APP_ENV"))
print("MONGO_DB      =", os.getenv("MONGO_DB"))
print("QWEN_MODEL    =", os.getenv("QWEN_MODEL"))
print("LANG_PROJECT  =", os.getenv("LANGCHAIN_PROJECT"))
