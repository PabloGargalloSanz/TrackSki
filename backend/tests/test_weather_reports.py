from datetime import datetime, timezone
from unittest.mock import Mock
import unittest

from app.repositories.weather_reports import get_latest_weather_report_by_resort_id


class WeatherReportsRepositoryTest(unittest.TestCase):
    def test_get_latest_weather_report_returns_last_known_report(self) -> None:
        db = Mock()
        row = {
            "id": 1,
            "resort_id": 3,
            "temperature_celsius": 4.5,
            "wind_speed_kmh": 12.0,
            "wind_direction": "NW",
            "precipitation_mm": 0.0,
            "visibility_m": 12000,
            "weather": "Nublado",
            "data_source": "open_meteo",
            "is_verified": True,
            "reported_at": datetime(2026, 1, 1, 8, tzinfo=timezone.utc),
        }
        result = Mock()
        result.mappings.return_value.one_or_none.return_value = row
        db.execute.return_value = result

        report = get_latest_weather_report_by_resort_id(db, 3)

        self.assertEqual(report, row)
        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("ORDER BY reported_at DESC, id DESC", sql)
        self.assertNotIn("INTERVAL", sql)
        self.assertNotIn("CURRENT_TIMESTAMP", sql)
        self.assertEqual(params["resort_id"], 3)


if __name__ == "__main__":
    unittest.main()
