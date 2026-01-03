import os
import urllib.parse

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def build_db_uri() -> str:
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([server, database, username, password]):
        raise RuntimeError(
            "Missing DB env vars. Set DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD."
        )

    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

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
