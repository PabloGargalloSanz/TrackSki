import unittest
from datetime import timezone
from decimal import Decimal

import httpx

from app.services.weather.open_meteo import (
    OPEN_METEO_URL,
    OpenMeteoProvider,
    degrees_to_cardinal,
)


class OpenMeteoProviderTest(unittest.TestCase):
    def test_normalizes_current_conditions(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(str(request.url).split("?")[0], OPEN_METEO_URL)
            return httpx.Response(
                200,
                json={
                    "current": {
                        "time": "2026-06-15T12:00",
                        "temperature_2m": -2.4,
                        "precipitation": 0.7,
                        "weather_code": 73,
                        "wind_speed_10m": 18.5,
                        "wind_direction_10m": 315,
                        "visibility": 4200,
                    }
                },
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OpenMeteoProvider(client=client)

        observation = provider.get_current(42.6985, 0.9326)

        self.assertEqual(observation.temperature_celsius, Decimal("-2.4"))
        self.assertEqual(observation.precipitation_mm, Decimal("0.7"))
        self.assertEqual(observation.wind_speed_kmh, Decimal("18.5"))
        self.assertEqual(observation.wind_direction, "NW")
        self.assertEqual(observation.visibility_m, 4200)
        self.assertEqual(observation.weather, "Nevada moderada")
        self.assertEqual(observation.data_source, "open-meteo")
        self.assertEqual(observation.reported_at.tzinfo, timezone.utc)
        self.assertFalse(observation.is_verified)

        client.close()

    def test_converts_degrees_to_cardinal_direction(self) -> None:
        self.assertEqual(degrees_to_cardinal(0), "N")
        self.assertEqual(degrees_to_cardinal(90), "E")
        self.assertEqual(degrees_to_cardinal(225), "SW")
        self.assertIsNone(degrees_to_cardinal(None))


if __name__ == "__main__":
    unittest.main()
