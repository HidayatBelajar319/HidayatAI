from __future__ import annotations

import secrets
import time
from typing import Any

from .authentication import generate_pairing_token
from .models import PairingOffer


class PairingManager:
    def __init__(self, service_name: str = "_BRAHMA._tcp.local.", ttl_seconds: int = 300):
        self.service_name = service_name
        self.ttl_seconds = max(60, int(ttl_seconds))
        self._offers: dict[str, PairingOffer] = {}
        self._code_index: dict[str, str] = {}

    def _prune(self) -> None:
        now = time.time()
        stale = [token for token, offer in self._offers.items() if offer.expires_at <= now]
        for token in stale:
            offer = self._offers.pop(token, None)
            if offer is not None:
                self._code_index.pop(offer.pairing_code, None)

    def create_offer(self, host: str, port: int) -> PairingOffer:
        self._prune()
        token = generate_pairing_token()
        code = f"{secrets.randbelow(1_000_000):06d}"
        offer = PairingOffer(
            service=self.service_name,
            host=host,
            port=int(port),
            pairing_token=token,
            pairing_code=code,
            expires_at=time.time() + self.ttl_seconds,
        )
        self._offers[token] = offer
        self._code_index[code] = token
        return offer

    def get_offer(self, pairing_token: str) -> PairingOffer | None:
        self._prune()
        return self._offers.get(pairing_token)

    def get_offer_by_code(self, pairing_code: str) -> PairingOffer | None:
        self._prune()
        token = self._code_index.get(str(pairing_code).strip())
        if not token:
            return None
        return self._offers.get(token)

    def approve(self, pairing_token: str) -> PairingOffer | None:
        self._prune()
        offer = self._offers.pop(pairing_token, None)
        if offer is None:
            return None
        self._code_index.pop(offer.pairing_code, None)
        return offer

    def reject(self, pairing_token: str) -> bool:
        self._prune()
        offer = self._offers.pop(pairing_token, None)
        if offer is None:
            return False
        self._code_index.pop(offer.pairing_code, None)
        return True

    def to_qr_payload(self, offer: PairingOffer) -> dict[str, Any]:
        return offer.to_dict()
