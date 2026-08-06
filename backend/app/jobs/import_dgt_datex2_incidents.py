from dataclasses import dataclass
from xml.etree.ElementTree import ParseError

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.roads import (
    get_best_road_id_by_code,
    upsert_road_condition_summary,
    upsert_road_incident,
)
from app.scrapers.dgt_datex2 import (
    NormalizedRoadIncident,
    download_datex2_xml,
    parse_datex2_incidents,
)
from app.services.road_access import road_condition_status_from_incidents


@dataclass
class ImportSummary:
    parsed: int = 0
    saved: int = 0
    skipped: int = 0
    roads_matched: int = 0
    roads_unmatched_skipped: int = 0
    road_conditions_updated: int = 0


def save_dgt_incidents(
    db,
    incidents: list[NormalizedRoadIncident],
) -> ImportSummary:
    summary = ImportSummary(parsed=len(incidents))
    incidents_by_road_id: dict[int, list[NormalizedRoadIncident]] = {}

    for incident in incidents:
        if not incident.source_id:
            summary.skipped += 1
            continue

        if not incident.road_code:
            summary.skipped += 1
            continue

        road_id = get_best_road_id_by_code(db, incident.road_code)
        if not road_id:
            summary.roads_unmatched_skipped += 1
            continue

        summary.roads_matched += 1
        upsert_road_incident(db, incident, road_id=road_id)
        incidents_by_road_id.setdefault(road_id, []).append(incident)
        summary.saved += 1

    for road_id, road_incidents in incidents_by_road_id.items():
        status = road_condition_status_from_incidents(
            [
                {
                    "incident_type": incident.incident_type,
                    "severity": incident.severity,
                }
                for incident in road_incidents
            ]
        )
        if not status:
            continue

        upsert_road_condition_summary(
            db,
            road_id=road_id,
            status=status,
            severity=_highest_severity(road_incidents),
            details=_build_condition_details(road_incidents),
            data_source="dgt_datex2_v37",
            source_updated_at=_latest_updated_at(road_incidents),
            raw_payload={
                "source": "dgt_datex2_v37",
                "source_ids": [incident.source_id for incident in road_incidents],
            },
        )
        summary.road_conditions_updated += 1

    return summary


def _highest_severity(incidents: list[NormalizedRoadIncident]) -> str:
    priority = {"critical": 1, "high": 2, "medium": 3, "low": 4, "unknown": 5}
    return min(
        (incident.severity for incident in incidents),
        key=lambda severity: priority.get(severity, 99),
    )


def _latest_updated_at(incidents: list[NormalizedRoadIncident]):
    dates = [incident.updated_at for incident in incidents if incident.updated_at]
    return max(dates) if dates else None


def _build_condition_details(incidents: list[NormalizedRoadIncident]) -> str:
    main_incident = min(
        incidents,
        key=lambda incident: {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
            "unknown": 5,
        }.get(incident.severity, 99),
    )
    description = main_incident.description or main_incident.incident_type
    return f"DGT DATEX2: {description}"


def main() -> int:
    result = run()
    print_job_result(result)
    return 0 if result.status == "success" else 1


def run() -> JobResult:
    try:
        xml_content = download_datex2_xml(
            url=settings.DGT_DATEX2_URL,
            timeout_seconds=settings.DGT_DATEX2_TIMEOUT_SECONDS,
        )
        incidents = parse_datex2_incidents(xml_content)
    except (httpx.HTTPError, ParseError, ValueError) as error:
        return JobResult.failed("DGT roads", error)

    db = SessionLocal()
    try:
        summary = save_dgt_incidents(db, incidents)
        db.commit()
    except Exception as error:
        db.rollback()
        return JobResult.failed("DGT roads", error)
    finally:
        db.close()

    return JobResult(
        job_name="DGT roads",
        processed=summary.parsed,
        inserted=summary.saved,
        updated=summary.road_conditions_updated,
        skipped=summary.skipped + summary.roads_unmatched_skipped,
        metadata={
            "roads_matched": summary.roads_matched,
            "roads_unmatched_skipped": summary.roads_unmatched_skipped,
            "source": "dgt_datex2_v37",
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
