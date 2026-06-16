import sys
from dataclasses import dataclass
from xml.etree.ElementTree import ParseError

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.roads import get_best_road_id_by_code, upsert_road_incident
from app.scrapers.dgt_datex2 import (
    NormalizedRoadIncident,
    download_datex2_xml,
    parse_datex2_incidents,
)


@dataclass
class ImportSummary:
    parsed: int = 0
    saved: int = 0
    skipped: int = 0
    roads_matched: int = 0
    roads_unmatched: int = 0


def save_dgt_incidents(
    db,
    incidents: list[NormalizedRoadIncident],
) -> ImportSummary:
    summary = ImportSummary(parsed=len(incidents))

    for incident in incidents:
        if not incident.source_id:
            summary.skipped += 1
            continue

        road_id = None
        if incident.road_code:
            road_id = get_best_road_id_by_code(db, incident.road_code)

        if road_id:
            summary.roads_matched += 1
        else:
            summary.roads_unmatched += 1

        upsert_road_incident(db, incident, road_id=road_id)
        summary.saved += 1

    return summary


def main() -> int:
    try:
        xml_content = download_datex2_xml(
            url=settings.DGT_DATEX2_URL,
            timeout_seconds=settings.DGT_DATEX2_TIMEOUT_SECONDS,
        )
        incidents = parse_datex2_incidents(xml_content)
    except (httpx.HTTPError, ParseError, ValueError) as error:
        print(f"ERROR: no se pudieron obtener incidencias DGT: {error}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        summary = save_dgt_incidents(db, incidents)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(
        "OK DGT DATEX2: "
        f"parsed={summary.parsed}, "
        f"saved={summary.saved}, "
        f"skipped={summary.skipped}, "
        f"roads_matched={summary.roads_matched}, "
        f"roads_unmatched={summary.roads_unmatched}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
