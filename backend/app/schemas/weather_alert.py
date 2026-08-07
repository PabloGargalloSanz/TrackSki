from datetime import datetime

from pydantic import BaseModel


class WeatherAlert(BaseModel):
    id: int
    identifier: str
    level: str
    event: str
    area: str
    onset: datetime | None
    expires: datetime | None
    headline: str | None
    description: str | None
    instruction: str | None
    data_source: str
    created_at: datetime
