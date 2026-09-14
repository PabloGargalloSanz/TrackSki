import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from app.commands import ingest_forecast
from app.services.weather.models import WeatherForecast


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


class FakeProvider:
    def __enter__(self) -> "FakeProvider":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get_daily_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> list[WeatherForecast]:
        return [
            WeatherForecast(
                forecast_date=date(2026, 9, 15),
                reported_at=datetime(2026, 9, 14, 8, tzinfo=timezone.utc),
                temperature_min_celsius=Decimal("-2.0"),
                temperature_max_celsius=Decimal("5.0"),
                precipitation_mm=Decimal("1.2"),
                snowfall_cm=Decimal("0.0"),
                wind_speed_max_kmh=Decimal("18.0"),
                weather="Parcialmente nuboso",
                data_source="open-meteo",
            )
        ]


class IngestForecastTest(unittest.TestCase):
    @patch("app.commands.ingest_forecast.upsert_weather_forecast")
    @patch("app.commands.ingest_forecast.OpenMeteoProvider", return_value=FakeProvider())
    @patch("app.commands.ingest_forecast.get_resorts")
    @patch("app.commands.ingest_forecast.SessionLocal")
    def test_imports_forecasts_for_all_resorts(
        self,
        session_local: Mock,
        get_resorts: Mock,
        _provider: Mock,
        upsert_weather_forecast: Mock,
    ) -> None:
        db = FakeSession()
        session_local.return_value = db
        get_resorts.return_value = [
            {
                "id": 3,
                "name": "Formigal",
                "latitude": 42.775,
                "longitude": -0.372,
            }
        ]

        result = ingest_forecast.run(days=3)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.processed, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(result.metadata["days"], 3)
        self.assertEqual(db.commits, 1)
        self.assertTrue(db.closed)
        upsert_weather_forecast.assert_called_once()


if __name__ == "__main__":
    unittest.main()
