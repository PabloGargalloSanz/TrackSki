from datetime import datetime
from decimal import Decimal

CRITICAL_SEVERITIES = {"critical", "high"}
CAUTION_SEVERITIES = {"medium", "low"}
DIRECT_ACCESS_ROLES = {"primary", "final_access"}
APPROACH_ACCESS_ROLES = {"approach"}
ACCESS_ROLE_PRIORITY = {
    "final_access": 1,
    "primary": 2,
    "approach": 3,
    "secondary": 4,
    "alternative": 5,
}
ROAD_CONDITION_STATUS_PRIORITY = {
    "closed": 1,
    "chains": 2,
    "affected": 3,
    "caution": 4,
    "unknown": 5,
}
SEVERITY_PRIORITY = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "unknown": 5,
}


def km_ranges_overlap(
    access_from_km: Decimal | None,
    access_to_km: Decimal | None,
    incident_start_km: Decimal | None,
    incident_end_km: Decimal | None,
) -> bool:
    if (
        access_from_km is None
        or access_to_km is None
        or incident_start_km is None
        or incident_end_km is None
    ):
        return True

    return access_from_km <= incident_end_km and incident_start_km <= access_to_km


def overall_access_status(incidents: list[dict]) -> str:
    if not incidents:
        return "open"

    if any(
        incident.get("incident_type") == "road_closed"
        and incident.get("severity") in CRITICAL_SEVERITIES
        and incident.get("access_role") in DIRECT_ACCESS_ROLES
        for incident in incidents
    ):
        return "closed"

    if any(
        incident.get("incident_type") == "chains_required"
        and incident.get("access_role") in DIRECT_ACCESS_ROLES
        for incident in incidents
    ):
        return "chains"

    if any(
        incident.get("incident_type") in {"road_closed", "chains_required"}
        and incident.get("severity") in CRITICAL_SEVERITIES
        and incident.get("access_role") in APPROACH_ACCESS_ROLES
        for incident in incidents
    ):
        return "affected"

    severities = {incident.get("severity") for incident in incidents}
    if severities & CRITICAL_SEVERITIES:
        return "affected"
    if severities & CAUTION_SEVERITIES:
        return "caution"

    return "unknown"


def most_relevant_access_role(access_roads: list[dict]) -> str | None:
    if not access_roads:
        return None

    return min(
        (access_road["access_role"] for access_road in access_roads),
        key=lambda access_role: ACCESS_ROLE_PRIORITY.get(access_role, 99),
    )


def road_condition_status_from_incidents(incidents: list[dict]) -> str | None:
    if not incidents:
        return None

    statuses = [_road_condition_status_from_incident(incident) for incident in incidents]
    return min(
        statuses,
        key=lambda status: ROAD_CONDITION_STATUS_PRIORITY.get(status, 99),
    )


def _road_condition_status_from_incident(incident: dict) -> str:
    incident_type = incident.get("incident_type")
    severity = incident.get("severity")

    if incident_type == "road_closed" and severity in CRITICAL_SEVERITIES:
        return "closed"
    if incident_type == "chains_required":
        return "chains"
    if incident_type in {
        "snow",
        "ice",
        "hail",
        "weather",
        "restriction",
        "roadworks",
        "accident",
        "congestion",
        "obstruction",
    }:
        return "affected" if severity in CRITICAL_SEVERITIES else "caution"
    if severity in CRITICAL_SEVERITIES:
        return "affected"
    if severity in CAUTION_SEVERITIES:
        return "caution"

    return "unknown"


def compact_roadwork_incidents(incidents: list[dict]) -> list[dict]:
    grouped: dict[tuple[int | None, str | None, str | None], list[dict]] = {}
    compacted = []

    for incident in incidents:
        if incident.get("incident_type") != "roadworks":
            compacted.append(incident)
            continue

        key = (
            incident.get("road_id"),
            _normalized_road_code(incident.get("road_code")),
            incident.get("access_role"),
        )
        grouped.setdefault(key, []).append(incident)

    for group in grouped.values():
        if len(group) == 1:
            compacted.append(group[0])
            continue

        compacted.append(_merge_roadwork_group(group))

    return sorted(
        compacted,
        key=lambda incident: (
            SEVERITY_PRIORITY.get(incident.get("severity"), 99),
            -_timestamp(incident.get("updated_at")),
            -(incident.get("id") or 0),
        ),
    )


def _merge_roadwork_group(incidents: list[dict]) -> dict:
    latest_incident = max(
        incidents,
        key=lambda incident: (
            incident.get("updated_at") is not None,
            incident.get("updated_at"),
            incident.get("id"),
        ),
    )
    merged = dict(latest_incident)
    road_code = latest_incident.get("road_code")
    start_km = _min_present(incident.get("start_km") for incident in incidents)
    end_km = _max_present(incident.get("end_km") for incident in incidents)
    severity = min(
        (incident.get("severity") for incident in incidents),
        key=lambda severity: SEVERITY_PRIORITY.get(severity, 99),
    )

    merged["start_km"] = start_km
    merged["end_km"] = end_km
    merged["severity"] = severity
    merged["title"] = f"Obras en {road_code}" if road_code else "Obras"
    merged["description"] = _build_roadwork_description(
        road_code,
        start_km,
        end_km,
        len(incidents),
    )
    merged["direction"] = _merged_direction(incidents)

    return merged


def _normalized_road_code(value: str | None) -> str | None:
    return value.upper() if value else None


def _min_present(values) -> Decimal | None:
    present_values = [value for value in values if value is not None]
    return min(present_values) if present_values else None


def _max_present(values) -> Decimal | None:
    present_values = [value for value in values if value is not None]
    return max(present_values) if present_values else None


def _build_roadwork_description(
    road_code: str | None,
    start_km: Decimal | None,
    end_km: Decimal | None,
    count: int,
) -> str:
    title = f"Obras en {road_code}" if road_code else "Obras"
    if start_km is None or end_km is None:
        return f"{title}. Agrupa {count} incidencias activas."
    if start_km == end_km:
        return f"{title}, km {start_km}. Agrupa {count} incidencias activas."
    return f"{title}, km {start_km}-{end_km}. Agrupa {count} incidencias activas."


def _merged_direction(incidents: list[dict]) -> str | None:
    directions = {
        incident.get("direction")
        for incident in incidents
        if incident.get("direction")
    }
    if not directions:
        return None
    if len(directions) == 1:
        return directions.pop()
    return "varios sentidos"


def _timestamp(value: datetime | None) -> float:
    return value.timestamp() if value else 0
