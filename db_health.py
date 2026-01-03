from sqlalchemy import text
from config import db

def check():
    try:
        result = db.session.execute(text("SELECT 1 AS ok")).mappings().first()
        ok = bool(result and result.get("ok") == 1)
        return {"db_connected": ok}, 200 if ok else 500
    except Exception as e:
        return {"db_connected": False, "error": str(e)}, 500

