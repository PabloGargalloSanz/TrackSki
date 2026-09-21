from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re
import unicodedata

import httpx

from app.scrapers.snow.base import SnowScraperResort
from app.services.snow.models import SnowReportData, TrailBreakdown


SOURCE = "astun_candanchu"
SNOW_REPORT_URL = "https://tienda.astuncandanchu.com/partenieve/pistas"

ASTUN_CANDANCHU_RESORTS = [
    SnowScraperResort(resort_id=0, name="Astún", url=SNOW_REPORT_URL),
    SnowScraperResort(resort_id=0, name="Candanchú", url=SNOW_REPORT_URL),
]


RESORT_FIELDS = {
    "Astún": {
        "open_lifts": "1_LabDatoRemontesR",
        "open_km": "1_lblMovilKm",
        "snow_depth_min_cm": "1_lblMovilEspesorMin",
        "snow_depth_max_cm": "1_lblMovilEspesorMax",
        "avalanche_risk": "1_lblMovilRiesgo",
        "access_status": "1_lblMovilAccesos",
        "green_trails": "RepPistasVerdes",
        "blue_trails": "RepPistasAzules",
        "red_trails": "RepPistasRojas",
        "black_trails": "RepPistasNegras",
    },
    "Candanchú": {
        "open_lifts": "1_LabDatoRemontesRCan",
        "open_km": "1_lblMovilKmCan",
        "snow_depth_min_cm": "1_lblMovilEspesorMinCan",
        "snow_depth_max_cm": "1_lblMovilEspesorMaxCan",
        "avalanche_risk": "1_lblMovilRiesgoCan",
        "access_status": "1_lblMovilAccesosCan",
        "green_trails": "RepPistasVerdesCan",
        "blue_trails": "RepPistasAzulesCan",
        "red_trails": "RepPistasRojasCan",
        "black_trails": "RepPistasNegrasCan",
    },
}


class AstunCandanchuSnowScraper:
    source = SOURCE

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30)

    def get_current(self, resort: SnowScraperResort) -> SnowReportData:
        response = self.client.get(resort.url)
        response.raise_for_status()
        return parse_astun_candanchu_snow_report(response.text, resort.name)

    def close(self) -> None:
        self.client.close()


def parse_astun_candanchu_snow_report(
    html: str,
    resort_name: str,
    reported_at: datetime | None = None,
) -> SnowReportData:
    fields = RESORT_FIELDS.get(resort_name)
    if not fields:
        raise ValueError(f"Estacion no soportada por {SOURCE}: {resort_name}")

    parser = _AstunCandanchuParser()
    parser.feed(html)

    open_lifts, total_lifts = _find_int_pair(parser.text_by_id, fields["open_lifts"])
    open_km, total_km = _find_decimal_pair(parser.text_by_id, fields["open_km"])
    access_status = _find_text(parser.text_by_id, fields["access_status"])
    full_text = " ".join(parser.all_text)

    if not access_status:
        access_status = _find_access_status(full_text, has_known_fields=bool(parser.text_by_id))

    if _is_closed(access_status):
        return SnowReportData(
            reported_at=reported_at or datetime.now(timezone.utc),
            access_status="Estacion cerrada",
            data_source=SOURCE,
            is_verified=True,
        )

    return SnowReportData(
        reported_at=reported_at or datetime.now(timezone.utc),
        open_lifts=open_lifts,
        total_lifts=total_lifts,
        open_km=open_km,
        total_km=total_km,
        snow_depth_min_cm=_find_int(parser.text_by_id, fields["snow_depth_min_cm"]),
        snow_depth_max_cm=_find_int(parser.text_by_id, fields["snow_depth_max_cm"]),
        avalanche_risk=_find_int(parser.text_by_id, fields["avalanche_risk"]),
        access_status=access_status,
        green_trails=parser.trail_breakdown(fields["green_trails"]),
        blue_trails=parser.trail_breakdown(fields["blue_trails"]),
        red_trails=parser.trail_breakdown(fields["red_trails"]),
        black_trails=parser.trail_breakdown(fields["black_trails"]),
        data_source=SOURCE,
        is_verified=True,
    )


class _TrailRow:
    def __init__(self, table_id: str) -> None:
        self.table_id = table_id
        self.text: list[str] = []
        self.is_open = False
        self.has_data_cell = False


