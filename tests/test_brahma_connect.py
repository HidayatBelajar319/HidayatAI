import asyncio
from pathlib import Path

from brahma_connect.gateway.command_router import CommandRouter
from brahma_connect.gateway.device_manager import DeviceManager
from brahma_connect.gateway.capability_manager import CapabilityManager
from brahma_connect.gateway.models import DeviceRecord
from brahma_connect.gateway.pairing import PairingManager
from brahma_connect.gateway.protocol import ProtocolTypes, build_message, validate_message
from brahma_connect.gateway.websocket import ConnectionHub


def test_protocol_message_has_required_fields():
    message = build_message(ProtocolTypes.HELLO, {"hello": True})

    assert message["type"] == ProtocolTypes.HELLO
    assert message["request_id"]
    assert message["timestamp"]
    assert message["payload"] == {"hello": True}
    assert validate_message(message) == (True, "")


def test_device_manager_persists_and_authenticates(tmp_path: Path):
    registry_path = tmp_path / "devices.json"
    manager = DeviceManager(registry_path)

    record, secret = manager.create_from_pairing(
        name="Galaxy S24",
        platform="android",
        os_version="14",
        agent_version="1.0.0",
        ip="192.168.1.12",
        capabilities=["camera", "screen_capture"],
        permissions=["camera"],
    )

    assert record.device_id
    assert secret
    assert registry_path.exists()

    loaded = DeviceManager(registry_path)
    fetched = loaded.get(record.device_id)
    assert fetched is not None
    assert fetched.name == "Galaxy S24"

    authenticated = loaded.authenticate(record.device_id, secret, ip="192.168.1.13")
    assert authenticated is not None
    assert authenticated.online is True
    assert authenticated.ip == "192.168.1.13"


def test_pairing_manager_returns_expiring_offer():
    pairing = PairingManager(ttl_seconds=120)
    offer = pairing.create_offer("192.168.1.20", 8765)

    assert offer.service == "_BRAHMA._tcp.local."
    assert offer.host == "192.168.1.20"
    assert len(offer.pairing_code) == 6
    assert pairing.get_offer(offer.pairing_token) is not None
    assert pairing.get_offer_by_code(offer.pairing_code) is not None


def test_command_router_reports_offline_device(tmp_path: Path):
    registry_path = tmp_path / "devices.json"
    manager = DeviceManager(registry_path)
    record = DeviceRecord(
        device_id="android_001",
        name="Galaxy S24",
        platform="android",
        online=False,
        capabilities=["camera"],
    )
    manager._devices[record.device_id] = record
    manager.save()

    router = CommandRouter(manager, ConnectionHub(), CapabilityManager())
    result = asyncio.run(router.route("Galaxy S24", "launch_app", {"package": "com.spotify.music"}))

    assert result["success"] is False
    assert "offline" in result["error"].lower()
