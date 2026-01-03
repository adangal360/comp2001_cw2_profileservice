import os
import pyodbc

SERVER = "dist-6-505.uopnet.plymouth.ac.uk"
DATABASE = "COMP2001_ADangal"
USERNAME = "ADangal"
PASSWORD = os.getenv("DB_PASSWORD") 
DRIVER = "{ODBC Driver 17 for SQL Server}"
SCHEMA = "CW2"

if not PASSWORD:
    raise RuntimeError("DB_PASSWORD environment variable is not set")

conn_str = (
    f"DRIVER={DRIVER};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    "Encrypt=Yes;"
    "TrustServerCertificate=Yes;"
    "Connection Timeout=30;"
    "Trusted_Connection=No;"
)

CREATE_SQL = f"""
-- Create schema if missing
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{SCHEMA}')
BEGIN
    EXEC('CREATE SCHEMA {SCHEMA}');
END;

-- PROFILE (FDG-driven)
IF OBJECT_ID('{SCHEMA}.Profile', 'U') IS NULL
BEGIN
    CREATE TABLE {SCHEMA}.Profile (
        Email       VARCHAR(30)  NOT NULL,
        Username    VARCHAR(30)  NOT NULL,
        AboutMe     VARCHAR(MAX) NULL,
        Location    VARCHAR(50)  NULL,
        Dob         DATE         NULL,
        Language    VARCHAR(30)  NULL,
        Password    VARCHAR(30)  NOT NULL,
        Role        VARCHAR(5)   NOT NULL CONSTRAINT DF_Profile_Role DEFAULT 'User',
        CONSTRAINT PK_Profile PRIMARY KEY (Email),
        CONSTRAINT CK_Profile_Role CHECK (Role IN ('Admin', 'User'))
    );
END;

-- ACTIVITY (FDG-driven)
IF OBJECT_ID('{SCHEMA}.Activity', 'U') IS NULL
BEGIN
    CREATE TABLE {SCHEMA}.Activity (
        Activity_id TINYINT IDENTITY(1,1) NOT NULL,
        Activity    VARCHAR(30) NOT NULL,
        CONSTRAINT PK_Activity PRIMARY KEY (Activity_id),
        CONSTRAINT UQ_Activity_Activity UNIQUE (Activity)
    );
END;

-- FAVOURITE ACTIVITY (FDG-driven link table)
IF OBJECT_ID('{SCHEMA}.FavouriteActivity', 'U') IS NULL
BEGIN
    CREATE TABLE {SCHEMA}.FavouriteActivity (
        Email       VARCHAR(30) NOT NULL,
        Activity_id TINYINT     NOT NULL,
        CONSTRAINT PK_FavouriteActivity PRIMARY KEY (Email, Activity_id),
        CONSTRAINT FK_FavAct_Profile FOREIGN KEY (Email)
            REFERENCES {SCHEMA}.Profile(Email)
            ON DELETE CASCADE,
        CONSTRAINT FK_FavAct_Activity FOREIGN KEY (Activity_id)
            REFERENCES {SCHEMA}.Activity(Activity_id)
            ON DELETE CASCADE
    );
END;
"""

def main():
    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(CREATE_SQL)
        print("✅ CW2 schema + tables created/verified (Profile, Activity, FavouriteActivity).")

if __name__ == "__main__":
    main()
