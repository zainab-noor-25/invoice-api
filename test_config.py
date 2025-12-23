from app.config.config import settings

print(settings.APP_NAME)
print(settings.APP_ENV)
print(settings.MONGO_DB)
print(settings.QWEN_MODEL)
print("Has Mongo URI?", bool(settings.MONGO_URI))
