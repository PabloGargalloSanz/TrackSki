from unittest.mock import Mock
import unittest

from app.repositories.weather_alerts import get_active_weather_alerts


class WeatherAlertsRepositoryTest(unittest.TestCase):
    def test_get_active_weather_alerts_orders_by_severity(self) -> None:
        db = Mock()
        result = Mock()
        result.mappings.return_value = []
        db.execute.return_value = result

        alerts = get_active_weather_alerts(
            db,
            area="Pirineo",
            level="naranja",
            limit=50,
        )

        self.assertEqual(alerts, [])
        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("WHEN 'rojo' THEN 1", sql)
        self.assertIn("WHEN 'naranja' THEN 2", sql)
        self.assertIn("WHEN 'amarillo' THEN 3", sql)
        self.assertIn("expires IS NULL OR expires >= CURRENT_TIMESTAMP", sql)
        self.assertNotIn("raw_payload", sql)
        self.assertEqual(params["area"], "%Pirineo%")
        self.assertEqual(params["level"], "naranja")
        self.assertEqual(params["limit"], 50)

    def test_get_active_weather_alerts_filters_by_area_list(self) -> None:
        db = Mock()
        result = Mock()
        result.mappings.return_value = []
        db.execute.return_value = result

        get_active_weather_alerts(db, areas=["62", "69"])

        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("area IN", sql)
        self.assertEqual(params["areas"], ["62", "69"])


if __name__ == "__main__":
    unittest.main()
