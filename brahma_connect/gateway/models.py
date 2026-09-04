from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class PairingOffer:
    service: str
    host: str
    port: int
    pairing_token: str
    pairing_code: str
    expires_at: float
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "host": self.host,
            "port": self.port,
            "pairing_token": self.pairing_token,
            "pairing_code": self.pairing_code,
            "expires": int(max(0, self.expires_at - datetime.now(timezone.utc).timestamp())),
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class DeviceRecord:
    device_id: str
    name: str
    platform: str
    os_version: str = ""
    agent_version: str = ""
    ip: str = ""
    online: bool = False
    last_seen: str = ""
    battery: int | None = None
    capabilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    paired_at: str = ""
    secret_hash: str = ""
    revoked: bool = False
    connection_id: str = ""
    identity_fingerprint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "platform": self.platform,
            "os_version": self.os_version,
            "agent_version": self.agent_version,
            "ip": self.ip,
            "online": self.online,
            "last_seen": self.last_seen,
            "battery": self.battery,
            "capabilities": list(self.capabilities),
            "permissions": list(self.permissions),
            "paired_at": self.paired_at,
            "secret_hash": self.secret_hash,
            "revoked": self.revoked,
            "connection_id": self.connection_id,
            "identity_fingerprint": self.identity_fingerprint,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceRecord":
        return cls(
            device_id=str(data.get("device_id", "")),
            name=str(data.get("name", "Unknown Device")),
            platform=str(data.get("platform", "unknown")),
            os_version=str(data.get("os_version", "")),
            agent_version=str(data.get("agent_version", "")),
            ip=str(data.get("ip", "")),
            online=bool(data.get("online", False)),
            last_seen=str(data.get("last_seen", "")),
            battery=data.get("battery"),
            capabilities=list(data.get("capabilities") or []),
            permissions=list(data.get("permissions") or []),
            paired_at=str(data.get("paired_at", "")),
            secret_hash=str(data.get("secret_hash", "")),
            revoked=bool(data.get("revoked", False)),
            connection_id=str(data.get("connection_id", "")),
            identity_fingerprint=str(data.get("identity_fingerprint", "")),
            metadata=dict(data.get("metadata") or {}),
        )
