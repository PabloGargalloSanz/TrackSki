from dataclasses import dataclass
from typing import Protocol

from app.services.snow.models import SnowReportData


@dataclass(frozen=True)
class SnowScraperResort:
    resort_id: int
    name: str
    url: str


class SnowScraper(Protocol):
    source: str

    def get_current(self, resort: SnowScraperResort) -> SnowReportData: ...
