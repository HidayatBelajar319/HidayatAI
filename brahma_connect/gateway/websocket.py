from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from .models import DeviceRecord


@dataclass(slots=True)
class ConnectionState:
    websocket: WebSocket
    device_id: str = ""
    role: str = "agent"
    authenticated: bool = False
    pending: dict[str, asyncio.Future] = field(default_factory=dict)


class ConnectionHub:
    def __init__(self):
        self._connections: dict[str, ConnectionState] = {}
        self._socket_index: dict[int, str] = {}
        self._lock = asyncio.Lock()

    async def attach(self, websocket: WebSocket, *, role: str = "agent") -> ConnectionState:
        state = ConnectionState(websocket=websocket, role=role)
        async with self._lock:
            key = id(websocket)
            self._socket_index[key] = ""
        return state

    async def register(self, websocket: WebSocket, device_id: str, *, role: str = "agent") -> ConnectionState:
        state = ConnectionState(websocket=websocket, device_id=device_id, role=role, authenticated=True)
        async with self._lock:
            self._connections[device_id] = state
            self._socket_index[id(websocket)] = device_id
        return state

    async def unregister(self, websocket: WebSocket) -> str:
        async with self._lock:
            device_id = self._socket_index.pop(id(websocket), "")
            if device_id:
                self._connections.pop(device_id, None)
            return device_id

    async def get(self, device_id: str) -> ConnectionState | None:
        async with self._lock:
            return self._connections.get(str(device_id))

    async def send_to_device(self, device_id: str, message: dict[str, Any]) -> bool:
        state = await self.get(device_id)
        if state is None:
            return False
        await state.websocket.send_json(message)
        return True

    async def broadcast_chat_message(self, message: dict[str, Any]) -> None:
        async with self._lock:
            states = list(self._connections.values())
        for state in states:
            try:
                await state.websocket.send_json(message)
            except Exception:
                pass

    async def set_pending(self, device_id: str, request_id: str) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        async with self._lock:
            state = self._connections.get(device_id)
            if state is None:
                future.set_exception(RuntimeError("Device connection is unavailable."))
                return future
            state.pending[request_id] = future
        return future

    async def resolve_pending(self, device_id: str, request_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            state = self._connections.get(device_id)
            if state is None:
                return
            future = state.pending.pop(request_id, None)
        if future and not future.done():
            future.set_result(payload)

    async def reject_pending(self, device_id: str, request_id: str, error: str) -> None:
        async with self._lock:
            state = self._connections.get(device_id)
            if state is None:
                return
            future = state.pending.pop(request_id, None)
        if future and not future.done():
            future.set_exception(RuntimeError(error))

    async def close_device(self, device_id: str, code: int = 1000, reason: str = "") -> bool:
        async with self._lock:
            state = self._connections.get(str(device_id))
        if state is None:
            return False
        try:
            await state.websocket.close(code=code, reason=reason)
        except Exception:
            return False
        return True
