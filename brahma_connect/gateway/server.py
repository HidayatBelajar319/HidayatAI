from __future__ import annotations

import asyncio
import json
import socket
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .capability_manager import CapabilityManager
from .command_router import CommandRouter
from .device_manager import DeviceManager
from .discovery import GatewayDiscovery, local_ip
from .models import PairingOffer
from .pairing import PairingManager
from .protocol import ProtocolTypes, build_message, validate_message, now_iso, new_request_id
from .websocket import ConnectionHub


def _default_config_path(base_dir: Path) -> Path:
    return Path(base_dir) / "config" / "brahma_connect.json"


def _default_registry_path(base_dir: Path) -> Path:
    return Path(base_dir) / "config" / "brahma_connect" / "devices.json"


@dataclass(slots=True)
class BrahmaGatewayConfig:
    host: str = "0.0.0.0"
    port: int = 8765
    enabled: bool = True
    advertise: bool = True
    service_name: str = "_BRAHMA._tcp.local."
    pairing_ttl_seconds: int = 300
    request_timeout_seconds: int = 30
    config_path: Path | None = None
    registry_path: Path | None = None

    @classmethod
    def load(cls, base_dir: Path, override: dict[str, Any] | None = None) -> "BrahmaGatewayConfig":
        base_dir = Path(base_dir)
        data: dict[str, Any] = {
            "host": "0.0.0.0",
            "port": 8765,
            "enabled": True,
            "advertise": True,
            "service_name": "_BRAHMA._tcp.local.",
            "pairing_ttl_seconds": 300,
            "request_timeout_seconds": 30,
        }
        config_path = _default_config_path(base_dir)
        if config_path.exists():
            try:
                data.update(json.loads(config_path.read_text(encoding="utf-8")))
            except Exception:
                pass
        if override:
            data.update({k: v for k, v in override.items() if v is not None})
        return cls(
            host=str(data.get("host", "0.0.0.0")),
            port=int(data.get("port", 8765)),
            enabled=bool(data.get("enabled", True)),
            advertise=bool(data.get("advertise", True)),
            service_name=str(data.get("service_name", "_BRAHMA._tcp.local.")),
            pairing_ttl_seconds=int(data.get("pairing_ttl_seconds", 300)),
            request_timeout_seconds=int(data.get("request_timeout_seconds", 30)),
            config_path=config_path,
            registry_path=_default_registry_path(base_dir),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "enabled": self.enabled,
            "advertise": self.advertise,
            "service_name": self.service_name,
            "pairing_ttl_seconds": self.pairing_ttl_seconds,
            "request_timeout_seconds": self.request_timeout_seconds,
        }

    def save(self) -> None:
        if self.config_path is None:
            return
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


