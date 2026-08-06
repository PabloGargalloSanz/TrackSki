from pydantic import BaseModel

from app.schemas.resort import Resort
from app.schemas.road import ResortAccessStatusResponse, Road
from app.schemas.snow_report import SnowReport
from app.schemas.weather_alert import WeatherAlert
from app.schemas.weather_report import WeatherReport


class ResortSummary(BaseModel):
    resort: Resort
    latest_snow_report: SnowReport | None
    latest_weather_report: WeatherReport | None
    roads: list[Road]
    weather_alerts: list[WeatherAlert]
    access_status: ResortAccessStatusResponse
