from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class WeatherObservation:
    reported_at: datetime
    temperature_celsius: Decimal | None
    wind_speed_kmh: Decimal | None
    wind_direction: str | None
    precipitation_mm: Decimal | None
    visibility_m: int | None
    weather: str | None
    data_source: str
    is_verified: bool = False
