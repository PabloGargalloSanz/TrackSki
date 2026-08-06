from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
import httpx
import re
import unicodedata
from typing import Any
from xml.etree import ElementTree


SOURCE = "dgt_datex2_v37"
DEFAULT_DATEX2_URL = (
    "https://nap.dgt.es/datex2/v3/dgt/SituationPublication/datex2_v37.xml"
)

ROAD_CODE_PATTERN = re.compile(
    r"\b(AP|A|N|M|C|B|GI|L|T|V|CV|CM|CL|EX|GR|H|HU|LE|LO|LU|MA|NA|O|OU|P|PO|"
    r"SA|SE|SG|SO|TE|TO|VA|ZA)-?\d{1,4}[A-Z]?\b",
    re.IGNORECASE,
)
KM_RANGE_PATTERN = re.compile(
    r"(?:km|p\.?k\.?|punto kilometrico)\s*"
    r"(\d+(?:[,.]\d+)?)"
    r"(?:\s*(?:-|al|a|hasta|y)\s*(\d+(?:[,.]\d+)?))?",
    re.IGNORECASE,
)
DATEX2_POINT_PATTERN = re.compile(
    r"nonLinkedPoint\s+(-?\d+(?:[,.]\d+)?)\s+(-?\d+(?:[,.]\d+)?)",
    re.IGNORECASE,
)
DIRECTION_PATTERN = re.compile(
    r"\b(?:AP|A|N|M|C|B|GI|L|T|V|CV|CM|CL|EX|GR|H|HU|LE|LO|LU|MA|NA|O|OU|P|PO|"
    r"SA|SE|SG|SO|TE|TO|VA|ZA)-?\d{1,4}[A-Z]?\s+([a-z]+Bound)\b",
    re.IGNORECASE,
)
ISO_DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
TECHNICAL_DESCRIPTION_TERMS = {
    "certain",
    "dgt3.0",
    "nonlinkedpoint",
    "positive",
    "negative",
    "vehicleobstruction",
    "vehiclestuck",
}
INCIDENT_TITLES = {
    "road_closed": "Carretera cortada",
    "chains_required": "Cadenas obligatorias",
    "snow": "Nieve en la calzada",
    "ice": "Hielo en la calzada",
    "roadworks": "Obras",
    "accident": "Accidente",
    "restriction": "Restriccion",
    "congestion": "Retencion",
    "obstruction": "Obstaculo en la calzada",
    "weather": "Incidencia meteorologica",
}


@dataclass(frozen=True)
class NormalizedRoadIncident:
    source: str
    source_id: str
    road_code: str | None
    title: str | None
    description: str | None
    incident_type: str
    status: str
    severity: str
    start_km: Decimal | None
    end_km: Decimal | None
    direction: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    starts_at: datetime | None
    ends_at: datetime | None
    reported_at: datetime | None
    updated_at: datetime | None
    raw_payload: dict[str, Any]


def download_datex2_xml(
    url: str = DEFAULT_DATEX2_URL,
    timeout_seconds: int = 30,
) -> bytes:
    response = httpx.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.content


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    without_accents = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in without_accents if not unicodedata.combining(char)
    ).lower()


def extract_road_code(text: str | None) -> str | None:
    if not text:
        return None

    match = ROAD_CODE_PATTERN.search(text)
    if not match:
        return None

    return match.group(0).replace(" ", "").upper()


def _to_decimal(value: str) -> Decimal:
    return Decimal(value.replace(",", "."))


def extract_km_range(text: str | None) -> tuple[Decimal | None, Decimal | None]:
    if not text:
        return None, None

    match = KM_RANGE_PATTERN.search(normalize_text(text))
    if not match:
        return None, None

    start_km = _to_decimal(match.group(1))
    end_km = _to_decimal(match.group(2)) if match.group(2) else start_km

    if start_km > end_km:
        return end_km, start_km

    return start_km, end_km


def extract_datex2_point(text: str | None) -> tuple[Decimal | None, Decimal | None]:
    if not text:
        return None, None

    match = DATEX2_POINT_PATTERN.search(text)
    if not match:
        return None, None

    return _to_decimal(match.group(1)), _to_decimal(match.group(2))


