from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re
import unicodedata

import httpx

from app.scrapers.snow.base import SnowScraperResort
from app.services.snow.models import SnowReportData, TrailBreakdown


SOURCE = "grandvalira"
SNOW_REPORT_URL = "https://www.grandvalira.com/es/estacion/estado-pistas"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
    "Referer": "https://www.grandvalira.com/",
}


GRANDVALIRA_RESORTS = [
    SnowScraperResort(
        resort_id=0,
        name="Grandvalira",
        url=SNOW_REPORT_URL,
    ),
]


class GrandvaliraSnowScraper:
    source = SOURCE

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30)

    def get_current(self, resort: SnowScraperResort) -> SnowReportData:
        response = self.client.get(
            resort.url,
            headers=REQUEST_HEADERS,
            follow_redirects=True,
        )
        response.raise_for_status()
        report = parse_grandvalira_snow_report(response.text)
        if not _has_grandvalira_data(report):
            raise ValueError(
                "No se encontraron datos de Grandvalira en la pagina descargada."
            )
        return report

    def close(self) -> None:
        self.client.close()


def parse_grandvalira_snow_report(
    html: str,
    reported_at: datetime | None = None,
) -> SnowReportData:
    parser = _GrandvaliraParser()
    parser.feed(html)
    parser.close()

    open_lifts, total_lifts = _number_pair(parser.text_by_context.get("lifts", ""))
    open_km, total_km = _decimal_pair(parser.text_by_context.get("km", ""))
    snow_depth_min_cm, snow_depth_max_cm = _depth_range(
        parser.text_by_context.get("depth", "")
    )

    return SnowReportData(
        reported_at=reported_at or datetime.now(timezone.utc),
        open_lifts=open_lifts,
        total_lifts=total_lifts,
        open_km=open_km,
        total_km=total_km,
        snow_depth_min_cm=snow_depth_min_cm,
        snow_depth_max_cm=snow_depth_max_cm,
        access_status=_access_status(open_lifts, open_km, parser.trails),
        green_trails=parser.trails["green"],
        blue_trails=parser.trails["blue"],
        red_trails=parser.trails["red"],
        black_trails=parser.trails["black"],
        data_source=SOURCE,
        is_verified=True,
    )


class _GrandvaliraParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_by_context: dict[str, str] = {}
        self.trails = {
            "green": TrailBreakdown(),
            "blue": TrailBreakdown(),
            "red": TrailBreakdown(),
            "black": TrailBreakdown(),
        }
        self._context_stack: list[str | None] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in {"br", "img", "input", "meta", "link"}:
            return

        attrs_by_name = {key: value or "" for key, value in attrs}
        context = _context_from_attrs(attrs_by_name)
        self._context_stack.append(context)

        if context == "lifts" and attrs_by_name.get("value"):
            self._append_context_text(context, attrs_by_name["value"])

    def handle_endtag(self, tag: str) -> None:
        if tag not in {"br", "img", "input", "meta", "link"} and self._context_stack:
            self._context_stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return

        for context in self._context_stack:
            if context:
                self._append_context_text(context, text)

    def close(self) -> None:
        super().close()
        for color in self.trails:
            self.trails[color] = _trail_breakdown(
                self.text_by_context.get(f"trail_{color}", "")
            )

    def _append_context_text(self, context: str, text: str) -> None:
        current_text = self.text_by_context.get(context, "")
        self.text_by_context[context] = f"{current_text} {text}".strip()


def _context_from_attrs(attrs: dict[str, str]) -> str | None:
    element_id = _normalize_text(attrs.get("id", ""))
    aria_label = _normalize_text(attrs.get("aria-label", ""))
    classes = {_normalize_text(value) for value in attrs.get("class", "").split()}

    if element_id == "facilities-resort-status-grandvalira":
        return "lifts"
    if "kilometros esquiables" in aria_label:
        return "km"
    if "espesores de nieve" in aria_label:
        return "depth"
    if any("icon-green" in value for value in classes):
        return "trail_green"
    if any("icon-blue" in value for value in classes):
        return "trail_blue"
    if any("icon-red" in value for value in classes):
        return "trail_red"
    if any("icon-black" in value for value in classes):
        return "trail_black"

    return None


def _trail_breakdown(value: str) -> TrailBreakdown:
    open_trails, total_trails = _number_pair(value)
    return TrailBreakdown(open=open_trails, total=total_trails)


def _number_pair(value: str) -> tuple[int, int]:
    values = _numbers(value)
    if not values:
        return 0, 0
    if len(values) == 1:
        return int(values[0]), 0
    return int(values[0]), int(values[1])


def _decimal_pair(value: str) -> tuple[Decimal, Decimal]:
    values = _numbers(value)
    if not values:
        return Decimal("0"), Decimal("0")
    if len(values) == 1:
        return values[0], Decimal("0")
    return values[0], values[1]


def _depth_range(value: str) -> tuple[int | None, int | None]:
    values = _numbers(value)
    if not values:
        return None, None
    if len(values) == 1:
        depth = int(values[0])
        return depth, depth
    return int(min(values[0], values[1])), int(max(values[0], values[1]))


def _numbers(value: str) -> list[Decimal]:
    numbers = []
    for raw_number in re.findall(r"\d+(?:[,.]\d+)?", value):
        try:
            numbers.append(Decimal(raw_number.replace(",", ".")))
        except InvalidOperation:
            continue
    return numbers


def _access_status(
    open_lifts: int,
    open_km: Decimal,
    trails: dict[str, TrailBreakdown],
) -> str:
    open_trails = sum(trail.open for trail in trails.values())
    total_trails = sum(trail.total for trail in trails.values())
    if open_lifts > 0 or open_km > 0 or open_trails > 0:
        return "Estacion abierta"
    if total_trails > 0:
        return "Estacion cerrada"
    return "Sin datos"


def _has_grandvalira_data(report: SnowReportData) -> bool:
    return any(
        [
            report.total_lifts,
            report.total_km,
            report.snow_depth_min_cm is not None,
            report.green_trails.total,
            report.blue_trails.total,
            report.red_trails.total,
            report.black_trails.total,
            report.access_status != "Sin datos",
        ]
    )


def _normalize_text(value: str) -> str:
    normalized = value.replace("–", "-").replace("—", "-")
    without_accents = unicodedata.normalize("NFKD", normalized)
    return "".join(
        char for char in without_accents if not unicodedata.combining(char)
    ).lower()
