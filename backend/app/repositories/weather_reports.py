from sqlalchemy import text
from sqlalchemy.orm import Session


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
