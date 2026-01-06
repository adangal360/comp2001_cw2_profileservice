from flask import request, abort

from auth_client import verify_email_password
from models import Profile


def require_verified_email(target_email: str) -> None:
    email = request.headers.get("X-Auth-Email")
    password = request.headers.get("X-Auth-Password")

    if not email or not password:
        abort(401, "Missing credentials. Send X-Auth-Email and X-Auth-Password headers.")
    if email != target_email:
        abort(403, "You can only perform this action for your own email")

    try:
        if not verify_email_password(email, password):
            abort(401, "Invalid credentials")
    except Exception as e:
        abort(502, f"Authenticator API error: {str(e)}")



def _get_credentials():
    email = request.headers.get("X-Auth-Email")
    password = request.headers.get("X-Auth-Password")

    if not email or not password:
        abort(401, "Missing credentials. Send X-Auth-Email and X-Auth-Password headers.")
    return email, password


def require_auth() -> Profile:
    email, password = _get_credentials()

    try:
        ok = verify_email_password(email, password)
    except Exception as e:
        abort(502, f"Authenticator API error: {str(e)}")

    if not ok:
        abort(401, "Invalid credentials")

    actor = Profile.query.get(email)
    if actor is None:
        abort(403, "Authenticated user has no local Profile in CW2.Profile (Trail App roles).")

    return actor


def require_admin() -> Profile:
    actor = require_auth()
    if actor.Role != "Admin":
        abort(403, "Admin role required")
    return actor


def require_self_or_admin(target_email: str) -> Profile:
    actor = require_auth()
    if actor.Role != "Admin" and actor.Email != target_email:
        abort(403, "Forbidden: only Admin or the same user can perform this action")
    return actor
