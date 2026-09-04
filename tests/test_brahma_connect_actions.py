import json
from pathlib import Path

from actions import brahma_connect as bc


class FakeService:
    def __init__(self):
        self.devices = [
            {
                "device_id": "android_001",
                "name": "Galaxy S24",
                "platform": "android",
                "online": True,
                "battery": 82,
                "capabilities": ["camera", "clipboard", "screen_capture", "files"],
                "permissions": ["camera"],
            },
            {
                "device_id": "win_001",
                "name": "Gaming Laptop",
                "platform": "windows",
                "online": False,
                "battery": None,
                "capabilities": ["screen", "mouse", "keyboard", "files", "clipboard"],
                "permissions": [],
            },
        ]

    def list_devices(self):
        return list(self.devices)

    def get_device(self, target: str):
        for device in self.devices:
            if target.lower() in {device["device_id"].lower(), device["name"].lower()}:
                return device
        return None

    def resolve_devices(self, query: str):
        q = query.lower()
        if "phone" in q:
            return [self.devices[0]]
        if "laptop" in q:
            return [self.devices[1]]
        return []

    def get_capabilities(self, target: str):
        device = self.get_device(target)
        if not device:
            return {"success": False, "error": "Device not found.", "error_code": "DEVICE_NOT_FOUND"}
        return {"success": True, "device": device, "capabilities": device["capabilities"], "permissions": device["permissions"]}

    def route_command(self, target: str, action: str, parameters: dict | None = None):
        parameters = dict(parameters or {})
        required_capabilities = list(parameters.pop("required_capabilities", []))
        if target == "Galaxy S24" and "mouse" in required_capabilities:
            return {"success": False, "device": "android_001", "action": action, "error": "That device does not support: mouse.", "error_code": "CAPABILITY_MISSING", "missing": ["mouse"]}
        if target == "Gaming Laptop":
            return {"success": False, "device": "win_001", "action": action, "error": "Your Gaming Laptop is currently offline.", "error_code": "DEVICE_OFFLINE"}
        return {"success": True, "device": "android_001", "action": action, "data": {"ok": True}, "request_id": "req_1"}

    def create_pairing_offer(self, *, device_name: str = "Unknown Device", platform: str = "unknown"):
        return {"service": "_BRAHMA._tcp.local.", "host": "192.168.1.20", "port": 8765, "pairing_token": "token", "pairing_code": "123456", "expires": 300}

    async def disconnect_device(self, target: str, *, reason: str = "Disconnected by Ultron Jarvis"):
        return {"success": True, "device": {"name": target}, "disconnected": True}

    async def approve_pending_request(self, pending_id: str):
        return {"success": True, "device": {"device_id": "android_001"}, "device_secret": "secret"}


def test_connect_tools_are_registered_in_main():
    main_text = Path("main.py").read_text(encoding="utf-8")
    for tool_name in (
        "connect_list_devices",
        "connect_get_device",
        "connect_get_capabilities",
        "connect_execute",
        "connect_pair_device",
        "connect_disconnect_device",
    ):
        assert f'"name": "{tool_name}"' in main_text


def test_connect_list_devices_and_capabilities(monkeypatch):
    bc.set_service_provider(lambda: FakeService())
    try:
        devices = json.loads(bc.connect_list_devices())
        assert devices["success"] is True
        assert devices["count"] == 2

        caps = json.loads(bc.connect_get_capabilities({"device": "Galaxy S24"}))
        assert caps["success"] is True
        assert "camera" in caps["capabilities"]

        unknown = json.loads(bc.connect_get_capabilities({"device": "Unknown Device"}))
        assert unknown["success"] is False
        assert unknown["error_code"] == "DEVICE_NOT_FOUND"
    finally:
        bc.set_service_provider(None)


def test_connect_device_resolution_and_offline_handling(monkeypatch):
    bc.set_service_provider(lambda: FakeService())
    try:
        device = json.loads(bc.connect_get_device({"device": "my phone"}))
        assert device["success"] is True
        assert device["device"]["name"] == "Galaxy S24"

        unknown = json.loads(bc.connect_get_device({"device": "smart watch"}))
        assert unknown["success"] is False
        assert unknown["error_code"] == "DEVICE_NOT_FOUND"

        offline = json.loads(bc.connect_execute({"device": "Gaming Laptop", "action": "launch_app", "parameters": {"app_name": "Chrome"}}))
        assert offline["success"] is False
        assert offline["error_code"] == "DEVICE_OFFLINE"
    finally:
        bc.set_service_provider(None)


def test_connect_execute_validates_capability_and_parameters(monkeypatch):
    bc.set_service_provider(lambda: FakeService())
    try:
        missing_param = json.loads(bc.connect_execute({"device": "Galaxy S24", "action": "open_url", "parameters": {}}))
        assert missing_param["success"] is False
        assert missing_param["error_code"] == "MISSING_PARAMETERS"

        unsupported = json.loads(bc.connect_execute({"device": "Galaxy S24", "action": "mouse_move", "parameters": {"x": 1, "y": 2}}))
        assert unsupported["success"] is False
        assert unsupported["error_code"] == "CAPABILITY_MISSING"

        success = json.loads(bc.connect_execute({"device": "Galaxy S24", "action": "launch_app", "parameters": {"app_name": "Spotify"}}))
        assert success["success"] is True
        assert success["device"] == "android_001"
    finally:
        bc.set_service_provider(None)


def test_connect_pair_and_disconnect(monkeypatch):
    bc.set_service_provider(lambda: FakeService())
    try:
        pairing = json.loads(bc.connect_pair_device({"device_name": "Galaxy S24", "platform": "android"}))
        assert pairing["success"] is True
        assert pairing["pairing"]["pairing_code"] == "123456"

        disconnect = json.loads(bc.connect_disconnect_device({"device": "Galaxy S24"}))
        assert disconnect["success"] is True
    finally:
        bc.set_service_provider(None)
