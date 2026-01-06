import os
import requests

AUTH_URL = os.getenv(
    "AUTH_API_URL",
    "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users",
)

def verify_email_password(email: str, password: str) -> bool:
    r = requests.post(AUTH_URL, json={"Email": email, "Password": password}, timeout=8)
    r.raise_for_status()
    data = r.json()

    # Expect: ["Verified", "True"] or ["Verified", "False"]
    return isinstance(data, list) and len(data) >= 2 and str(data[1]).lower() == "true"
