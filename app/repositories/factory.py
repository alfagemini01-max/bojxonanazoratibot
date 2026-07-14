from __future__ import annotations

from app.config import Settings

from .base import VehicleRepository
from .demo_repository import DemoVehicleRepository
from .sql_repository import SqlServerVehicleRepository


def create_vehicle_repository(settings: Settings) -> VehicleRepository:
    if settings.data_source == "sqlserver":
        return SqlServerVehicleRepository(settings.sql_connection_string, settings.sql_query_path)
    return DemoVehicleRepository()
