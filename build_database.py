# build_database.py  (UPDATED: adds ProfileAudit + trigger + view + stored procedure)

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

-- PROFILE AUDIT (for Trigger evidence)
IF OBJECT_ID('{SCHEMA}.ProfileAudit', 'U') IS NULL
BEGIN
    CREATE TABLE {SCHEMA}.ProfileAudit (
        AuditId     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ProfileAudit PRIMARY KEY,
        Email       VARCHAR(30)        NOT NULL,
        Action      VARCHAR(20)        NOT NULL,
        ChangedAt   DATETIME2(0)       NOT NULL CONSTRAINT DF_ProfileAudit_ChangedAt DEFAULT (SYSUTCDATETIME()),
        ChangedBy   SYSNAME            NULL,
        Details     VARCHAR(200)       NULL
    );
END;

-- TRIGGER: audit Profile INSERT
IF OBJECT_ID('{SCHEMA}.trg_Profile_Audit_Insert', 'TR') IS NOT NULL
    DROP TRIGGER {SCHEMA}.trg_Profile_Audit_Insert;

-- STORED PROCEDURE: upsert profile
IF OBJECT_ID('{SCHEMA}.usp_UpsertProfile', 'P') IS NOT NULL
    DROP PROCEDURE {SCHEMA}.usp_UpsertProfile;
"""

TRIGGER_SQL = f"""
CREATE TRIGGER {SCHEMA}.trg_Profile_Audit_Insert
ON {SCHEMA}.Profile
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO {SCHEMA}.ProfileAudit (Email, Action, ChangedAt, ChangedBy, Details)
    SELECT
        i.Email,
        'INSERT',
        SYSUTCDATETIME(),
        SUSER_SNAME(),
        CONCAT('Profile created (Role=', i.Role, ')')
    FROM inserted i;
END;
"""

# VIEW: profiles + favourites + activity name (report-friendly)
VIEW_SQL = f"""
IF OBJECT_ID('{SCHEMA}.vw_ProfileFavourites', 'V') IS NOT NULL
    DROP VIEW {SCHEMA}.vw_ProfileFavourites;

EXEC('
CREATE VIEW {SCHEMA}.vw_ProfileFavourites
AS
SELECT
    p.Email,
    p.Username,
    p.Role,
    a.Activity_id,
    a.Activity
FROM {SCHEMA}.Profile AS p
LEFT JOIN {SCHEMA}.FavouriteActivity AS fa
    ON fa.Email = p.Email
LEFT JOIN {SCHEMA}.Activity AS a
    ON a.Activity_id = fa.Activity_id;
');
"""

# Stored procedure: kept inside EXEC('...') to avoid "CREATE PROCEDURE must be first in batch" issues
PROC_SQL = f"""
EXEC('
CREATE PROCEDURE {SCHEMA}.usp_UpsertProfile
    @Email      VARCHAR(30),
    @Username   VARCHAR(30),
    @AboutMe    VARCHAR(MAX) = NULL,
    @Location   VARCHAR(50)  = NULL,
    @Dob        DATE         = NULL,
    @Language   VARCHAR(30)  = NULL,
    @Password   VARCHAR(30),
    @Role       VARCHAR(5)   = ''User''
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = @Email)
    BEGIN
        UPDATE {SCHEMA}.Profile
        SET
            Username  = @Username,
            AboutMe   = @AboutMe,
            Location  = @Location,
            Dob       = @Dob,
            Language  = @Language,
            Password  = @Password,
            Role      = @Role
        WHERE Email = @Email;

        SELECT ''UPDATED'' AS result;
    END
    ELSE
    BEGIN
        INSERT INTO {SCHEMA}.Profile (Email, Username, AboutMe, Location, Dob, Language, Password, Role)
        VALUES (@Email, @Username, @AboutMe, @Location, @Dob, @Language, @Password, @Role);

        SELECT ''CREATED'' AS result;
    END
END
');
"""

SEED_SQL = f"""
-- Seed required accounts (roles are stored in Trail App DB)
IF NOT EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = 'grace@plymouth.ac.uk')
BEGIN
    INSERT INTO {SCHEMA}.Profile (Email, Username, AboutMe, Location, Dob, Language, Password, Role)
    VALUES ('grace@plymouth.ac.uk', 'Grace Hopper', NULL, NULL, NULL, NULL, '***', 'Admin');
END;

IF NOT EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = 'tim@plymouth.ac.uk')
BEGIN
    INSERT INTO {SCHEMA}.Profile (Email, Username, AboutMe, Location, Dob, Language, Password, Role)
    VALUES ('tim@plymouth.ac.uk', 'Tim Berners-Lee', NULL, NULL, NULL, NULL, '***', 'User');
END;

IF NOT EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = 'ada@plymouth.ac.uk')
BEGIN
    INSERT INTO {SCHEMA}.Profile (Email, Username, AboutMe, Location, Dob, Language, Password, Role)
    VALUES ('ada@plymouth.ac.uk', 'Ada Lovelace', NULL, NULL, NULL, NULL, '***', 'User');
END;
"""



def main():
    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = True
        cur = conn.cursor()

        # Run main DDL (tables etc.)
        cur.execute(CREATE_SQL)

        # Trigger (separate execute)
        cur.execute(TRIGGER_SQL)

        # View
        cur.execute(VIEW_SQL)

        # Stored procedure
        cur.execute(PROC_SQL)
        
        # Seed data
        cur.execute(SEED_SQL)


        print("✅ CW2 schema + tables + trigger + view + stored procedure created/verified.")

if __name__ == "__main__":
    main()
