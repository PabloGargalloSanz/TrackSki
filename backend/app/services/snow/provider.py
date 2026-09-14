from typing import Protocol

from app.services.snow.models import SnowReportData


class SnowReportProvider(Protocol):
    def get_current(self, resort_id: int) -> SnowReportData: ...
