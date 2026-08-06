from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.weather.alerts import WeatherAlert


def get_active_weather_alerts(
    db: Session,
    *,
    area: str | None = None,
    level: str | None = None,
    limit: int = 100,
) -> list[dict]:
    filters = [
        "(expires IS NULL OR expires >= CURRENT_TIMESTAMP)",
        "level <> 'verde'",
    ]
    params = {"limit": limit}
    if area:
        filters.append("area ILIKE :area")
        params["area"] = f"%{area}%"
    if level:
        filters.append("level = :level")
        params["level"] = level

    where_clause = " AND ".join(filters)
    result = db.execute(
        text(
            f"""
            SELECT
                id,
                identifier,
                level,
                event,
                area,
                onset,
                expires,
                headline,
                description,
                instruction,
                data_source,
                created_at
            FROM weather_alerts
            WHERE {where_clause}
            ORDER BY
                CASE level
                    WHEN 'rojo' THEN 1
                    WHEN 'naranja' THEN 2
                    WHEN 'amarillo' THEN 3
                    WHEN 'verde' THEN 4
                    ELSE 5
                END,
                COALESCE(onset, created_at) DESC,
                id DESC
            LIMIT :limit
            """
        ),
        params,
    )

    return [dict(row) for row in result.mappings()]


def save_weather_alert(db: Session, alert: WeatherAlert) -> int:
    result = db.execute(
        text(
            """
            INSERT INTO weather_alerts (
                identifier,
                level,
                event,
                area,
                onset,
                expires,
                headline,
                description,
                instruction,
                data_source
            )
            VALUES (
                :identifier,
                :level,
                :event,
                :area,
                :onset,
                :expires,
                :headline,
                :description,
                :instruction,
                :data_source
            )
            ON CONFLICT (identifier, area)
            DO UPDATE SET
                level = EXCLUDED.level,
                event = EXCLUDED.event,
                onset = EXCLUDED.onset,
                expires = EXCLUDED.expires,
                headline = EXCLUDED.headline,
                description = EXCLUDED.description,
                instruction = EXCLUDED.instruction,
                data_source = EXCLUDED.data_source
            RETURNING id
            """
        ),
        {
            "identifier": alert.identifier,
            "level": alert.level,
            "event": alert.event,
            "area": alert.area,
            "onset": alert.onset,
            "expires": alert.expires,
            "headline": alert.headline,
            "description": alert.description,
            "instruction": alert.instruction,
            "data_source": alert.source,
        },
    )

    return result.scalar_one()
