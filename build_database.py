# Responsible for creating and verifying all CW2 database objects at runtime.
# This script is executed automatically when the Docker container starts.

import os
import pyodbc
from werkzeug.security import generate_password_hash

# --- Database connection configuration ---
# Credentials are provided via environment variables (baked into the Docker image
# for CW2 constraints). No credentials are committed to version control.
SERVER = "dist-6-505.uopnet.plymouth.ac.uk"
DATABASE = "COMP2001_ADangal"
USERNAME = "ADangal"
PASSWORD = os.getenv("DB_PASSWORD")
DRIVER = "{ODBC Driver 18 for SQL Server}"
SCHEMA = "CW2"

if not PASSWORD:
    raise RuntimeError("DB_PASSWORD environment variable is not set")

# ODBC connection string for direct SQL execution.
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

# --- Core schema and table creation ---
# All objects are created only if they do not already exist,
# allowing the container to be restarted safely.
CREATE_SQL = f"""
-- Create schema if missing
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{SCHEMA}')
BEGIN
    EXEC('CREATE SCHEMA {SCHEMA}');
END;

-- PROFILE
-- Password column stores secure hashes only; plaintext passwords are never persisted.
IF OBJECT_ID('{SCHEMA}.Profile', 'U') IS NULL
BEGIN
    CREATE TABLE {SCHEMA}.Profile (
        Email       VARCHAR(30)  NOT NULL,
        Username    VARCHAR(30)  NOT NULL,
        AboutMe     VARCHAR(MAX) NULL,
        Location    VARCHAR(50)  NULL,
        Dob         DATE         NULL,
        Language    VARCHAR(30)  NULL,
        Password    VARCHAR(255) NOT NULL,
        Role        VARCHAR(5)   NOT NULL CONSTRAINT DF_Profile_Role DEFAULT 'User',
        CONSTRAINT PK_Profile PRIMARY KEY (Email),
        CONSTRAINT CK_Profile_Role CHECK (Role IN ('Admin', 'User'))
    );
END;

-- ACTIVITY
IF OBJECT_ID('{SCHEMA}.Activity', 'U') IS NULL
BEGIN
    CREATE TABLE {SCHEMA}.Activity (
        Activity_id TINYINT IDENTITY(1,1) NOT NULL,
        Activity    VARCHAR(30) NOT NULL,
        CONSTRAINT PK_Activity PRIMARY KEY (Activity_id),
        CONSTRAINT UQ_Activity_Activity UNIQUE (Activity)
    );
END;

-- FAVOURITE ACTIVITY
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

-- PROFILE AUDIT
-- Used to demonstrate triggers and data auditing for CW2.
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

-- Drop trigger and stored procedures if they already exist to allow re-creation
IF OBJECT_ID('{SCHEMA}.trg_Profile_Audit_Insert', 'TR') IS NOT NULL
    DROP TRIGGER {SCHEMA}.trg_Profile_Audit_Insert;

IF OBJECT_ID('{SCHEMA}.usp_Profile_Create', 'P') IS NOT NULL DROP PROCEDURE {SCHEMA}.usp_Profile_Create;
IF OBJECT_ID('{SCHEMA}.usp_Profile_ReadAll', 'P') IS NOT NULL DROP PROCEDURE {SCHEMA}.usp_Profile_ReadAll;
IF OBJECT_ID('{SCHEMA}.usp_Profile_ReadByEmail', 'P') IS NOT NULL DROP PROCEDURE {SCHEMA}.usp_Profile_ReadByEmail;
IF OBJECT_ID('{SCHEMA}.usp_Profile_Update', 'P') IS NOT NULL DROP PROCEDURE {SCHEMA}.usp_Profile_Update;
IF OBJECT_ID('{SCHEMA}.usp_Profile_Delete', 'P') IS NOT NULL DROP PROCEDURE {SCHEMA}.usp_Profile_Delete;
"""

# --- Trigger for auditing profile creation ---
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

# --- View for reporting / inspection ---
# Provides a denormalised, read-optimised view of profiles and their favourites.
# Intended for reporting and evidence, not direct API usage.
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

