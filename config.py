import os
import pathlib
import urllib.parse

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Shared SQLAlchemy and Marshmallow instances.
# These are initialised in app.py once the Flask app is created.
db = SQLAlchemy()
ma = Marshmallow()


def build_db_uri() -> str:
    """
    Build a SQLAlchemy-compatible database URI for SQL Server using pyodbc.

    Connection details are provided via environment variables so that:
    - credentials are not hard-coded
    - the service can run consistently in Docker and locally
    """

    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    # Fail fast if any required configuration is missing.
    if not all([server, database, username, password]):
        raise RuntimeError(
            "Missing DB env vars. Set DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD."
        )

    # Allow the ODBC driver to be overridden if needed,
    # but default to the SQL Server 17 driver used in CW2.
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

    # Build a raw ODBC connection string.
    # This is URL-encoded before being passed to SQLAlchemy.
    odbc_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_str)