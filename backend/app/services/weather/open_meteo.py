from datetime import date, datetime, timezone
from decimal import Decimal

import httpx

from app.services.weather.models import WeatherForecast, WeatherObservation

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = (
    "temperature_2m",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "visibility",
)
DAILY_FIELDS = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
)

WMO_WEATHER = {
    0: "Despejado",
    1: "Principalmente despejado",
    2: "Parcialmente nuboso",
    3: "Cubierto",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna intensa",
    56: "Llovizna helada ligera",
    57: "Llovizna helada intensa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia intensa",
    66: "Lluvia helada ligera",
    67: "Lluvia helada intensa",
    71: "Nevada ligera",
    73: "Nevada moderada",
    75: "Nevada intensa",
    77: "Granos de nieve",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos intensos",
    85: "Chubascos de nieve ligeros",
    86: "Chubascos de nieve intensos",
    95: "Tormenta",
    96: "Tormenta con granizo ligero",
    99: "Tormenta con granizo intenso",
}


def degrees_to_cardinal(value: float | int | None) -> str | None:
    if value is None:
        return None

    directions = (
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    )
    return directions[round(float(value) / 22.5) % 16]


def decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def weather_from_code(value: object) -> str | None:
    if value is None:
        return None

    code = int(value)
    return WMO_WEATHER.get(code, f"Codigo WMO {code}")


class OpenMeteoProvider:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=15.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "OpenMeteoProvider":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherObservation:
        response = self._client.get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join(CURRENT_FIELDS),
                "timezone": "UTC",
            },
        )
        response.raise_for_status()

        current = response.json().get("current")
        if not isinstance(current, dict) or "time" not in current:
            raise ValueError("Open-Meteo no devolvio condiciones actuales validas")

        reported_at = datetime.fromisoformat(str(current["time"]))
        if reported_at.tzinfo is None:
            reported_at = reported_at.replace(tzinfo=timezone.utc)

        visibility = current.get("visibility")

        return WeatherObservation(
            reported_at=reported_at,
            temperature_celsius=decimal_or_none(current.get("temperature_2m")),
            wind_speed_kmh=decimal_or_none(current.get("wind_speed_10m")),
            wind_direction=degrees_to_cardinal(
                current.get("wind_direction_10m")
            ),
            precipitation_mm=decimal_or_none(current.get("precipitation")),
            visibility_m=int(visibility) if visibility is not None else None,
            weather=weather_from_code(current.get("weather_code")),
            data_source="open-meteo",
        )

    def get_daily_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> list[WeatherForecast]:
        response = self._client.get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": ",".join(DAILY_FIELDS),
                "forecast_days": days,
                "timezone": "UTC",
            },
        )
        response.raise_for_status()

        daily = response.json().get("daily")
        if not isinstance(daily, dict) or "time" not in daily:
            raise ValueError("Open-Meteo no devolvio prevision diaria valida")

        times = daily["time"]
        if not isinstance(times, list):
            raise ValueError("Open-Meteo no devolvio fechas de prevision validas")

        reported_at = datetime.now(timezone.utc)
        forecasts: list[WeatherForecast] = []
        for index, raw_date in enumerate(times):
            forecasts.append(
                WeatherForecast(
                    forecast_date=date.fromisoformat(str(raw_date)),
                    reported_at=reported_at,
                    temperature_min_celsius=decimal_or_none(
                        daily_value(daily, "temperature_2m_min", index)
                    ),
                    temperature_max_celsius=decimal_or_none(
                        daily_value(daily, "temperature_2m_max", index)
                    ),
                    precipitation_mm=decimal_or_none(
                        daily_value(daily, "precipitation_sum", index)
                    ),
                    snowfall_cm=decimal_or_none(
                        daily_value(daily, "snowfall_sum", index)
                    ),
                    wind_speed_max_kmh=decimal_or_none(
                        daily_value(daily, "wind_speed_10m_max", index)
                    ),
                    weather=weather_from_code(
                        daily_value(daily, "weather_code", index)
                    ),
                    data_source="open-meteo",
                )
            )

        return forecasts


def daily_value(daily: dict, key: str, index: int) -> object:
    values = daily.get(key)
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]