class BrahmaGateway:
    def __init__(self, base_dir: Path, config: BrahmaGatewayConfig | None = None):
        self.base_dir = Path(base_dir)
        self.config = config or BrahmaGatewayConfig.load(self.base_dir)
        self.device_manager = DeviceManager(self.config.registry_path or _default_registry_path(self.base_dir))
        self.capability_manager = CapabilityManager()
        self.hub = ConnectionHub()
        self.command_router = CommandRouter(self.device_manager, self.hub, self.capability_manager)
        self.pairing_manager = PairingManager(self.config.service_name, self.config.pairing_ttl_seconds)
        self.discovery = GatewayDiscovery(self.config.service_name)
        self._running = False
        self._shutdown = threading.Event()
        self._server: uvicorn.Server | None = None
        self._log: list[dict[str, Any]] = []
        self._pending_requests: dict[str, dict[str, Any]] = {}
        self.on_chat_message = None
        self.app = self._build_app()

    def is_running(self) -> bool:
        return self._running and not self._shutdown.is_set()

    def request_shutdown(self) -> None:
        self._shutdown.set()
        if self._server is not None:
            self._server.should_exit = True

    def _append_log(self, event_type: str, **payload: Any) -> None:
        entry = {"type": event_type, "timestamp": now_iso(), **payload}
        self._log.append(entry)
        self._log = self._log[-200:]

    def log(self) -> list[dict[str, Any]]:
        return list(self._log)

    def list_devices(self) -> list[dict[str, Any]]:
        return self.device_manager.list_devices()

    def get_device(self, device_or_target: str) -> dict[str, Any] | None:
        query = str(device_or_target or "").strip()
        if not query:
            return None
        record = self.device_manager.get(query)
        if record is None:
            matches = self.device_manager.resolve(query)
            record = matches[0] if len(matches) == 1 else None
        return record.to_dict() if record else None

    def resolve_devices(self, query: str) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.device_manager.resolve(query)]

    def rename_device(self, device_or_target: str, new_name: str) -> dict[str, Any]:
        query = str(device_or_target or "").strip()
        record = self.device_manager.get(query)
        if record is None:
            matches = self.device_manager.resolve(query)
            if len(matches) == 1:
                record = matches[0]
            elif len(matches) > 1:
                return {
                    "success": False,
                    "error": "Multiple devices matched the request.",
                    "error_code": "MULTIPLE_DEVICES",
                    "matches": [item.to_dict() for item in matches],
                }
        if record is None:
            return {"success": False, "error": "Device not found.", "error_code": "DEVICE_NOT_FOUND"}
        renamed = self.device_manager.rename(record.device_id, new_name)
        if renamed is None:
            return {"success": False, "error": "Device not found.", "error_code": "DEVICE_NOT_FOUND"}
        self._append_log("DEVICE_RENAMED", device_id=renamed.device_id, name=renamed.name)
        return {"success": True, "device": renamed.to_dict()}

    def get_capabilities(self, device_or_target: str) -> dict[str, Any]:
        record = self.device_manager.get(str(device_or_target or "").strip())
        if record is None:
            matches = self.device_manager.resolve(device_or_target)
            if len(matches) == 1:
                record = matches[0]
            elif len(matches) > 1:
                return {
                    "success": False,
                    "error": "Multiple devices matched the request.",
                    "error_code": "MULTIPLE_DEVICES",
                    "matches": [item.to_dict() for item in matches],
                }
        if record is None:
            return {"success": False, "error": "Device not found.", "error_code": "DEVICE_NOT_FOUND"}
        return {
            "success": True,
            "device": record.to_dict(),
            "capabilities": list(record.capabilities),
            "permissions": list(record.permissions),
        }

    async def disconnect_device(self, device_or_target: str, *, reason: str = "Disconnected by Brahma") -> dict[str, Any]:
        query = str(device_or_target or "").strip()
        matches = self.device_manager.resolve(query)
        record = None
        if self.device_manager.get(query):
            record = self.device_manager.get(query)
        elif len(matches) == 1:
            record = matches[0]
        elif len(matches) > 1:
            return {
                "success": False,
                "error": "Multiple devices matched the request.",
                "error_code": "MULTIPLE_DEVICES",
                "matches": [item.to_dict() for item in matches],
            }
        if record is None:
            return {"success": False, "error": "Device not found.", "error_code": "DEVICE_NOT_FOUND"}

        disconnected = False
        try:
            disconnected = await self.hub.close_device(record.device_id, reason=reason)
        except Exception:
            disconnected = False
        self.device_manager.mark_offline(record.device_id)
        self._append_log("DEVICE_DISCONNECTED", device_id=record.device_id, name=record.name, forced=disconnected)
        return {"success": True, "device": record.to_dict(), "disconnected": disconnected}

    async def reconnect_device(self, device_or_target: str) -> dict[str, Any]:
        query = str(device_or_target or "").strip()
        matches = self.device_manager.resolve(query)
        record = self.device_manager.get(query)
        if record is None and len(matches) == 1:
            record = matches[0]
        elif record is None and len(matches) > 1:
            return {
                "success": False,
                "error": "Multiple devices matched the request.",
                "error_code": "MULTIPLE_DEVICES",
                "matches": [item.to_dict() for item in matches],
            }
        if record is None:
            return {"success": False, "error": "Device not found.", "error_code": "DEVICE_NOT_FOUND"}
        state = await self.hub.get(record.device_id)
        if state is None:
            return {
                "success": False,
                "device": record.to_dict(),
                "error": f"Your {record.name} is currently offline.",
                "error_code": "DEVICE_OFFLINE",
            }
        self.device_manager.touch(record.device_id)
        self._append_log("DEVICE_RECONNECTED", device_id=record.device_id, name=record.name)
        return {"success": True, "device": record.to_dict(), "reconnected": True}

    def create_pairing_offer(self, *, device_name: str = "Unknown Device", platform: str = "unknown") -> dict[str, Any]:
        advertised_host = local_ip() if self.config.host in {"0.0.0.0", "::"} else self.config.host
        offer = self.pairing_manager.create_offer(advertised_host, self.config.port)
        self._append_log("PAIRING_REQUEST", device=device_name, platform=platform, code=offer.pairing_code)
        return offer.to_dict()

    def list_pending_requests(self) -> list[dict[str, Any]]:
        return [
            {
                "pending_id": pending_id,
                "timestamp": item.get("timestamp", ""),
                "device_name": item.get("device_name", "Unknown Device"),
                "platform": item.get("platform", "unknown"),
                "os_version": item.get("os_version", ""),
                "agent_version": item.get("agent_version", ""),
                "capabilities": list(item.get("capabilities") or []),
                "permissions": list(item.get("permissions") or []),
                "ip": item.get("ip", ""),
            }
            for pending_id, item in self._pending_requests.items()
        ]

    async def approve_pending_request(self, pending_id: str) -> dict[str, Any]:
        item = self._pending_requests.pop(str(pending_id), None)
        if item is None:
            return {"success": False, "error": "Pending request not found."}
        websocket = item.get("websocket")
        if websocket is None:
            return {"success": False, "error": "Device is no longer connected."}

        record, secret = self.device_manager.create_from_pairing(
            name=str(item.get("device_name") or "Unknown Device"),
            platform=str(item.get("platform") or "unknown"),
            os_version=str(item.get("os_version") or ""),
            agent_version=str(item.get("agent_version") or ""),
            ip=str(item.get("ip") or ""),
            battery=item.get("battery"),
            capabilities=list(item.get("capabilities") or []),
            permissions=list(item.get("permissions") or []),
            metadata=dict(item.get("metadata") or {}),
        )
        self._append_log("PAIR_APPROVED", device=record.device_id, name=record.name, platform=record.platform)
        await websocket.send_json(
            build_message(
                ProtocolTypes.PAIR_APPROVED,
                {"device": record.to_dict(), "device_secret": secret},
                request_id=str(item.get("request_id") or ""),
            )
        )
        return {"success": True, "device": record.to_dict(), "device_secret": secret}

    def reject_pending_request(self, pending_id: str) -> bool:
        item = self._pending_requests.pop(str(pending_id), None)
        if item is None:
            return False
        websocket = item.get("websocket")
        if websocket is not None:
            try:
                asyncio.create_task(
                    websocket.send_json(
                        build_message(
                            ProtocolTypes.ERROR,
                            {"error": "Pairing request rejected by user."},
                            request_id=str(item.get("request_id") or ""),
                        )
                    )
                )
            except Exception:
                pass
        self._append_log("PAIR_REJECTED", pending_id=pending_id)
        return True

    async def route_command(self, target: str, action: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.command_router.route(target, action, parameters or {}, timeout=self.config.request_timeout_seconds)

    async def _pair_device(self, payload: dict[str, Any], websocket: WebSocket) -> dict[str, Any]:
        offer_token = str(payload.get("pairing_token") or "").strip()
        offer_code = str(payload.get("pairing_code") or "").strip()
        offer = self.pairing_manager.get_offer(offer_token) if offer_token else self.pairing_manager.get_offer_by_code(offer_code)
        if offer is None:
            return {"success": False, "error": "Invalid or expired pairing token."}

        device_name = str(payload.get("device_name") or "Unknown Device").strip()
        platform = str(payload.get("platform") or "unknown").strip()
        os_version = str(payload.get("os_version") or "")
        agent_version = str(payload.get("agent_version") or "")
        battery = payload.get("battery")
        capabilities = list(payload.get("capabilities") or [])
        permissions = list(payload.get("permissions") or [])
        metadata = dict(payload.get("metadata") or {})
        ip = websocket.client.host if websocket.client else ""
        record, secret = self.device_manager.create_from_pairing(
            name=device_name,
            platform=platform,
            os_version=os_version,
            agent_version=agent_version,
            ip=ip,
            battery=int(battery) if isinstance(battery, (int, float, str)) and str(battery).isdigit() else None,
            capabilities=capabilities,
            permissions=permissions,
            metadata=metadata,
        )
        self._append_log("PAIR_APPROVED", device=record.device_id, name=record.name, platform=record.platform)
        return {
            "success": True,
            "device": record.to_dict(),
            "device_secret": secret,
            "pairing_token": offer.pairing_token,
        }

    def _build_app(self) -> FastAPI:
        app = FastAPI(docs_url=None, redoc_url=None)

        @app.get("/health")
        async def health():
            return {"ok": True, "running": self.is_running(), "host": self.config.host, "port": self.config.port}

        @app.get("/gateway/info")
        async def info():
            return {
                "ok": True,
                "service": "Brahma Connect",
                "host": self.config.host,
                "port": self.config.port,
                "advertise": self.config.advertise,
                "paired_devices": len(self.device_manager.list_devices()),
                "log_entries": len(self._log),
            }

        @app.get("/gateway/pair")
        async def get_pairing_offer():
            return self.create_pairing_offer()

        @app.get("/gateway/devices")
        async def list_devices():
            return {"ok": True, "devices": self.device_manager.list_devices()}

        @app.post("/gateway/devices/{device_id}/revoke")
        async def revoke_device(device_id: str):
            if not self.device_manager.revoke(device_id):
                return JSONResponse({"ok": False, "error": "Device not found."}, status_code=404)
            self._append_log("DEVICE_REVOKED", device_id=device_id)
            return {"ok": True}

        @app.post("/gateway/devices/{device_id}/forget")
        async def forget_device(device_id: str):
            if not self.device_manager.remove(device_id):
                return JSONResponse({"ok": False, "error": "Device not found."}, status_code=404)
            self._append_log("DEVICE_FORGOTTEN", device_id=device_id)
            return {"ok": True}

        @app.get("/gateway/logs")
        async def logs():
            return {"ok": True, "entries": self.log()}

        @app.get("/gateway/pending")
        async def pending_requests():
            return {"ok": True, "requests": self.list_pending_requests()}

        @app.post("/gateway/pending/{pending_id}/approve")
        async def approve_pending(pending_id: str):
            result = await self.approve_pending_request(pending_id)
            if not result.get("success"):
                return JSONResponse(result, status_code=404)
            return result

        @app.post("/gateway/pending/{pending_id}/reject")
        async def reject_pending(pending_id: str):
            if not self.reject_pending_request(pending_id):
                return JSONResponse({"ok": False, "error": "Pending request not found."}, status_code=404)
            return {"ok": True}

        @app.websocket("/ws")
        async def ws_endpoint(websocket: WebSocket):
            await websocket.accept()
            state = await self.hub.attach(websocket)
            device_id = ""
            try:
                while True:
                    incoming = await websocket.receive_json()
                    valid, error = validate_message(incoming)
                    if not valid:
                        await websocket.send_json(build_message(ProtocolTypes.ERROR, {"error": error}))
                        continue
                    msg_type = str(incoming["type"]).strip().lower()
                    request_id = str(incoming["request_id"])
                    payload = dict(incoming.get("payload") or {})

                    if msg_type == ProtocolTypes.PING:
                        await websocket.send_json(build_message(ProtocolTypes.PONG, {"status": "ok"}, request_id=request_id))
                        continue

                    if msg_type == ProtocolTypes.HELLO:
                        pending_id = new_request_id()
                        self._pending_requests[pending_id] = {
                            "request_id": pending_id,
                            "websocket": websocket,
                            "timestamp": now_iso(),
                            "device_name": str(payload.get("device_name") or "Unknown Device"),
                            "platform": str(payload.get("platform") or "unknown"),
                            "os_version": str(payload.get("os_version") or ""),
                            "agent_version": str(payload.get("agent_version") or ""),
                            "capabilities": list(payload.get("capabilities") or []),
                            "permissions": list(payload.get("permissions") or []),
                            "battery": payload.get("battery"),
                            "metadata": dict(payload.get("metadata") or {}),
                            "ip": websocket.client.host if websocket.client else "",
                        }
                        await websocket.send_json(
                            build_message(
                                ProtocolTypes.PAIR_REQUEST,
                                {
                                    "pending_id": pending_id,
                                    "message": "Pairing request received. Awaiting user approval in Brahma.",
                                    "device_name": self._pending_requests[pending_id]["device_name"],
                                    "platform": self._pending_requests[pending_id]["platform"],
                                },
                                request_id=request_id,
                            )
                        )
                        continue

                    if msg_type == ProtocolTypes.AUTHENTICATE:
                        device_id = str(payload.get("device_id") or "").strip()
                        secret = str(payload.get("device_secret") or "").strip()
                        record = self.device_manager.authenticate(
                            device_id,
                            secret,
                            ip=websocket.client.host if websocket.client else "",
                        )
                        if record is None:
                            await websocket.send_json(build_message(ProtocolTypes.ERROR, {"error": "Authentication failed."}, request_id=request_id))
                            continue
                        await self.hub.register(websocket, record.device_id)
                        self.device_manager.touch(record.device_id, ip=websocket.client.host if websocket.client else "")
                        self._append_log("DEVICE_CONNECTED", device_id=record.device_id, name=record.name)
                        await websocket.send_json(build_message(ProtocolTypes.DEVICE_ONLINE, {"device": record.to_dict()}, request_id=request_id))
                        await websocket.send_json(build_message(ProtocolTypes.CAPABILITIES, {"device_id": record.device_id, "capabilities": record.capabilities}, request_id=request_id))
                        continue

                    if msg_type == ProtocolTypes.PAIR_REQUEST:
                        result = await self._pair_device(payload, websocket)
                        await websocket.send_json(build_message(ProtocolTypes.PAIR_APPROVED if result.get("success") else ProtocolTypes.ERROR, result, request_id=request_id))
                        continue

                    if msg_type == ProtocolTypes.RESULT:
                        await self.hub.resolve_pending(device_id or str(payload.get("device_id") or ""), request_id, payload)
                        continue

                    if msg_type == ProtocolTypes.ERROR:
                        await self.hub.reject_pending(device_id or str(payload.get("device_id") or ""), request_id, str(payload.get("error") or "Unknown error"))
                        continue

                    if msg_type == ProtocolTypes.EVENT:
                        self._append_log("EVENT", device_id=device_id, payload=payload)
                        continue

                    if msg_type == ProtocolTypes.CHAT_MESSAGE:
                        if self.on_chat_message and payload.get("text"):
                            self.on_chat_message(payload.get("text"))
                        continue

                    if msg_type == ProtocolTypes.DEVICE_OFFLINE:
                        if device_id:
                            self.device_manager.mark_offline(device_id)
                            self._append_log("DEVICE_DISCONNECTED", device_id=device_id)
                        continue

                    await websocket.send_json(build_message(ProtocolTypes.ERROR, {"error": f"Unsupported message type: {msg_type}."}, request_id=request_id))
            except WebSocketDisconnect:
                pass
            finally:
                detached = await self.hub.unregister(websocket)
                if detached:
                    self.device_manager.mark_offline(detached)
                    self._append_log("DEVICE_DISCONNECTED", device_id=detached)

        return app

    async def serve(self) -> None:
        if not self.config.enabled:
            return
        self._running = True
        advertised = False
        if self.config.advertise:
            advertised = self.discovery.start(host=self.config.host, port=self.config.port, properties={"service": "brahma", "version": "1"})
        self._append_log("GATEWAY_STARTING", host=self.config.host, port=self.config.port, advertised=advertised)
        try:
            cfg = uvicorn.Config(
                self.app,
                host=self.config.host,
                port=self.config.port,
                log_level="warning",
                log_config=None,
                access_log=False,
            )
            self._server = uvicorn.Server(cfg)
            self._server.install_signal_handlers = lambda: None
            await self._server.serve()
        finally:
            self._server = None
            self.discovery.stop()
            self._running = False
