"""
Historique GPS hybride - Boukoulou Transport V5.9.

DEVICE prioritaire.
PHONE utilise en secours lorsque DEVICE n'est plus recent.
Aucune modification des positions en base de donnees.
"""

from datetime import timezone
from typing import Iterable

from .config import GPS_STALE_SECONDS


def select_auto_history(positions: Iterable) -> list:
    """
    Selectionne les positions de l'historique GPS AUTO.

    Les positions doivent exposer :
      - id
      - source
      - recorded_at

    Les positions simultanees sont traitees avec
    priorite DEVICE.
    """

    def normalize_time(point):
        timestamp = point.recorded_at

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return timestamp.astimezone(timezone.utc)

    def source_name(point):
        return getattr(point.source, "value", point.source)

    ordered = sorted(
        positions,
        key=lambda p: (
            normalize_time(p),
            0 if source_name(p) == "DEVICE" else 1,
            p.id,
        ),
    )

    last_device = None
    selected = []

    for point in ordered:
        source = source_name(point)
        timestamp = normalize_time(point)

        if source == "DEVICE":
            last_device = point
            selected.append(point)
            continue

        if source != "PHONE":
            continue

        if last_device is not None:
            age_device = (
                timestamp - normalize_time(last_device)
            ).total_seconds()

            if 0 <= age_device <= GPS_STALE_SECONDS:
                continue

        selected.append(point)

    return selected
