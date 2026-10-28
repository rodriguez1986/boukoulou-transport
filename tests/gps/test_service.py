import unittest
from datetime import datetime, timedelta, timezone

from app.gps.config import GPSSource, GPSMode
from app.gps.service import (
    GPSPoint,
    choose_position,
    validate_position,
)


class TestGPSService(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)

        self.phone = GPSPoint(
            vehicle_id=1,
            latitude=-4.2634,
            longitude=15.2429,
            speed=30.0,
            recorded_at=self.now,
            source=GPSSource.PHONE,
        )

        self.device = GPSPoint(
            vehicle_id=1,
            latitude=-4.2635,
            longitude=15.2430,
            speed=32.0,
            recorded_at=self.now,
            source=GPSSource.DEVICE,
        )

    def test_valid_position(self):
        validate_position(1, -4.2634, 15.2429, 30)

    def test_invalid_latitude(self):
        with self.assertRaises(ValueError):
            validate_position(1, 100, 15.2429, 30)

    def test_invalid_speed(self):
        with self.assertRaises(ValueError):
            validate_position(1, -4.2634, 15.2429, -5)

    def test_auto_prefers_device(self):
        selected = choose_position(
            self.phone,
            self.device,
            GPSMode.AUTO,
            self.now,
        )
        self.assertEqual(selected.source, GPSSource.DEVICE)

    def test_auto_fallback_to_phone(self):
        old_device = GPSPoint(
            vehicle_id=1,
            latitude=-4.2635,
            longitude=15.2430,
            speed=0,
            recorded_at=self.now - timedelta(minutes=5),
            source=GPSSource.DEVICE,
        )

        selected = choose_position(
            self.phone,
            old_device,
            GPSMode.AUTO,
            self.now,
        )
        self.assertEqual(selected.source, GPSSource.PHONE)

    def test_device_mode(self):
        selected = choose_position(
            self.phone,
            self.device,
            GPSMode.DEVICE,
            self.now,
        )
        self.assertEqual(selected.source, GPSSource.DEVICE)

    def test_no_recent_position(self):
        self.assertIsNone(
            choose_position(None, None, GPSMode.AUTO, self.now)
        )


if __name__ == "__main__":
    unittest.main()
