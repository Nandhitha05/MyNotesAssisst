import os
import hmac
import time
import json
import base64
import hashlib


def _secret() -> bytes:
    return os.getenv("APP_SECRET", "change-this-secret").encode()


def verify_credentials(username: str, password: str) -> bool:
    expected_user = os.getenv("APP_USERNAME", "admin")
    expected_pass = os.getenv("APP_PASSWORD", "admin123")
    return hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_pass)


def create_token(username: str) -> str:
    payload = json.dumps({"u": username, "t": int(time.time())}).encode()
    sig = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=") + "." + sig


def verify_token(token: str):
    try:
        payload_b64, sig = token.split(".", 1)
        # restore padding
        pad = "=" * (-len(payload_b64) % 4)
        payload = base64.urlsafe_b64decode(payload_b64 + pad)
        expected = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(payload)
        # 24h expiry
        if int(time.time()) - int(data.get("t", 0)) > 60 * 60 * 24:
            return None
        return data
    except Exception:
        return None
