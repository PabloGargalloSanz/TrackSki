from datetime import datetime, timezone
from dataclasses import dataclass
from html.parser import HTMLParser
import re
import unicodedata

import httpx

from app.scrapers.snow.base import SnowScraperResort
from app.services.snow.models import SnowReportData, TrailBreakdown


SOURCE = "baqueira"
BAQUEIRA_URLS = [
    "https://www.baqueira.es/estado-pistas",
    "https://www.baqueira.es/estado-pistas/Beret",
    "https://www.baqueira.es/estado-pistas/Bonaigua",
    "https://www.baqueira.es/estado-pistas/Baciver",
]
BAQUEIRA_WEATHER_URL = "https://www.baqueira.es/meteorologia"
URL_SEPARATOR = "|"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
    "Referer": "https://www.baqueira.es/",
}

LIFT_CLASSES = {
    "carpet",
    "gondola",
    "cable_car",
    "chair_lift",
    "drag_lift",
    "ski_lift",
    "2-person",
    "3-person",
    "4-person",
    "6-person",
    "8-person",
}


BAQUEIRA_RESORTS = [
    SnowScraperResort(
        resort_id=0,
        name="Baqueira Beret",
        url=URL_SEPARATOR.join(BAQUEIRA_URLS),
    ),
]


class BaqueiraSnowScraper:
    source = SOURCE

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30)

    def get_current(self, resort: SnowScraperResort) -> SnowReportData:
        reports = []
        blocks_by_url = {}
        for url in _resort_urls(resort.url):
            response = self.client.get(
                url,
                headers=REQUEST_HEADERS,
                follow_redirects=True,
            )
            response.raise_for_status()
            report = parse_baqueira_snow_report(response.text)
            blocks_by_url[_url_label(url)] = _total_report_blocks(report)
            if _has_baqueira_data(report):
                reports.append(report)

        if not reports:
            diagnostics = ", ".join(
                f"{label}={blocks}" for label, blocks in blocks_by_url.items()
            )
            raise ValueError(
                "No se encontraron datos de Baqueira en las paginas descargadas"
                f" ({diagnostics})."
            )

        report = merge_baqueira_reports(reports)

        weather_response = self.client.get(
            BAQUEIRA_WEATHER_URL,
            headers=REQUEST_HEADERS,
            follow_redirects=True,
        )
        weather_response.raise_for_status()
        weather_data = parse_baqueira_weather_report(weather_response.text)

        return SnowReportData(
            reported_at=report.reported_at,
            open_lifts=report.open_lifts,
            total_lifts=report.total_lifts,
            open_km=report.open_km,
            total_km=report.total_km,
            snow_depth_min_cm=weather_data.snow_depth_min_cm,
            snow_depth_max_cm=weather_data.snow_depth_max_cm,
            avalanche_risk=weather_data.avalanche_risk,
            access_status=report.access_status,
            green_trails=report.green_trails,
            blue_trails=report.blue_trails,
            red_trails=report.red_trails,
            black_trails=report.black_trails,
            data_source=SOURCE,
            is_verified=True,
        )

    def close(self) -> None:
        self.client.close()


def parse_baqueira_snow_report(
    html: str,
    reported_at: datetime | None = None,
) -> SnowReportData:
    parser = _BaqueiraParser()
    parser.feed(html)

    access_status = _access_status(parser)

    return SnowReportData(
        reported_at=reported_at or datetime.now(timezone.utc),
        open_lifts=parser.open_lifts,
        total_lifts=parser.total_lifts,
        access_status=access_status,
        green_trails=TrailBreakdown(
            open=parser.open_green_trails,
            total=parser.total_green_trails,
        ),
        blue_trails=TrailBreakdown(
            open=parser.open_blue_trails,
            total=parser.total_blue_trails,
        ),
        red_trails=TrailBreakdown(
            open=parser.open_red_trails,
            total=parser.total_red_trails,
        ),
        black_trails=TrailBreakdown(
            open=parser.open_black_trails,
            total=parser.total_black_trails,
        ),
        data_source=SOURCE,
        is_verified=True,
    )


def merge_baqueira_reports(reports: list[SnowReportData]) -> SnowReportData:
    if not reports:
        return SnowReportData(
            reported_at=datetime.now(timezone.utc),
            access_status="Sin datos",
            data_source=SOURCE,
            is_verified=True,
        )

    access_statuses = [report.access_status for report in reports if report.access_status]
    if "Estacion abierta" in access_statuses:
        access_status = "Estacion abierta"
    elif "Estacion cerrada" in access_statuses:
        access_status = "Estacion cerrada"
    else:
        access_status = "Sin datos"

    return SnowReportData(
        reported_at=max(report.reported_at for report in reports),
        open_lifts=sum(report.open_lifts for report in reports),
        total_lifts=sum(report.total_lifts for report in reports),
        access_status=access_status,
        green_trails=_merge_trails([report.green_trails for report in reports]),
        blue_trails=_merge_trails([report.blue_trails for report in reports]),
        red_trails=_merge_trails([report.red_trails for report in reports]),
        black_trails=_merge_trails([report.black_trails for report in reports]),
        data_source=SOURCE,
        is_verified=True,
    )


