from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Optional

from .config import GPSSource, GPSMode, GPS_STALE_SECONDS


@dataclass(frozen=True)
class GPSPoint:
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float
    recorded_at: datetime
    source: GPSSource


def validate_position(
    vehicle_id: int,
    latitude: float,
    longitude: float,
    speed: float = 0.0,
) -> None:
    if isinstance(vehicle_id, bool) or not isinstance(vehicle_id, int) or vehicle_id <= 0:
        raise ValueError("Identifiant du véhicule invalide")

    for name, value in (
        ("latitude", latitude),
        ("longitude", longitude),
        ("vitesse", speed),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} doit être numérique")
        if not isfinite(value):
            raise ValueError(f"{name} doit être un nombre fini")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude invalide")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude invalide")

    if speed < 0:
        raise ValueError("La vitesse ne peut pas être négative")


def is_recent(
    point: Optional[GPSPoint],
    now: Optional[datetime] = None,
) -> bool:
    if point is None:
        return False

    now = now or datetime.now(timezone.utc)
    recorded_at = point.recorded_at

    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)

    age = (now - recorded_at).total_seconds()

    return 0 <= age <= GPS_STALE_SECONDS


def choose_position(
    phone: Optional[GPSPoint],
    device: Optional[GPSPoint],
    mode: GPSMode = GPSMode.AUTO,
    now: Optional[datetime] = None,
) -> Optional[GPSPoint]:
    now = now or datetime.now(timezone.utc)

    if mode == GPSMode.PHONE:
        return phone if is_recent(phone, now) else None

    if mode == GPSMode.DEVICE:
        return device if is_recent(device, now) else None

    if is_recent(device, now):
        return device

    if is_recent(phone, now):
        return phone

    return None
