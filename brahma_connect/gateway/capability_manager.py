from __future__ import annotations

from typing import Iterable


class CapabilityManager:
    def normalize(self, capability: str) -> str:
        return "_".join((capability or "").strip().lower().split())

    def normalize_many(self, capabilities: Iterable[str] | None) -> list[str]:
        values = []
        for capability in capabilities or []:
            normalized = self.normalize(capability)
            if normalized:
                values.append(normalized)
        return sorted(dict.fromkeys(values))

    def supports(self, capabilities: Iterable[str] | None, capability: str) -> bool:
        target = self.normalize(capability)
        return target in self.normalize_many(capabilities)

    def missing(self, capabilities: Iterable[str] | None, required: Iterable[str]) -> list[str]:
        current = set(self.normalize_many(capabilities))
        return [self.normalize(item) for item in required if self.normalize(item) not in current]
