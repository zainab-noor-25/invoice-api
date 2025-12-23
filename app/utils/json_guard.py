import json

# --------------------------------------------

# ----------- Safe JSON Parsing & Validation -----------

def safe_json_load(text: str) -> dict:
    try:
        return json.loads(text)
    
    except json.JSONDecodeError:
        return {}
