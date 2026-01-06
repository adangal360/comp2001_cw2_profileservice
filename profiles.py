from flask import abort, make_response
from sqlalchemy import text

from config import db
from models import Profile, profile_schema, profiles_schema

from authz import require_admin, require_self_or_admin, require_verified_email


def read_all():
    require_admin()
    profiles = Profile.query.all()
    return profiles_schema.dump(profiles)


def read_one(email):
    require_self_or_admin(email)
    profile = Profile.query.get(email)
    if profile is None:
        abort(404, f"Profile with Email '{email}' not found")
    return profile_schema.dump(profile)


def create(profile):
    email = profile.get("Email")
    if not email:
        abort(400, "Email is required")

    username = profile.get("Username")
    if not username:
        abort(400, "Username is required")

    require_verified_email(email)

    existing = Profile.query.get(email)
    if existing is not None:
        abort(409, f"Profile with Email '{email}' already exists")

    # Never store real passwords (auth is external)
    profile["Password"] = "***"

    # Prevent role escalation on self-signup
    profile["Role"] = "User"

    new_profile = profile_schema.load(profile, session=db.session)
    db.session.add(new_profile)
    db.session.commit()
    return profile_schema.dump(new_profile), 201



def upsert(profile):
    """
    Demonstrates the CW2 stored procedure (CW2.usp_UpsertProfile).
    If the Email already exists it updates; otherwise it inserts.
    """
    require_admin()
    # Basic validation (matches required fields in ProfileCreate)
    email = profile.get("Email")
    username = profile.get("Username")
    password = "***"

    if not email or not username:
        abort(400, "Email and Username are required")

    # Optional fields (procedure has defaults for some)
    about_me = profile.get("AboutMe")
    location = profile.get("Location")
    dob = profile.get("Dob")          # expects 'YYYY-MM-DD' or None
    language = profile.get("Language")
    role = profile.get("Role", "User")

    try:
        result = db.session.execute(
            text("""
                EXEC CW2.usp_UpsertProfile
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
        ).mappings().first()

        db.session.commit()

        outcome = (result.get("result") if result else None)
        status_code = 201 if outcome == "CREATED" else 200

        # Return the up-to-date row using ORM (keeps output consistent)
        saved = Profile.query.get(email)
        return profile_schema.dump(saved), status_code

    except Exception as e:
        db.session.rollback()
        abort(500, f"Stored procedure failed: {str(e)}")


def update(email, profile):
    require_self_or_admin(email)
    existing = Profile.query.get(email)
    if existing is None:
        abort(404, f"Profile with Email '{email}' not found")

    if "Email" in profile and profile["Email"] != email:
        abort(400, "Email cannot be changed")

    for field in ["Username", "AboutMe", "Location", "Dob", "Language", "Role"]:
        if field in profile:
            setattr(existing, field, profile[field])

    db.session.commit()
    return profile_schema.dump(existing), 200


def delete(email):
    require_self_or_admin(email)
    existing = Profile.query.get(email)
    if existing is None:
        abort(404, f"Profile with Email '{email}' not found")

    db.session.delete(existing)
    db.session.commit()
    return make_response(f"Profile '{email}' deleted", 200)
