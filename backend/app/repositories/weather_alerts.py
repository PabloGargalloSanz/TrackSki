from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.weather.alerts import WeatherAlert


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