@dataclass(frozen=True)
class BaqueiraWeatherData:
    snow_depth_min_cm: int | None = None
    snow_depth_max_cm: int | None = None
    avalanche_risk: int | None = None


def parse_baqueira_weather_report(html: str) -> BaqueiraWeatherData:
    parser = _TextParser()
    parser.feed(html)
    text = " ".join(parser.all_text)
    snow_depth_min_cm, snow_depth_max_cm = _snow_depth_range(text)

    return BaqueiraWeatherData(
        snow_depth_min_cm=snow_depth_min_cm,
        snow_depth_max_cm=snow_depth_max_cm,
        avalanche_risk=_avalanche_risk(text),
    )


class _BaqueiraParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.open_lifts = 0
        self.total_lifts = 0
        self.open_green_trails = 0
        self.total_green_trails = 0
        self.open_blue_trails = 0
        self.total_blue_trails = 0
        self.open_red_trails = 0
        self.total_red_trails = 0
        self.open_black_trails = 0
        self.total_black_trails = 0
        self.open_accesses = 0
        self.total_accesses = 0
        self.blocks = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "li":
            return

        attrs_by_name = {key: value or "" for key, value in attrs}
        classes = set(attrs_by_name.get("class", "").split())
        if "spolio-block" not in classes:
            return

        data_classes = set(attrs_by_name.get("data-class", "").split())
        if not data_classes:
            return

        self.blocks += 1
        is_open = "open" in data_classes

        if "access" in data_classes:
            self.total_accesses += 1
            if is_open:
                self.open_accesses += 1

        if data_classes.intersection(LIFT_CLASSES):
            self.total_lifts += 1
            if is_open:
                self.open_lifts += 1

        self._count_trail(data_classes, is_open, "pista-verde", "green")
        self._count_trail(data_classes, is_open, "pista-azul", "blue")
        self._count_trail(data_classes, is_open, "pista-roja", "red")
        self._count_trail(data_classes, is_open, "pista-negra", "black")

    def _count_trail(
        self,
        data_classes: set[str],
        is_open: bool,
        trail_class: str,
        color: str,
    ) -> None:
        if trail_class not in data_classes:
            return

        total_field = f"total_{color}_trails"
        open_field = f"open_{color}_trails"
        setattr(self, total_field, getattr(self, total_field) + 1)
        if is_open:
            setattr(self, open_field, getattr(self, open_field) + 1)


def _access_status(parser: _BaqueiraParser) -> str:
    if parser.open_accesses > 0:
        return "Estacion abierta"
    if parser.total_accesses > 0:
        return "Estacion cerrada"
    if parser.open_lifts > 0 or _open_trail_count(parser) > 0:
        return "Estacion abierta"
    if parser.blocks == 0:
        return "Sin datos"
    return "Sin datos"


def _open_trail_count(parser: _BaqueiraParser) -> int:
    return (
        parser.open_green_trails
        + parser.open_blue_trails
        + parser.open_red_trails
        + parser.open_black_trails
    )


def _merge_trails(trails: list[TrailBreakdown]) -> TrailBreakdown:
    return TrailBreakdown(
        open=sum(trail.open for trail in trails),
        total=sum(trail.total for trail in trails),
    )


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.all_text: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.all_text.append(text)


def _has_baqueira_data(report: SnowReportData) -> bool:
    return any(
        [
            report.total_lifts,
            report.green_trails.total,
            report.blue_trails.total,
            report.red_trails.total,
            report.black_trails.total,
            report.access_status != "Sin datos",
        ]
    )


def _total_report_blocks(report: SnowReportData) -> int:
    return (
        report.total_lifts
        + report.green_trails.total
        + report.blue_trails.total
        + report.red_trails.total
        + report.black_trails.total
    )


def _url_label(url: str) -> str:
    return url.rstrip("/").split("/")[-1] or "estado-pistas"


def _resort_urls(url: str) -> list[str]:
    return [current_url.strip() for current_url in url.split(URL_SEPARATOR) if current_url.strip()]


def _snow_depth_range(text: str) -> tuple[int | None, int | None]:
    normalized_text = _normalize_text(text)
    match = re.search(
        r"(?:espesor|espesores|nieve).{0,80}?(\d{1,3})(?:\s*[-/]\s*(\d{1,3}))?\s*cm",
        normalized_text,
    )
    if not match:
        return None, None

    first_depth = int(match.group(1))
    second_depth = int(match.group(2)) if match.group(2) else first_depth
    return min(first_depth, second_depth), max(first_depth, second_depth)


def _avalanche_risk(text: str) -> int | None:
    normalized_text = _normalize_text(text)
    match = re.search(r"\b([1-5])\s*/\s*5\b", normalized_text)
    if match:
        return int(match.group(1))

    match = re.search(r"\b(?:alud|aludes|avalancha|avalanchas)\D{0,50}([1-5])\b", normalized_text)
    if match:
        return int(match.group(1))

    return None


def _normalize_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in without_accents if not unicodedata.combining(char)
    ).lower()
