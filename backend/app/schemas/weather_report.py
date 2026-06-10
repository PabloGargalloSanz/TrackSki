from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class WeatherReport(BaseModel):
    id: int
    resort_id: int
    temperature_celsius: Decimal | None
    wind_speed_kmh: Decimal | None
    wind_direction: str | None
    precipitation_mm: Decimal | None
    visibility_m: int | None
    weather: str | None
    data_source: str
    is_verified: bool
    reported_at: datetime
