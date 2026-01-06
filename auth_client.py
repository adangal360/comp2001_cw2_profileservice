import os
import requests

# Base URL for the external Authenticator service provided for COMP2001.
AUTH_URL = os.getenv(
    "AUTH_API_URL",
    "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users",
)


def verify_email_password(email: str, password: str) -> bool:
    """
    Verify user credentials against the external Authenticator API.

    Returns True if the credentials are valid, False otherwise.
    Any network or protocol errors are raised to the caller so they can be
    translated into appropriate HTTP responses at the API layer.
    """

    # Credentials are sent as JSON in a POST request.
    r = requests.post(
        AUTH_URL,
        json={"Email": email, "Password": password},
        timeout=8
    )

    r.raise_for_status()
    data = r.json()

    # Expected response format from the Authenticator API:
    # ["Verified", "True"] or ["Verified", "False"]
    # We defensively validate the structure before interpreting the result.
    return (
        isinstance(data, list)
        and len(data) >= 2
        and str(data[1]).lower() == "true"
    )