from typing import Protocol

from app.services.weather.models import WeatherObservation


class WeatherProvider(Protocol):
    def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherObservation: ...