# --- Profile CRUD stored procedures ---
# All CRUD operations in Profile
# are performed via stored procedures.
PROC_SQL = f"""
-- CREATE
EXEC('
CREATE PROCEDURE {SCHEMA}.usp_Profile_Create
    @Email      VARCHAR(30),
    @Username   VARCHAR(30),
    @AboutMe    VARCHAR(MAX) = NULL,
    @Location   VARCHAR(50)  = NULL,
    @Dob        DATE         = NULL,
    @Language   VARCHAR(30)  = NULL,
    @Password   VARCHAR(255),
    @Role       VARCHAR(5)   = ''User''
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = @Email)
    BEGIN
        RAISERROR(''Profile already exists'', 16, 1);
        RETURN;
    END

    INSERT INTO {SCHEMA}.Profile (Email, Username, AboutMe, Location, Dob, Language, Password, Role)
    VALUES (@Email, @Username, @AboutMe, @Location, @Dob, @Language, @Password, @Role);

    SELECT ''CREATED'' AS result;
END
');

-- READ ALL
EXEC('
CREATE PROCEDURE {SCHEMA}.usp_Profile_ReadAll
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        Email,
        Username,
        AboutMe,
        Location,
        Dob,
        Language,
        Role
    FROM {SCHEMA}.Profile
    ORDER BY Email;
END
');

-- READ BY EMAIL
EXEC('
CREATE PROCEDURE {SCHEMA}.usp_Profile_ReadByEmail
    @Email VARCHAR(30)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        Email,
        Username,
        AboutMe,
        Location,
        Dob,
        Language,
        Role
    FROM {SCHEMA}.Profile
    WHERE Email = @Email;
END
');

-- UPDATE
EXEC('
CREATE PROCEDURE {SCHEMA}.usp_Profile_Update
    @Email      VARCHAR(30),
    @Username   VARCHAR(30)  = NULL,
    @AboutMe    VARCHAR(MAX) = NULL,
    @Location   VARCHAR(50)  = NULL,
    @Dob        DATE         = NULL,
    @Language   VARCHAR(30)  = NULL,
    @Password   VARCHAR(255) = NULL,
    @Role       VARCHAR(5)   = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = @Email)
    BEGIN
        RAISERROR(''Profile not found'', 16, 1);
        RETURN;
    END

    UPDATE {SCHEMA}.Profile
    SET
        Username = COALESCE(@Username, Username),
        AboutMe  = COALESCE(@AboutMe, AboutMe),
        Location = COALESCE(@Location, Location),
        Dob      = COALESCE(@Dob, Dob),
        Language = COALESCE(@Language, Language),
        Password = COALESCE(@Password, Password),
        Role     = COALESCE(@Role, Role)
    WHERE Email = @Email;

    SELECT ''UPDATED'' AS result;
END
');

-- DELETE
EXEC('
CREATE PROCEDURE {SCHEMA}.usp_Profile_Delete
    @Email VARCHAR(30)
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (SELECT 1 FROM {SCHEMA}.Profile WHERE Email = @Email)
    BEGIN
        RAISERROR(''Profile not found'', 16, 1);
        RETURN;
    END

    DELETE FROM {SCHEMA}.Profile
    WHERE Email = @Email;

    SELECT ''DELETED'' AS result;
END
');
"""

# --- Seed data helpers ---
# These functions populate baseline data for testing and demonstration.
# All inserts are safe to run multiple times.

def seed_profiles(cur):
    # Seed required user accounts with hashed passwords.
    seeds = [
        ("grace@plymouth.ac.uk", "Grace Hopper", "ISAD123!", "Admin"),
        ("tim@plymouth.ac.uk", "Tim Berners-Lee", "COMP2001!", "User"),
        ("ada@plymouth.ac.uk", "Ada Lovelace", "insecurePassword", "User"),
    ]

    for email, username, plain_password, role in seeds:
        exists = cur.execute(
            f"SELECT 1 FROM {SCHEMA}.Profile WHERE Email = ?", (email,)
        ).fetchone()

        if not exists:
            pwd_hash = generate_password_hash(plain_password)
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.Profile
                    (Email, Username, AboutMe, Location, Dob, Language, Password, Role)
                VALUES (?, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (email, username, pwd_hash, role),
            )


def seed_activities(cur):
    # Baseline activities for preference selection.
    activities = [
        "Running",
        "Swimming",
        "Cycling",
        "Hiking",
        "Walking",
    ]

    for name in activities:
        exists = cur.execute(
            f"SELECT 1 FROM {SCHEMA}.Activity WHERE Activity = ?", (name,)
        ).fetchone()

        if not exists:
            cur.execute(
                f"INSERT INTO {SCHEMA}.Activity (Activity) VALUES (?)",
                (name,),
            )


def seed_favourites(cur):
    # Pre-populate favourite activities for demonstration accounts.
    favourites_by_email = {
        "grace@plymouth.ac.uk": ["Running", "Cycling"],
        "tim@plymouth.ac.uk": ["Swimming", "Walking"],
        "ada@plymouth.ac.uk": ["Hiking", "Running"],
    }

    # Build Activity name -> id lookup once to avoid repeated queries
    rows = cur.execute(
        f"SELECT Activity_id, Activity FROM {SCHEMA}.Activity"
    ).fetchall()
    activity_id_by_name = {r.Activity: r.Activity_id for r in rows}

    for email, fav_names in favourites_by_email.items():
        prof_exists = cur.execute(
            f"SELECT 1 FROM {SCHEMA}.Profile WHERE Email = ?", (email,)
        ).fetchone()
        if not prof_exists:
            continue

        for act_name in fav_names:
            act_id = activity_id_by_name.get(act_name)
            if act_id is None:
                continue

            exists = cur.execute(
                f"""
                SELECT 1
                FROM {SCHEMA}.FavouriteActivity
                WHERE Email = ? AND Activity_id = ?
                """,
                (email, act_id),
            ).fetchone()

            if not exists:
                cur.execute(
                    f"""
                    INSERT INTO {SCHEMA}.FavouriteActivity (Email, Activity_id)
                    VALUES (?, ?)
                    """,
                    (email, act_id),
                )


def main():
    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = True
        cur = conn.cursor()

        # Core schema and tables
        cur.execute(CREATE_SQL)

        # Trigger, view, and stored procedures
        cur.execute(TRIGGER_SQL)
        cur.execute(VIEW_SQL)
        cur.execute(PROC_SQL)

        # Seed baseline data
        seed_profiles(cur)
        seed_activities(cur)
        seed_favourites(cur)

        print("CW2 schema + tables + trigger + view + Profile CRUD stored procedures created/verified.")


if __name__ == "__main__":
    main()