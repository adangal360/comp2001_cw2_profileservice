from sqlalchemy import text
from config import db

# Lightweight database health check.
# This endpoint verifies that the application can execute a simple query
# against the configured SQL Server database.
def check():
    try:
        # Execute a trivial query to confirm database connectivity.
        result = db.session.execute(text("SELECT 1 AS ok")).mappings().first()

        ok = bool(result and result.get("ok") == 1)
        status = 200 if ok else 500

        return {"db_connected": ok}, status

    except Exception:
        # Any exception here indicates a database connectivity or configuration issue.
        return {"db_connected": False}, 500