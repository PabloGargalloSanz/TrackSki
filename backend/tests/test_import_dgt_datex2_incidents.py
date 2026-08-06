from decimal import Decimal
from unittest.mock import Mock, patch
import unittest

from app.jobs.import_dgt_datex2_incidents import run, save_dgt_incidents
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
    @patch("app.jobs.import_dgt_datex2_incidents.mark_stale_dgt_incidents_resolved")
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_condition_summary")
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_incident")
    @patch("app.jobs.import_dgt_datex2_incidents.get_best_road_id_by_code")
    def test_save_dgt_incidents_matches_road(
        self,
        get_best_road_id_by_code: Mock,
        upsert_road_incident: Mock,
        upsert_road_condition_summary: Mock,
        mark_stale_dgt_incidents_resolved: Mock,
    ) -> None:
        db = Mock()
        incident = make_incident()
        get_best_road_id_by_code.return_value = 7
        mark_stale_dgt_incidents_resolved.return_value = 2

        summary = save_dgt_incidents(db, [incident])

        self.assertEqual(summary.parsed, 1)
        self.assertEqual(summary.saved, 1)
        self.assertEqual(summary.skipped, 0)
        self.assertEqual(summary.roads_matched, 1)
        self.assertEqual(summary.roads_unmatched_skipped, 0)
        self.assertEqual(summary.road_conditions_updated, 1)
        self.assertEqual(summary.resolved_missing, 2)
        get_best_road_id_by_code.assert_called_once_with(db, "A-136")
        upsert_road_incident.assert_called_once_with(db, incident, road_id=7)
        upsert_road_condition_summary.assert_called_once()
        mark_stale_dgt_incidents_resolved.assert_called_once_with(db, ["record-1"])

        _, kwargs = upsert_road_condition_summary.call_args
        self.assertEqual(kwargs["road_id"], 7)
        self.assertEqual(kwargs["status"], "chains")
        self.assertEqual(kwargs["severity"], "high")
        self.assertEqual(kwargs["data_source"], "dgt_datex2_v37")

    @patch("app.jobs.import_dgt_datex2_incidents.mark_stale_dgt_incidents_resolved")
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_condition_summary")
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_incident")
    @patch("app.jobs.import_dgt_datex2_incidents.get_best_road_id_by_code")
    def test_save_dgt_incidents_skips_unmatched_road(
        self,
        get_best_road_id_by_code: Mock,
        upsert_road_incident: Mock,
        upsert_road_condition_summary: Mock,
        mark_stale_dgt_incidents_resolved: Mock,
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
        upsert_road_condition_summary.assert_not_called()
        mark_stale_dgt_incidents_resolved.assert_called_once_with(db, ["record-1"])

    @patch("app.jobs.import_dgt_datex2_incidents.mark_stale_dgt_incidents_resolved")
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_condition_summary")
    @patch("app.jobs.import_dgt_datex2_incidents.upsert_road_incident")
    @patch("app.jobs.import_dgt_datex2_incidents.get_best_road_id_by_code")
    def test_save_dgt_incidents_without_road_code(
        self,
        get_best_road_id_by_code: Mock,
        upsert_road_incident: Mock,
        upsert_road_condition_summary: Mock,
        mark_stale_dgt_incidents_resolved: Mock,
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
        upsert_road_condition_summary.assert_not_called()
        mark_stale_dgt_incidents_resolved.assert_called_once_with(db, ["record-1"])

    @patch("app.jobs.import_dgt_datex2_incidents.SessionLocal")
    @patch("app.jobs.import_dgt_datex2_incidents.save_dgt_incidents")
    @patch("app.jobs.import_dgt_datex2_incidents.parse_datex2_incidents")
    @patch("app.jobs.import_dgt_datex2_incidents.download_datex2_xml")
    def test_run_reports_saved_incidents_without_claiming_inserts(
        self,
        download_datex2_xml: Mock,
        parse_datex2_incidents: Mock,
        save_dgt_incidents_mock: Mock,
        session_local: Mock,
    ) -> None:
        db = Mock()
        session_local.return_value = db
        download_datex2_xml.return_value = b"<xml />"
        parse_datex2_incidents.return_value = []
        save_dgt_incidents_mock.return_value.parsed = 10
        save_dgt_incidents_mock.return_value.saved = 3
        save_dgt_incidents_mock.return_value.skipped = 2
        save_dgt_incidents_mock.return_value.roads_matched = 3
        save_dgt_incidents_mock.return_value.roads_unmatched_skipped = 5
        save_dgt_incidents_mock.return_value.road_conditions_updated = 1
        save_dgt_incidents_mock.return_value.resolved_missing = 2

        result = run()

        self.assertEqual(result.status, "success")
        self.assertEqual(result.processed, 10)
        self.assertEqual(result.inserted, 0)
        self.assertEqual(result.updated, 1)
        self.assertEqual(result.skipped, 7)
        self.assertEqual(result.metadata["saved"], 3)
        self.assertEqual(result.metadata["resolved_missing"], 2)
        self.assertIn("Guardadas 3 incidencias", result.message)
        self.assertIn("Cerradas 2 ausentes", result.message)
        db.commit.assert_called_once()
        db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
