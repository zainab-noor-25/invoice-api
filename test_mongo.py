from app.db.mongodb import db

print("Connected DB:", db.name)
print("Collections:", db.list_collection_names())
