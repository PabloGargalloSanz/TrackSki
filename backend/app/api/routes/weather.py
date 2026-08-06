from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.weather_alerts import get_active_weather_alerts
from app.schemas.weather_alert import WeatherAlert

router = APIRouter()
AlertLimit = Annotated[int, Query(ge=1, le=500)]


def serialize_weather_alert(row: dict) -> WeatherAlert:
    return WeatherAlert(
        id=row["id"],
        identifier=row["identifier"],
        level=row["level"],
        event=row["event"],
        area=row["area"],
        onset=row["onset"],
        expires=row["expires"],
        headline=row["headline"],
        description=row["description"],
        instruction=row["instruction"],
        data_source=row["data_source"],
        created_at=row["created_at"],
    )


@router.get("/alerts/active", response_model=list[WeatherAlert])
def list_active_weather_alerts(
    area: str | None = None,
    level: str | None = None,
    limit: AlertLimit = 100,
    db: Session = Depends(get_db),
) -> list[WeatherAlert]:
    return [
        serialize_weather_alert(row)
        for row in get_active_weather_alerts(
            db,
            area=area,
            level=level,
            limit=limit,
        )
    ]
