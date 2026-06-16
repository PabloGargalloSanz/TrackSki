from decimal import Decimal

CRITICAL_SEVERITIES = {"critical", "high"}
CAUTION_SEVERITIES = {"medium", "low"}


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

    severities = {incident["severity"] for incident in incidents}
    if severities & CRITICAL_SEVERITIES:
        return "affected"
    if severities & CAUTION_SEVERITIES:
        return "caution"

    return "unknown"
