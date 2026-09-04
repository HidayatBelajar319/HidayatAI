from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


@dataclass(slots=True)
class GatewayDiscovery:
    service_name: str = "_BRAHMA._tcp.local."
    _zeroconf: Any = None
    _service_info: Any = None

    def start(self, *, host: str, port: int, properties: dict[str, str] | None = None) -> bool:
        try:
            from zeroconf import IPVersion, ServiceInfo, Zeroconf
        except Exception:
            return False

        try:
            self._zeroconf = Zeroconf(ip_version=IPVersion.All)
            info = ServiceInfo(
                type_=self.service_name,
                name=f"Brahma Connect.{self.service_name}",
                addresses=[socket.inet_aton(host if host and host != "0.0.0.0" else local_ip())],
                port=int(port),
                properties={k.encode("utf-8"): v.encode("utf-8") for k, v in (properties or {}).items()},
            )
            self._service_info = info
            self._zeroconf.register_service(info)
            return True
        except Exception:
            self.stop()
            return False

    def stop(self) -> None:
        try:
            if self._zeroconf and self._service_info:
                self._zeroconf.unregister_service(self._service_info)
        except Exception:
            pass
        try:
            if self._zeroconf:
                self._zeroconf.close()
        except Exception:
            pass
        self._zeroconf = None
        self._service_info = None
