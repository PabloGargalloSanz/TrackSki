from dataclasses import dataclass
from datetime import date, datetime
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


@dataclass(frozen=True)
class WeatherForecast:
    forecast_date: date
    reported_at: datetime
    temperature_min_celsius: Decimal | None
    temperature_max_celsius: Decimal | None
    precipitation_mm: Decimal | None
    snowfall_cm: Decimal | None
    wind_speed_max_kmh: Decimal | None
    weather: str | None
    data_source: str
    is_verified: bool = False
