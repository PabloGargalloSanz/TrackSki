from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
import re
import unicodedata
from typing import Any


SOURCE = "dgt_datex2_v37"

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
    if "obra" in text:
        return "roadworks"
    if "accidente" in text:
        return "accident"
    if "restric" in text or "limitacion" in text:
        return "restriction"
    if "retencion" in text or "congestion" in text:
        return "congestion"
    if "obstaculo" in text or "desprendimiento" in text:
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
