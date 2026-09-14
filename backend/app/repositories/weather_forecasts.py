from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.weather.models import WeatherForecast


def upsert_weather_forecast(
    db: Session,
    resort_id: int,
    forecast: WeatherForecast,
) -> int:
    result = db.execute(
        text(
            """
            INSERT INTO weather_forecasts (
                resort_id,
                forecast_date,
                temperature_min_celsius,
                temperature_max_celsius,
                precipitation_mm,
                snowfall_cm,
                wind_speed_max_kmh,
                weather,
                data_source,
                is_verified,
                reported_at
            )
            VALUES (
                :resort_id,
                :forecast_date,
                :temperature_min_celsius,
                :temperature_max_celsius,
                :precipitation_mm,
                :snowfall_cm,
                :wind_speed_max_kmh,
                :weather,
                :data_source,
                :is_verified,
                :reported_at
            )
            ON CONFLICT (resort_id, data_source, forecast_date)
            DO UPDATE SET
                temperature_min_celsius = EXCLUDED.temperature_min_celsius,
                temperature_max_celsius = EXCLUDED.temperature_max_celsius,
                precipitation_mm = EXCLUDED.precipitation_mm,
                snowfall_cm = EXCLUDED.snowfall_cm,
                wind_speed_max_kmh = EXCLUDED.wind_speed_max_kmh,
                weather = EXCLUDED.weather,
                is_verified = EXCLUDED.is_verified,
                reported_at = EXCLUDED.reported_at
            RETURNING id
            """
        ),
        {
            "resort_id": resort_id,
            "forecast_date": forecast.forecast_date,
            "temperature_min_celsius": forecast.temperature_min_celsius,
            "temperature_max_celsius": forecast.temperature_max_celsius,
            "precipitation_mm": forecast.precipitation_mm,
            "snowfall_cm": forecast.snowfall_cm,
            "wind_speed_max_kmh": forecast.wind_speed_max_kmh,
            "weather": forecast.weather,
            "data_source": forecast.data_source,
            "is_verified": forecast.is_verified,
            "reported_at": forecast.reported_at,
        },
    )

    return int(result.scalar_one())


def get_weather_forecasts_by_resort_id(
    db: Session,
    resort_id: int,
    limit: int = 7,
) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                id,
                resort_id,
                forecast_date,
                temperature_min_celsius,
                temperature_max_celsius,
                precipitation_mm,
                snowfall_cm,
                wind_speed_max_kmh,
                weather,
                data_source,
                is_verified,
                reported_at
            FROM weather_forecasts
            WHERE resort_id = :resort_id
              AND forecast_date >= CURRENT_DATE
            ORDER BY forecast_date ASC, id DESC
            LIMIT :limit
            """
        ),
        {"resort_id": resort_id, "limit": limit},
    )

    return [dict(row) for row in result.mappings()]
