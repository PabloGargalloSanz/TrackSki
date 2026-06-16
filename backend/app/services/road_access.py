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
