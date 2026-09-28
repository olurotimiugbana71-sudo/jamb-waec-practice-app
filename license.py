"""
license.py
----------
Signed license keys with no database required. A key is derived from the
buyer's email plus a private secret (LICENSE_SECRET) that only you know -
the app can verify a key is genuine just by recalculating it, so there's
nothing to host or keep in sync.

IMPORTANT: LICENSE_SECRET must never be committed to GitHub or shared
anywhere. It lives only in your local .env and in Streamlit Cloud's
Secrets. Anyone who obtains it could generate fake valid keys.
"""

import hmac
import hashlib


def _normalize_email(email):
    return email.strip().lower()


def generate_license_key(email, secret):
    """Generate the one true license key for a given buyer email."""
    email = _normalize_email(email)
    signature = hmac.new(secret.encode(), email.encode(), hashlib.sha256).hexdigest().upper()
    short = signature[:16]
    groups = [short[i:i + 4] for i in range(0, 16, 4)]
    return "APEX-" + "-".join(groups)


def verify_license_key(email, key, secret):
    """Returns True only if `key` is the genuine key for `email`."""
    if not email or not key or not secret:
        return False
    expected = generate_license_key(email, secret)
    return hmac.compare_digest(expected, key.strip().upper())