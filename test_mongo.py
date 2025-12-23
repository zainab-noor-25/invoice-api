from app.db.mongo import db

print("Connected DB:", db.name)
print("Collections:", db.list_collection_names())
