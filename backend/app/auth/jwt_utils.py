from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.config import SecurityConfig


class JWTError(ValueError):
    pass


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign(message: bytes, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def encode_token(payload: dict[str, object], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signed = f"{header_part}.{payload_part}".encode("ascii")
    signature = _sign(signed, secret)
    return f"{header_part}.{payload_part}.{signature}"


def decode_token(token: str, secret: str) -> dict[str, object]:
    parts = token.split(".")
    if len(parts) != 3:
        raise JWTError("Malformed token")

    header_part, payload_part, signature = parts
    signed = f"{header_part}.{payload_part}".encode("ascii")
    expected = _sign(signed, secret)
    if not hmac.compare_digest(expected, signature):
        raise JWTError("Invalid token signature")

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception as exc:
        raise JWTError("Invalid token payload") from exc

    exp = payload.get("exp")
    if isinstance(exp, (int, float)):
        if datetime.now(timezone.utc).timestamp() > exp:
            raise JWTError("Token expired")

    return payload


def build_access_token_payload(user_id: str, username: str, roles: list[str], cfg: SecurityConfig) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "type": "access",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=cfg.access_token_ttl_seconds)).timestamp()),
    }


def build_refresh_token_payload(user_id: str, cfg: SecurityConfig) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=cfg.refresh_token_ttl_seconds)).timestamp()),
    }


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
