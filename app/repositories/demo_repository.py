from __future__ import annotations

from .base import VehicleRecord
from .demo_data import DEMO_VEHICLES


class DemoVehicleRepository:
    async def find_by_plate(self, plate: str) -> VehicleRecord | None:
        vehicle = DEMO_VEHICLES.get(plate)
        if vehicle is None:
            return None
        return dict(vehicle)
