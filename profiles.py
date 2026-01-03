from flask import abort, make_response
from config import db
from models import Profile, profile_schema, profiles_schema

def read_all():
    profiles = Profile.query.all()
    return profiles_schema.dump(profiles)

def read_one(email):
    profile = Profile.query.get(email)
    if profile is None:
        abort(404, f"Profile with Email '{email}' not found")
    return profile_schema.dump(profile)

def create(profile):
    email = profile.get("Email")
    if not email:
        abort(400, "Email is required")

    existing = Profile.query.get(email)
    if existing is not None:
        abort(409, f"Profile with Email '{email}' already exists")

    new_profile = profile_schema.load(profile, session=db.session)
    db.session.add(new_profile)
    db.session.commit()
    return profile_schema.dump(new_profile), 201

def update(email, profile):
    existing = Profile.query.get(email)
    if existing is None:
        abort(404, f"Profile with Email '{email}' not found")

    if "Email" in profile and profile["Email"] != email:
        abort(400, "Email cannot be changed")

    for field in ["Username", "AboutMe", "Location", "Dob", "Language", "Password", "Role"]:
        if field in profile:
            setattr(existing, field, profile[field])

    db.session.commit()
    return profile_schema.dump(existing), 200

def delete(email):
    existing = Profile.query.get(email)
    if existing is None:
        abort(404, f"Profile with Email '{email}' not found")

    db.session.delete(existing)
    db.session.commit()
    return make_response(f"Profile '{email}' deleted", 200)