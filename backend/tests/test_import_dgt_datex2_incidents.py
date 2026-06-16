from decimal import Decimal
from unittest.mock import Mock, patch
import unittest

from app.jobs.import_dgt_datex2_incidents import save_dgt_incidents
from app.scrapers.dgt_datex2 import NormalizedRoadIncident


def make_incident(road_code: str | None = "A-136") -> NormalizedRoadIncident:
    return NormalizedRoadIncident(
        source="dgt_datex2_v37",
        source_id="record-1",
        road_code=road_code,
        title=None,
        description="Uso obligatorio de cadenas entre km 12 y 18",
        incident_type="chains_required",
        status="active",
        severity="high",
        start_km=Decimal("12"),
        end_km=Decimal("18"),
        direction=None,
        latitude=None,
        longitude=None,
        starts_at=None,
        ends_at=None,
        reported_at=None,
        updated_at=None,
        raw_payload={"source_id": "record-1"},
    )


class ImportDgtDatex2IncidentsTest(unittest.TestCase):
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_incident")
    @patch("app.jobs.import_dgt_datex2_incidents.get_best_road_id_by_code")
    def test_save_dgt_incidents_matches_road(
        self,
        get_best_road_id_by_code: Mock,
        upsert_road_incident: Mock,
    ) -> None:
        db = Mock()
        incident = make_incident()
        get_best_road_id_by_code.return_value = 7

        summary = save_dgt_incidents(db, [incident])

        self.assertEqual(summary.parsed, 1)
        self.assertEqual(summary.saved, 1)
        self.assertEqual(summary.skipped, 0)
        self.assertEqual(summary.roads_matched, 1)
        self.assertEqual(summary.roads_unmatched_skipped, 0)
        get_best_road_id_by_code.assert_called_once_with(db, "A-136")
        upsert_road_incident.assert_called_once_with(db, incident, road_id=7)

    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_incident")
    @patch("app.jobs.import_dgt_datex2_incidents.get_best_road_id_by_code")
    def test_save_dgt_incidents_skips_unmatched_road(
        self,
        get_best_road_id_by_code: Mock,
        upsert_road_incident: Mock,
    ) -> None:
        db = Mock()
        incident = make_incident()
        get_best_road_id_by_code.return_value = None

        summary = save_dgt_incidents(db, [incident])

        self.assertEqual(summary.parsed, 1)
        self.assertEqual(summary.saved, 0)
        self.assertEqual(summary.roads_matched, 0)
        self.assertEqual(summary.roads_unmatched_skipped, 1)
        upsert_road_incident.assert_not_called()

    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_incident")
    @patch("app.jobs.import_dgt_datex2_incidents.get_best_road_id_by_code")
    def test_save_dgt_incidents_without_road_code(
        self,
        get_best_road_id_by_code: Mock,
        upsert_road_incident: Mock,
    ) -> None:
        db = Mock()
        incident = make_incident(road_code=None)

        summary = save_dgt_incidents(db, [incident])

        self.assertEqual(summary.parsed, 1)
        self.assertEqual(summary.saved, 0)
        self.assertEqual(summary.skipped, 1)
        self.assertEqual(summary.roads_matched, 0)
        get_best_road_id_by_code.assert_not_called()
        upsert_road_incident.assert_not_called()


if __name__ == "__main__":
    unittest.main()
