from flask import abort
from auth_client import verify_email_password

def verify(credentials):
    email = credentials.get("Email")
    password = credentials.get("Password")
    if not email or not password:
        abort(400, "Email and Password are required")

    try:
        return {"verified": verify_email_password(email, password)}, 200
    except Exception as e:
        abort(502, f"Authenticator error: {str(e)}")
