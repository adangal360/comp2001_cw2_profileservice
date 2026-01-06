from flask import request, abort

from auth_client import verify_email_password
from models import Profile

# Helper used in limited scenarios where we want to confirm that the caller
# is both authenticated AND acting strictly on their own email address.
def require_verified_email(target_email: str) -> None:
    # Credentials are passed via custom headers rather than request body
    # to keep authentication concerns separate from payload data.
    email = request.headers.get("X-Auth-Email")
    password = request.headers.get("X-Auth-Password")

    if not email or not password:
        abort(401, "Missing credentials. Send X-Auth-Email and X-Auth-Password headers.")

    # Enforce self-only access (no admin override here by design)
    if email != target_email:
        abort(403, "You can only perform this action for your own email")

    try:
        if not verify_email_password(email, password):
            abort(401, "Invalid credentials")
    except Exception as e:
        abort(502, f"Authenticator API error: {str(e)}")

def _get_credentials():
    """
    Internal helper to extract authentication headers.
    Kept separate to avoid duplication across auth guards.
    """
    email = request.headers.get("X-Auth-Email")
    password = request.headers.get("X-Auth-Password")

    if not email or not password:
        abort(401, "Missing credentials. Send X-Auth-Email and X-Auth-Password headers.")

    return email, password


def require_auth() -> Profile:
    """
    Authenticate the caller and return their local Profile.
    Authentication is handled externally; authorisation is enforced locally.
    """
    email, password = _get_credentials()

    try:
        ok = verify_email_password(email, password)
    except Exception as e:
        abort(502, f"Authenticator API error: {str(e)}")

    if not ok:
        abort(401, "Invalid credentials")

    # Map authenticated identity to a local Profile record.
    # This allows the Trail App to enforce roles without duplicating auth data.
    actor = Profile.query.get(email)
    if actor is None:
        abort(
            403,
            "Authenticated user has no local Profile in CW2.Profile (Trail App roles)."
        )

    return actor


def require_admin() -> Profile:
    """
    Enforce admin-only access.
    Returns the authenticated Profile for further use if needed.
    """
    actor = require_auth()
    if actor.Role != "Admin":
        abort(403, "Admin role required")

    return actor


def require_self_or_admin(target_email: str) -> Profile:
    """
    Allow access if the caller is either:
    - the same user as the target email, or
    - an Admin user

    This pattern is used across profile and favourites endpoints.
    """
    actor = require_auth()
    if actor.Role != "Admin" and actor.Email != target_email:
        abort(403, "Forbidden: only Admin or the same user can perform this action")

    return actor