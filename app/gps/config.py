from enum import Enum


class GPSSource(str, Enum):
    PHONE = "PHONE"
    DEVICE = "DEVICE"


class GPSMode(str, Enum):
    PHONE = "PHONE"
    DEVICE = "DEVICE"
    AUTO = "AUTO"


GPS_REFRESH_SECONDS = 5
GPS_STALE_SECONDS = 60
GPS_DEVICE_PRIORITY = True
