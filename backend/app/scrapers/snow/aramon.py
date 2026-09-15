from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re
import unicodedata
from zoneinfo import ZoneInfo

import httpx

from app.scrapers.snow.base import SnowScraperResort
from app.services.snow.models import SnowReportData


SOURCE = "aramon"
SPANISH_TIMEZONE = ZoneInfo("Europe/Madrid")

ARAMON_RESORTS = [
    SnowScraperResort(
        resort_id=0,
        name="Cerler",
        url="https://www.cerler.com/partes/parteNieve?prevision=0",
    ),
    SnowScraperResort(
        resort_id=0,
        name="Formigal",
        url="https://www.formigal-panticosa.com/partes/parteNieve?prevision=0",
    ),
    #SnowScraperResort(
        #resort_id=0,
        #name="Panticosa",
        #url="https://www.formigal-panticosa.com/partes/parteNieve?prevision=0",
    #),
    SnowScraperResort(
        resort_id=0,
        name="Valdelinares",
        url=(
            "https://www.javalambre-valdelinares.com/partes/parteNieve"
            "?prevision=0&estacion=4"
        ),
    ),
]


class AramonSnowScraper:
    source = SOURCE

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30)

    def get_current(self, resort: SnowScraperResort) -> SnowReportData:
        response = self.client.get(resort.url)
        response.raise_for_status()
        return parse_aramon_snow_report(response.text)

    def close(self) -> None:
        self.client.close()


def parse_aramon_snow_report(
    html: str,
    reported_at: datetime | None = None,
) -> SnowReportData:
    parser = _AramonSnowReportParser()
    parser.feed(html)

    items = {
        _normalize_text(item.title): item
        for item in parser.items
        if item.title
    }
    open_lifts, total_lifts = _find_int_pair(items, "remontes")
    open_km, total_km = _find_decimal_pair(items, "kilometros")
    snow_depth_min_cm, snow_depth_max_cm = _find_depth_range(items)
    avalanche_risk = _find_avalanche_risk(parser.footer_text)
    full_text = " ".join(parser.all_text)
    access_status = _find_access_status(full_text, has_snow_report_items=bool(items))
    parsed_reported_at = _find_reported_at(full_text)

    return SnowReportData(
        reported_at=reported_at or parsed_reported_at or datetime.now(timezone.utc),
        open_lifts=open_lifts,
        total_lifts=total_lifts,
        open_km=open_km,
        total_km=total_km,
        snow_depth_min_cm=snow_depth_min_cm,
        snow_depth_max_cm=snow_depth_max_cm,
        avalanche_risk=avalanche_risk,
        access_status=access_status,
        data_source=SOURCE,
        is_verified=True,
    )


class _SnowReportItem:
    def __init__(self) -> None:
        self.title = ""
        self.num = ""
        self.info = ""


class _AramonSnowReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[_SnowReportItem] = []
        self.footer_text: list[str] = []
        self.all_text: list[str] = []
        self._current_item: _SnowReportItem | None = None
        self._current_field: str | None = None
        self._in_footer_text = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        classes = _classes(attrs)

        if tag == "li" and "snow-report__item" in classes:
            self._current_item = _SnowReportItem()
            self.items.append(self._current_item)
            return

        if self._current_item:
            if "snow-report__title" in classes:
                self._current_field = "title"
            elif "snow-report__num" in classes:
                self._current_field = "num"
            elif "snow-report__info" in classes:
                self._current_field = "info"

        if "snow-report__footer-txt" in classes:
            self._in_footer_text = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self._current_item:
            self._current_item = None
            self._current_field = None
            return

        if tag in {"p", "span", "strong", "div"}:
            self._current_field = None
            self._in_footer_text = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return

        self.all_text.append(text)

        if self._current_item and self._current_field:
            current_value = getattr(self._current_item, self._current_field)
            setattr(
                self._current_item,
                self._current_field,
                f"{current_value} {text}".strip(),
            )
            return

        if self._in_footer_text:
            self.footer_text.append(text)


def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
    class_value = next((value for key, value in attrs if key == "class"), "") or ""
    return set(class_value.split())


def _normalize_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in without_accents if not unicodedata.combining(char)
    ).lower()


def _find_item(
    items: dict[str, _SnowReportItem],
    title_contains: str,
) -> _SnowReportItem | None:
    normalized_title = _normalize_text(title_contains)
    return next(
        (item for title, item in items.items() if normalized_title in title),
        None,
    )


def _find_int_pair(
    items: dict[str, _SnowReportItem],
    title_contains: str,
) -> tuple[int, int]:
    item = _find_item(items, title_contains)
    if not item:
        return 0, 0

    values = _extract_numbers(f"{item.num} {item.info}")
    if not values:
        return 0, 0
    if len(values) == 1:
        return int(values[0]), 0
    return int(values[0]), int(values[1])


def _find_decimal_pair(
    items: dict[str, _SnowReportItem],
    title_contains: str,
) -> tuple[Decimal, Decimal]:
    item = _find_item(items, title_contains)
    if not item:
        return Decimal("0"), Decimal("0")

    values = _extract_numbers(f"{item.num} {item.info}")
    if not values:
        return Decimal("0"), Decimal("0")
    if len(values) == 1:
        return values[0], Decimal("0")
    return values[0], values[1]


def _find_depth_range(items: dict[str, _SnowReportItem]) -> tuple[int | None, int | None]:
    item = _find_item(items, "espesor")
    if not item:
        return None, None

    values = _extract_numbers(f"{item.num} {item.info}")
    if not values:
        return None, None
    if len(values) == 1:
        depth = int(values[0])
        return depth, depth

    return int(min(values[0], values[1])), int(max(values[0], values[1]))


def _find_avalanche_risk(footer_text: list[str]) -> int | None:
    text = " ".join(footer_text)
    match = re.search(r"\b([1-5])\s*/\s*5\b", text)
    if match:
        return int(match.group(1))

    match = re.search(r"\b(?:riesgo|aludes?)\D*([1-5])\b", _normalize_text(text))
    if match:
        return int(match.group(1))

    return None


def _find_access_status(text: str, has_snow_report_items: bool) -> str | None:
    normalized_text = _normalize_text(text)
    if "estacion cerrada" in normalized_text or "fin de temporada" in normalized_text:
        return "Estacion cerrada"
    if "estacion abierta" in normalized_text:
        return "Estacion abierta"
    if not has_snow_report_items:
        return "Sin datos"
    return None


def _find_reported_at(text: str) -> datetime | None:
    normalized_text = _normalize_text(text)
    match = re.search(
        r"emitido a las\s+(\d{1,2}):(\d{2})\s+h\s+del\s+"
        r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})",
        normalized_text,
    )
    if not match:
        return None

    month = _spanish_month_to_number(match.group(4))
    if month is None:
        return None

    local_reported_at = datetime(
        int(match.group(5)),
        month,
        int(match.group(3)),
        int(match.group(1)),
        int(match.group(2)),
        tzinfo=SPANISH_TIMEZONE,
    )
    return local_reported_at.astimezone(timezone.utc)


def _spanish_month_to_number(month: str) -> int | None:
    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    return months.get(month)


def _extract_numbers(value: str) -> list[Decimal]:
    numbers = []
    for raw_number in re.findall(r"\d+(?:[,.]\d+)?", value):
        try:
            numbers.append(Decimal(raw_number.replace(",", ".")))
        except InvalidOperation:
            continue

    return numbers
