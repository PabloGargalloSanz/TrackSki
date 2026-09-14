from datetime import date, datetime, timezone
from decimal import Decimal

from app.repositories.weather_forecasts import (
    get_weather_forecasts_by_resort_id,
    upsert_weather_forecast,
)
from app.services.weather.models import WeatherForecast


class ScalarResult:
    def scalar_one(self) -> int:
        return 7


class MappingResult:
    def mappings(self) -> "MappingResult":
        return self

    def __iter__(self):
        return iter(
            [
                {
                    "id": 1,
                    "resort_id": 3,
                    "forecast_date": date(2026, 9, 15),
                    "weather": "Nevada ligera",
                }
            ]
        )


class FakeSession:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[tuple[str, dict]] = []

    def execute(self, query: object, params: dict) -> object:
        self.calls.append((str(query), params))
        return self.result


def test_upsert_weather_forecast_updates_existing_forecast() -> None:
    db = FakeSession(ScalarResult())
    forecast = WeatherForecast(
        forecast_date=date(2026, 9, 15),
        reported_at=datetime(2026, 9, 14, 8, tzinfo=timezone.utc),
        temperature_min_celsius=Decimal("-3.2"),
        temperature_max_celsius=Decimal("4.8"),
        precipitation_mm=Decimal("2.5"),
        snowfall_cm=Decimal("6.0"),
        wind_speed_max_kmh=Decimal("28.4"),
        weather="Nevada ligera",
        data_source="open-meteo",
        is_verified=True,
    )

    forecast_id = upsert_weather_forecast(db, resort_id=3, forecast=forecast)

    sql, params = db.calls[0]
    assert forecast_id == 7
    assert "ON CONFLICT (resort_id, data_source, forecast_date)" in sql
    assert "DO UPDATE SET" in sql
    assert params["resort_id"] == 3
    assert params["forecast_date"] == date(2026, 9, 15)
    assert params["snowfall_cm"] == Decimal("6.0")


def test_get_weather_forecasts_by_resort_id_returns_upcoming_forecasts() -> None:
    db = FakeSession(MappingResult())

    forecasts = get_weather_forecasts_by_resort_id(db, resort_id=3, limit=5)

    sql, params = db.calls[0]
    assert "forecast_date >= CURRENT_DATE" in sql
    assert "ORDER BY forecast_date ASC" in sql
    assert params == {"resort_id": 3, "limit": 5}
    assert forecasts == [
        {
            "id": 1,
            "resort_id": 3,
            "forecast_date": date(2026, 9, 15),
            "weather": "Nevada ligera",
        }
    ]