class _AstunCandanchuParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_by_id: dict[str, str] = {}
        self.all_text: list[str] = []
        self.trail_rows: dict[str, list[_TrailRow]] = {}
        self._id_stack: list[str | None] = []
        self._table_stack: list[str] = []
        self._current_row: _TrailRow | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in {"br", "img", "input", "meta", "link"}:
            return

        attrs_by_name = {key: value or "" for key, value in attrs}
        element_id = attrs_by_name.get("id")
        classes = set(attrs_by_name.get("class", "").split())

        if element_id:
            self._id_stack.append(element_id)
            if tag == "table":
                self._table_stack.append(element_id)
        else:
            self._id_stack.append(None)

        if tag == "tr" and self._table_stack:
            self._current_row = _TrailRow(self._table_stack[-1])

        if tag == "td" and self._current_row:
            self._current_row.has_data_cell = True

        if self._current_row and classes.intersection({"estado_abierto", "text-success"}):
            self._current_row.is_open = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._current_row:
            if self._current_row.has_data_cell and " ".join(self._current_row.text).strip():
                self.trail_rows.setdefault(self._current_row.table_id, []).append(
                    self._current_row
                )
            self._current_row = None

        if tag == "table" and self._table_stack:
            self._table_stack.pop()

        if tag not in {"br", "img", "input", "meta", "link"} and self._id_stack:
            self._id_stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return

        self.all_text.append(text)

        for element_id in self._id_stack:
            if not element_id:
                continue
            current_text = self.text_by_id.get(element_id, "")
            self.text_by_id[element_id] = f"{current_text} {text}".strip()

        if self._current_row:
            self._current_row.text.append(text)

    def trail_breakdown(self, table_id: str) -> TrailBreakdown:
        rows = self._rows_for_table(table_id)
        return TrailBreakdown(
            open=sum(1 for row in rows if row.is_open),
            total=len(rows),
        )

    def _rows_for_table(self, table_id: str) -> list[_TrailRow]:
        normalized_table_id = _normalize_text(table_id)
        return [
            row
            for stored_table_id, rows in self.trail_rows.items()
            if _normalize_text(stored_table_id).endswith(normalized_table_id)
            for row in rows
        ]


def _find_text(text_by_id: dict[str, str], target_id: str) -> str | None:
    value = _find_value(text_by_id, target_id)
    if not value:
        return None
    return value.strip()


def _find_int(text_by_id: dict[str, str], target_id: str) -> int | None:
    values = _extract_numbers(_find_value(text_by_id, target_id) or "")
    if not values:
        return None
    return int(values[0])


def _find_int_pair(
    text_by_id: dict[str, str],
    target_id: str,
) -> tuple[int, int]:
    values = _extract_numbers(_find_value(text_by_id, target_id) or "")
    if not values:
        return 0, 0
    if len(values) == 1:
        return int(values[0]), 0
    return int(values[0]), int(values[1])


def _find_decimal_pair(
    text_by_id: dict[str, str],
    target_id: str,
) -> tuple[Decimal, Decimal]:
    values = _extract_numbers(_find_value(text_by_id, target_id) or "")
    if not values:
        return Decimal("0"), Decimal("0")
    if len(values) == 1:
        return values[0], Decimal("0")
    return values[0], values[1]


def _find_value(text_by_id: dict[str, str], target_id: str) -> str | None:
    normalized_target = _normalize_text(target_id)
    for element_id, value in text_by_id.items():
        if _normalize_text(element_id).endswith(normalized_target):
            return value
    return None


def _find_access_status(text: str, has_known_fields: bool) -> str:
    normalized_text = _normalize_text(text)
    if "estacion cerrada" in normalized_text or "fin de temporada" in normalized_text:
        return "Estacion cerrada"
    if "estacion abierta" in normalized_text:
        return "Estacion abierta"
    if not has_known_fields:
        return "Sin datos"
    return "Sin datos"


def _is_closed(access_status: str | None) -> bool:
    return bool(access_status and "estacion cerrada" in _normalize_text(access_status))


def _normalize_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in without_accents if not unicodedata.combining(char)
    ).lower()


def _extract_numbers(value: str) -> list[Decimal]:
    numbers = []
    for raw_number in re.findall(r"\d+(?:[,.]\d+)?", value):
        try:
            numbers.append(Decimal(raw_number.replace(",", ".")))
        except InvalidOperation:
            continue
    return numbers
