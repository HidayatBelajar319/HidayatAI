from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_pairing_token() -> str:
    return secrets.token_urlsafe(32)


def generate_device_secret() -> str:
    return secrets.token_urlsafe(48)


def generate_device_id(platform: str, name: str) -> str:
    prefix = "".join(ch for ch in (platform or "device").lower() if ch.isalnum())[:8] or "device"
    suffix = secrets.token_hex(3)
    return f"{prefix}_{suffix}"


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
