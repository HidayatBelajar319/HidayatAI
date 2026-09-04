from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


class ProtocolTypes:
    HELLO = "hello"
    PAIR_REQUEST = "pair_request"
    PAIR_APPROVED = "pair_approved"
    AUTHENTICATE = "authenticate"
    DEVICE_ONLINE = "device_online"
    DEVICE_OFFLINE = "device_offline"
    CAPABILITIES = "capabilities"
    EXECUTE = "execute"
    RESULT = "result"
    EVENT = "event"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    FILE_TRANSFER = "file_transfer"
    SCREEN_CAPTURE = "screen_capture"
    CHAT_MESSAGE = "chat_message"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_request_id() -> str:
    return uuid4().hex


def build_message(message_type: str, payload: dict | None = None, request_id: str | None = None, timestamp: str | None = None) -> dict:
    return {
        "type": message_type,
        "request_id": request_id or new_request_id(),
        "timestamp": timestamp or now_iso(),
        "payload": payload or {},
    }


def validate_message(message: dict) -> tuple[bool, str]:
    if not isinstance(message, dict):
        return False, "Message must be a JSON object."
    for key in ("type", "request_id", "timestamp"):
        if not str(message.get(key, "")).strip():
            return False, f"Missing required field: {key}"
    return True, ""
