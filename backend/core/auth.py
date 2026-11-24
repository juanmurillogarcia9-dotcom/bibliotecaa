import base64
import hashlib
import hmac
import json
import time

SESSION_COOKIE = "biblioteca_session"
SESSION_MAX_AGE = 12 * 60 * 60


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_session_token(email: str, secret: str, now: int | None = None) -> str:
    current_time = int(time.time()) if now is None else now
    payload = json.dumps(
        {"sub": email, "exp": current_time + SESSION_MAX_AGE},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = _encode(payload)
    signature = hmac.new(
        secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def verify_session_token(
    token: str | None, secret: str, expected_email: str, now: int | None = None
) -> bool:
    if not token:
        return False
    current_time = int(time.time()) if now is None else now
    try:
        encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        signature = _decode(encoded_signature)
        expected_signature = hmac.new(
            secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(signature, expected_signature):
            return False
        payload = json.loads(_decode(encoded_payload))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    return (
        isinstance(payload, dict)
        and payload.get("sub", "").casefold() == expected_email.casefold()
        and type(payload.get("exp")) is int
        and payload["exp"] > current_time
    )