def extract_datex2_km(text: str | None) -> tuple[Decimal | None, Decimal | None]:
    if not text:
        return None, None

    _, longitude = extract_datex2_point(text)
    if longitude is None:
        return None, None

    after_point = text.split(str(longitude), 1)[-1]
    match = re.search(r"\b(\d{1,4}(?:[,.]\d{1,3}))\b", after_point)
    if not match:
        return None, None

    km = _to_decimal(match.group(1))
    return km, km


def extract_direction(text: str | None) -> str | None:
    if not text:
        return None

    match = DIRECTION_PATTERN.search(text)
    if not match:
        return None

    return match.group(1)


def normalize_incident_type(
    raw_type: str | None,
    description: str | None,
) -> str:
    text = normalize_text(f"{raw_type or ''} {description or ''}")

    if any(term in text for term in ("carretera cortada", "corte total", "cerrado")):
        return "road_closed"
    if "cadena" in text:
        return "chains_required"
    if "nieve" in text or "nevada" in text:
        return "snow"
    if "hielo" in text or "helada" in text:
        return "ice"
    if "obra" in text or "roadworks" in text:
        return "roadworks"
    if "accidente" in text or "accident" in text:
        return "accident"
    if "restric" in text or "limitacion" in text:
        return "restriction"
    if "retencion" in text or "congestion" in text:
        return "congestion"
    if any(
        term in text
        for term in (
            "obstaculo",
            "desprendimiento",
            "obstruction",
            "objectontheroad",
        )
    ):
        return "obstruction"
    if any(term in text for term in ("meteorolog", "viento", "lluvia")):
        return "weather"
    if text.strip():
        return "other"

    return "unknown"


def normalize_status(raw_status: str | None) -> str:
    text = normalize_text(raw_status)

    if any(term in text for term in ("active", "activo", "en vigor", "vigente")):
        return "active"
    if any(term in text for term in ("planned", "previsto", "planificado")):
        return "planned"
    if any(term in text for term in ("resolved", "finalizado", "terminado", "resuelto")):
        return "resolved"

    return "unknown"


def normalize_severity(
    raw_severity: str | None,
    incident_type: str,
    description: str | None,
) -> str:
    text = normalize_text(f"{raw_severity or ''} {description or ''}")

    if any(term in text for term in ("critical", "critico", "muy grave")):
        return "critical"
    if any(term in text for term in ("high", "alto", "grave")):
        return "high"
    if any(term in text for term in ("medium", "medio", "moderado")):
        return "medium"
    if any(term in text for term in ("low", "bajo", "leve")):
        return "low"

    if incident_type == "road_closed":
        return "critical"
    if incident_type in {"chains_required", "ice"}:
        return "high"
    if incident_type in {"snow", "roadworks", "restriction", "accident"}:
        return "medium"
    if incident_type in {"congestion", "obstruction", "weather"}:
        return "low"

    return "unknown"


