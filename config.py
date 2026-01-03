import os
import pathlib
import urllib.parse

import connexion
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

basedir = pathlib.Path(__file__).parent.resolve()


connex_app = connexion.App(__name__, specification_dir=basedir)
app = connex_app.app


db = SQLAlchemy()
ma = Marshmallow()


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



app.config["SQLALCHEMY_DATABASE_URI"] = build_db_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)
ma.init_app(app)
