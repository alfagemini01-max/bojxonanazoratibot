from __future__ import annotations

from typing import Any, Protocol


VehicleRecord = dict[str, Any]


class VehicleRepository(Protocol):
    async def find_by_plate(self, plate: str) -> VehicleRecord | None:
        """Return current vehicle control information by normalized plate."""
