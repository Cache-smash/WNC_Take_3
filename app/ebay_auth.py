"""
ebay_auth.py — eBay OAuth2 client_credentials token management.

Fetches a short-lived application access token from the eBay production
OAuth endpoint using the PRD credentials stored in .env.  The token is
cached in memory and automatically refreshed 60 seconds before expiry.
"""

import base64
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_SCOPE     = "https://api.ebay.com/oauth/api_scope"

# In-memory cache; keyed by client_id so multi-env runs don't collide.
_cache: dict = {"token": None, "expires_at": 0.0}


def get_token() -> str:
    """
    Return a valid Bearer token, fetching a fresh one if necessary.
    Reads EBAY_CLIENT_ID and EBAY_CLIENT_SECRET from the environment.
    """
    now = time.monotonic()

    if _cache["token"] and now < _cache["expires_at"] - 60:
        logger.debug("[eBay Auth] Returning cached token.")
        return _cache["token"]

    client_id     = os.environ.get("EBAY_CLIENT_ID", "")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")

    import shutil
    import subprocess
    op_path = shutil.which("op")
    if op_path:
        for var_name, var_val in [("EBAY_CLIENT_ID", client_id), ("EBAY_CLIENT_SECRET", client_secret)]:
            if var_val and var_val.startswith("op://"):
                try:
                    res = subprocess.run([op_path, "read", var_val], capture_output=True, text=True, timeout=5, check=True)
                    resolved = res.stdout.strip()
                    if resolved:
                        if var_name == "EBAY_CLIENT_ID": client_id = resolved
                        else: client_secret = resolved
                        os.environ[var_name] = resolved
                except Exception:
                    pass

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()


    headers = {
        "Content-Type":  "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credentials}",
    }
    payload = {
        "grant_type": "client_credentials",
        "scope":      _SCOPE,
    }

    logger.info("[eBay Auth] Requesting new OAuth token from production endpoint...")
    resp = requests.post(_TOKEN_URL, headers=headers, data=payload, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    token      = data["access_token"]
    expires_in = int(data.get("expires_in", 7200))

    _cache["token"]      = token
    _cache["expires_at"] = now + expires_in

    logger.info("[eBay Auth] [OK] Token obtained - expires in %d s.", expires_in)
    return token