def make_stable_source_id(
    road_code: str | None,
    description: str | None,
    starts_at: datetime | None,
) -> str:
    base = "|".join(
        [
            road_code or "",
            description or "",
            starts_at.isoformat() if starts_at else "",
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def build_fallback_title(incident_type: str, road_code: str | None) -> str | None:
    title = INCIDENT_TITLES.get(incident_type)
    if not title:
        return None
    if road_code:
        return f"{title} en {road_code}"
    return title


def build_fallback_description(
    incident_type: str,
    road_code: str | None,
    start_km: Decimal | None,
    end_km: Decimal | None,
    direction: str | None,
) -> str | None:
    title = build_fallback_title(incident_type, road_code)
    if not title:
        return None

    parts = [title]
    if start_km is not None and end_km is not None:
        if start_km == end_km:
            parts.append(f"km {start_km}")
        else:
            parts.append(f"km {start_km}-{end_km}")
    if direction:
        parts.append(f"sentido {direction}")

    return ", ".join(parts)


def parse_datex2_incidents(xml_content: str | bytes) -> list[NormalizedRoadIncident]:
    root = ElementTree.fromstring(xml_content)
    incidents = []

    for record in _find_situation_records(root):
        description = _extract_description(record)
        search_text = _extract_search_text(record)
        raw_type = _extract_raw_type(record)
        incident_type = normalize_incident_type(
            raw_type,
            f"{description or ''} {search_text}",
        )
        status = normalize_status(
            _find_first_text(
                record,
                {"validityStatus", "situationRecordStatus", "lifeCycleManagement"},
            )
        )
        severity = normalize_severity(
            _find_first_text(record, {"severity", "trafficConstrictionType"}),
            incident_type,
            description,
        )
        road_code = extract_road_code(f"{description or ''} {search_text}")
        start_km, end_km = extract_km_range(f"{description or ''} {search_text}")
        if start_km is None or end_km is None:
            start_km, end_km = extract_datex2_km(search_text)
        starts_at = _parse_datetime(
            _find_first_text(record, {"overallStartTime", "validityStartTime"})
        )
        ends_at = _parse_datetime(
            _find_first_text(record, {"overallEndTime", "validityEndTime"})
        )
        reported_at = _parse_datetime(
            _find_first_text(record, {"situationRecordCreationTime", "publicationTime"})
        )
        updated_at = _parse_datetime(
            _find_first_text(record, {"situationRecordVersionTime", "publicationTime"})
        )
        direction = (
            _find_first_text(record, {"direction", "directionBound"})
            or extract_direction(search_text)
        )
        latitude = _parse_decimal(_find_first_text(record, {"latitude"}))
        longitude = _parse_decimal(_find_first_text(record, {"longitude"}))
        if latitude is None or longitude is None:
            latitude, longitude = extract_datex2_point(search_text)
        title = _find_first_text(record, {"situationRecordName", "headline"})
        if not title:
            title = build_fallback_title(incident_type, road_code)
        if description is None:
            description = build_fallback_description(
                incident_type,
                road_code,
                start_km,
                end_km,
                direction,
            )
        source_id = (
            record.attrib.get("id")
            or record.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
            or make_stable_source_id(road_code, description, starts_at)
        )

        incidents.append(
            NormalizedRoadIncident(
                source=SOURCE,
                source_id=source_id,
                road_code=road_code,
                title=title,
                description=description,
                incident_type=incident_type,
                status=status,
                severity=severity,
                start_km=start_km,
                end_km=end_km,
                direction=direction,
                latitude=latitude,
                longitude=longitude,
                starts_at=starts_at,
                ends_at=ends_at,
                reported_at=reported_at,
                updated_at=updated_at,
                raw_payload={
                    "source_id": source_id,
                    "raw_type": raw_type,
                    "text": description,
                    "search_text": search_text,
                },
            )
        )

    return incidents


def _find_situation_records(root: ElementTree.Element) -> list[ElementTree.Element]:
    records = [
        element
        for element in root.iter()
        if _local_name(element.tag).endswith("SituationRecord")
        or _local_name(element.tag) == "situationRecord"
    ]
    if records:
        return records

    return [
        element
        for element in root.iter()
        if _local_name(element.tag).lower() == "situation"
    ]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_first_text(
    element: ElementTree.Element,
    names: set[str],
) -> str | None:
    normalized_names = {name.lower() for name in names}
    for child in element.iter():
        if _local_name(child.tag).lower() in normalized_names and child.text:
            text = child.text.strip()
            if text:
                return text

    return None


def _extract_description(element: ElementTree.Element) -> str | None:
    preferred = _find_first_text(
        element,
        {"value", "comment", "description", "situationRecordDescription"},
    )
    if preferred and _looks_like_public_description(preferred):
        return preferred

    return None


def _looks_like_public_description(value: str) -> bool:
    text = normalize_text(value)
    if not text:
        return False

    if len(ISO_DATETIME_PATTERN.findall(value)) >= 2:
        return False

    technical_matches = {
        term for term in TECHNICAL_DESCRIPTION_TERMS if term in text
    }
    if len(technical_matches) >= 2:
        return False

    return True


def _extract_search_text(element: ElementTree.Element) -> str:
    text_parts = [
        child.text.strip()
        for child in element.iter()
        if child.text and child.text.strip()
    ]
    return " ".join(text_parts)


def _extract_raw_type(element: ElementTree.Element) -> str | None:
    xsi_type = next(
        (
            value
            for key, value in element.attrib.items()
            if _local_name(key).lower() == "type"
        ),
        None,
    )
    return xsi_type or _local_name(element.tag)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None

    try:
        return _to_decimal(value)
    except Exception:
        return None
