from flask import abort, make_response
from sqlalchemy import text

from config import db
from models import profile_schema, profiles_schema
from werkzeug.security import generate_password_hash

from authz import require_admin, require_self_or_admin


# -----------------------------
# READ OPERATIONS
# -----------------------------

def read_all():
    """
    Return all profiles in the system.

    This endpoint is Admin-only and uses a stored procedure
    to satisfy CW2 requirements for the main assessed resource.
    """
    require_admin()
    try:
        rows = db.session.execute(
            text("EXEC CW2.usp_Profile_ReadAll")
        ).mappings().all()

        return profiles_schema.dump(rows)

    except Exception as e:
        abort(500, f"Stored procedure failed: {str(e)}")


def read_one(email):
    """
    Return a single profile by email.

    Access is restricted to:
    - the profile owner, or
    - an Admin user
    """
    require_self_or_admin(email)

    try:
        row = db.session.execute(
            text("EXEC CW2.usp_Profile_ReadByEmail @Email=:Email"),
            {"Email": email},
        ).mappings().first()

        if row is None:
            abort(404, f"Profile with Email '{email}' not found")

        return profile_schema.dump(row)

    except Exception as e:
        abort(500, f"Stored procedure failed: {str(e)}")


# -----------------------------
# CREATE (ONBOARDING)
# -----------------------------

def create(profile):
    """
    Create a new profile (onboarding endpoint).

    This endpoint is intentionally unauthenticated to allow
    first-time user creation, as specified in CW2 ground truth.
    """
    email = profile.get("Email")
    if not email:
        abort(400, "Email is required")

    username = profile.get("Username")
    if not username:
        abort(400, "Username is required")

    # Optional profile fields
    about_me = profile.get("AboutMe")
    location = profile.get("Location")
    dob = profile.get("Dob")          # 'YYYY-MM-DD' or None
    language = profile.get("Language")

    # Password must be supplied and is hashed before storage
    raw_password = profile.get("Password")
    if not raw_password:
        abort(400, "Password is required")

    password = generate_password_hash(raw_password)

    # Prevent role escalation during self-signup
    role = "User"

    try:
        db.session.execute(
            text("""
                EXEC CW2.usp_Profile_Create
                    @Email=:Email,
                    @Username=:Username,
                    @AboutMe=:AboutMe,
                    @Location=:Location,
                    @Dob=:Dob,
                    @Language=:Language,
                    @Password=:Password,
                    @Role=:Role
            """),
            {
                "Email": email,
                "Username": username,
                "AboutMe": about_me,
                "Location": location,
                "Dob": dob,
                "Language": language,
                "Password": password,
                "Role": role,
            },
        )
        db.session.commit()

        # Fetch the created profile via READ procedure
        # (ensures Password is never returned)
        row = db.session.execute(
            text("EXEC CW2.usp_Profile_ReadByEmail @Email=:Email"),
            {"Email": email},
        ).mappings().first()

        return profile_schema.dump(row), 201

    except Exception as e:
        db.session.rollback()
        msg = str(e)

        if "Profile already exists" in msg:
            abort(409, f"Profile with Email '{email}' already exists")

        abort(500, f"Stored procedure failed: {msg}")


# -----------------------------
# UPDATE
# -----------------------------

def update(email, profile):
    """
    Update an existing profile.

    Users may update their own profile data.
    Only Admin users are permitted to change roles.
    """
    actor = require_self_or_admin(email)

    # Email is immutable once created
    if "Email" in profile and profile["Email"] != email:
        abort(400, "Email cannot be changed")

    # Enforce admin-only role changes (prevents self role escalation)
    role = profile.get("Role")
    if role != actor.Role and actor.Role != "Admin":
        abort(403, "Only Admin can change role")

    # Hash password if a new one is provided
    raw_password = profile.get("Password")
    hashed_password = generate_password_hash(raw_password) if raw_password else None

    # Only supplied fields are updated; others are preserved via COALESCE in SQL
    params = {
        "Email": email,
        "Username": profile.get("Username"),
        "AboutMe": profile.get("AboutMe"),
        "Location": profile.get("Location"),
        "Dob": profile.get("Dob"),
        "Language": profile.get("Language"),
        "Password": hashed_password,
        "Role": role,
    }

    try:
        db.session.execute(
            text("""
                EXEC CW2.usp_Profile_Update
                    @Email=:Email,
                    @Username=:Username,
                    @AboutMe=:AboutMe,
                    @Location=:Location,
                    @Dob=:Dob,
                    @Language=:Language,
                    @Password=:Password,
                    @Role=:Role
            """),
            params,
        )
        db.session.commit()

        # Return the updated profile using the READ procedure
        row = db.session.execute(
            text("EXEC CW2.usp_Profile_ReadByEmail @Email=:Email"),
            {"Email": email},
        ).mappings().first()

        if row is None:
            abort(404, f"Profile with Email '{email}' not found")

        return profile_schema.dump(row), 200

    except Exception as e:
        db.session.rollback()
        msg = str(e)

        if "Profile not found" in msg:
            abort(404, f"Profile with Email '{email}' not found")

        abort(500, f"Stored procedure failed: {msg}")


# -----------------------------
# DELETE
# -----------------------------

def delete(email):
    """
    Delete a profile.

    Access is restricted to:
    - the profile owner, or
    - an Admin user
    """
    require_self_or_admin(email)

    try:
        db.session.execute(
            text("EXEC CW2.usp_Profile_Delete @Email=:Email"),
            {"Email": email},
        )
        db.session.commit()

        return make_response(f"Profile '{email}' deleted", 200)

    except Exception as e:
        db.session.rollback()
        msg = str(e)

        if "Profile not found" in msg:
            abort(404, f"Profile with Email '{email}' not found")

        abort(500, f"Stored procedure failed: {msg}")