from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.weather.models import WeatherObservation


def get_latest_weather_report_by_resort_id(db: Session, resort_id: int) -> dict | None:
    result = db.execute(
        text(
            """
            SELECT
                id,
                resort_id,
                temperature_celsius,
                wind_speed_kmh,
                wind_direction,
                precipitation_mm,
                visibility_m,
                weather,
                data_source,
                is_verified,
                reported_at
            FROM weather_reports
            WHERE resort_id = :resort_id
            ORDER BY reported_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"resort_id": resort_id},
    )

    row = result.mappings().one_or_none()
    return dict(row) if row else None


def get_weather_reports_by_resort_id(
    db: Session,
    resort_id: int,
    limit: int,
) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                id,
                resort_id,
                temperature_celsius,
                wind_speed_kmh,
                wind_direction,
                precipitation_mm,
                visibility_m,
                weather,
                data_source,
                is_verified,
                reported_at
            FROM weather_reports
            WHERE resort_id = :resort_id
            ORDER BY reported_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {"resort_id": resort_id, "limit": limit},
    )

    return [dict(row) for row in result.mappings()]


def create_weather_report_if_missing(
    db: Session,
    resort_id: int,
    observation: WeatherObservation,
) -> int | None:
    result = db.execute(
        text(
            """
            INSERT INTO weather_reports (
                resort_id,
                temperature_celsius,
                wind_speed_kmh,
                wind_direction,
                precipitation_mm,
                visibility_m,
                weather,
                data_source,
                is_verified,
                reported_at
            )
            SELECT
                :resort_id,
                :temperature_celsius,
                :wind_speed_kmh,
                :wind_direction,
                :precipitation_mm,
                :visibility_m,
                :weather,
                CAST(:data_source AS VARCHAR(100)),
                :is_verified,
                :reported_at
            WHERE NOT EXISTS (
                SELECT 1
                FROM weather_reports
                WHERE resort_id = :resort_id
                  AND data_source = CAST(:data_source AS VARCHAR(100))
                  AND reported_at = :reported_at
            )
            RETURNING id
            """
        ),
        {
            "resort_id": resort_id,
            "temperature_celsius": observation.temperature_celsius,
            "wind_speed_kmh": observation.wind_speed_kmh,
            "wind_direction": observation.wind_direction,
            "precipitation_mm": observation.precipitation_mm,
            "visibility_m": observation.visibility_m,
            "weather": observation.weather,
            "data_source": observation.data_source,
            "is_verified": observation.is_verified,
            "reported_at": observation.reported_at,
        },
    )

    return result.scalar_one_or_none()
