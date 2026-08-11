from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
import unittest

from app.repositories.roads import (
    create_road_condition,
    get_active_road_incidents_for_road_ids,
    get_access_roads_by_resort_id,
    get_best_road_id_by_code,
    mark_stale_dgt_incidents_resolved,
    upsert_road_condition_summary,
    upsert_road_incident,
)
from app.scrapers.dgt_datex2 import NormalizedRoadIncident


class RoadConditionRepositoryTest(unittest.TestCase):
    def test_create_road_condition_returns_inserted_id(self) -> None:
        db = Mock()
        result = Mock()
        result.scalar_one.return_value = 123
        db.execute.return_value = result
        reported_at = datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc)

        inserted_id = create_road_condition(
            db,
            road_id=3,
            status="chains",
            severity="medium",
            details="Cadenas recomendadas en el acceso",
            data_source="manual_test",
            is_verified=False,
            raw_payload={"source": "test"},
            reported_at=reported_at,
        )

        self.assertEqual(inserted_id, 123)

        _, params = db.execute.call_args.args
        self.assertEqual(params["road_id"], 3)
        self.assertEqual(params["status"], "chains")
        self.assertEqual(params["severity"], "medium")
        self.assertEqual(params["details"], "Cadenas recomendadas en el acceso")
        self.assertEqual(params["data_source"], "manual_test")
        self.assertEqual(params["raw_payload"], '{"source": "test"}')
        self.assertEqual(params["reported_at"], reported_at)

    def test_get_best_road_id_by_code_returns_matching_id(self) -> None:
        db = Mock()
        result = Mock()
        result.scalar_one_or_none.return_value = 7
        db.execute.return_value = result

        road_id = get_best_road_id_by_code(db, "A-136")

        self.assertEqual(road_id, 7)
        statement, params = db.execute.call_args.args
        self.assertIn("UPPER(code) = UPPER(:road_code)", str(statement))
        self.assertEqual(params["road_code"], "A-136")

    def test_get_active_road_incidents_for_access_filters_noise(self) -> None:
        db = Mock()
        result = Mock()
        result.mappings.return_value = []
        db.execute.return_value = result

        incidents = get_active_road_incidents_for_road_ids(db, [1, 2], limit=30)

        self.assertEqual(incidents, [])
        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("status IN ('active', 'planned')", sql)
        self.assertIn("severity = 'unknown'", sql)
        self.assertIn("incident_type IN ('unknown', 'other')", sql)
        self.assertIn("LIMIT :limit", sql)
        self.assertEqual(params["road_ids"], [1, 2])
        self.assertEqual(params["limit"], 30)

    def test_mark_stale_dgt_incidents_resolved_returns_updated_count(self) -> None:
        db = Mock()
        result = Mock()
        result.fetchall.return_value = [(1,), (2,)]
        db.execute.return_value = result

        updated = mark_stale_dgt_incidents_resolved(db, ["record-1", "record-2"])

        self.assertEqual(updated, 2)
        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("UPDATE road_incidents", sql)
        self.assertIn("status = 'resolved'", sql)
        self.assertIn("source_id NOT IN", sql)
        self.assertEqual(params["current_source_ids"], ["record-1", "record-2"])

    def test_mark_stale_dgt_incidents_resolved_skips_empty_source_ids(self) -> None:
        db = Mock()

        updated = mark_stale_dgt_incidents_resolved(db, [])

        self.assertEqual(updated, 0)
        db.execute.assert_not_called()

    def test_upsert_road_incident_returns_saved_id(self) -> None:
        db = Mock()
        result = Mock()
        result.scalar_one.return_value = 456
        db.execute.return_value = result
        updated_at = datetime(2026, 1, 15, 10, 5, tzinfo=timezone.utc)
        incident = NormalizedRoadIncident(
            source="dgt_datex2_v37",
            source_id="record-1",
            road_code="A-136",
            title=None,
            description="Uso obligatorio de cadenas entre km 12 y 18",
            incident_type="chains_required",
            status="active",
            severity="high",
            start_km=Decimal("12"),
            end_km=Decimal("18"),
            direction="ambos sentidos",
            latitude=Decimal("42.7753"),
            longitude=Decimal("-0.3632"),
            starts_at=None,
            ends_at=None,
            reported_at=None,
            updated_at=updated_at,
            raw_payload={"source_id": "record-1"},
        )

        incident_id = upsert_road_incident(db, incident, road_id=7)

        self.assertEqual(incident_id, 456)

        _, params = db.execute.call_args.args
        self.assertEqual(params["road_id"], 7)
        self.assertEqual(params["source"], "dgt_datex2_v37")
        self.assertEqual(params["source_id"], "record-1")
        self.assertEqual(params["road_code"], "A-136")
        self.assertEqual(params["incident_type"], "chains_required")
        self.assertEqual(params["severity"], "high")
        self.assertEqual(params["latitude"], Decimal("42.7753"))
        self.assertEqual(params["longitude"], Decimal("-0.3632"))
        self.assertEqual(params["updated_at"], updated_at)
        self.assertEqual(params["raw_payload"], '{"source_id": "record-1"}')

    def test_upsert_road_condition_summary_keeps_history(self) -> None:
        db = Mock()
        result = Mock()
        result.scalar_one.return_value = 789
        db.execute.return_value = result
        source_updated_at = datetime(2026, 1, 15, 10, 5, tzinfo=timezone.utc)

        condition_id = upsert_road_condition_summary(
            db,
            road_id=7,
            status="chains",
            severity="high",
            details="DGT DATEX2: cadenas",
            data_source="dgt_datex2_v37",
            source_updated_at=source_updated_at,
            raw_payload={"source_ids": ["record-1"]},
        )

        self.assertEqual(condition_id, 789)

        _, params = db.execute.call_args.args
        statement = str(db.execute.call_args.args[0])
        self.assertIn("INSERT INTO road_conditions", statement)
        self.assertNotIn("UPDATE road_conditions", statement)
        self.assertIn("CAST(:status AS VARCHAR(50))", statement)
        self.assertIn("CAST(:details AS TEXT)", statement)
        self.assertIn("CAST(:source_updated_at AS TIMESTAMP WITH TIME ZONE)", statement)
        self.assertEqual(params["road_id"], 7)
        self.assertEqual(params["status"], "chains")
        self.assertEqual(params["severity"], "high")
        self.assertEqual(params["details"], "DGT DATEX2: cadenas")
        self.assertEqual(params["data_source"], "dgt_datex2_v37")
        self.assertEqual(params["source_updated_at"], source_updated_at)
        self.assertEqual(params["raw_payload"], '{"source_ids": ["record-1"]}')

    def test_upsert_road_incident_uses_canonical_road_code_when_road_id_exists(
        self,
    ) -> None:
        db = Mock()
        result = Mock()
        result.scalar_one.return_value = 456
        db.execute.return_value = result
        incident = NormalizedRoadIncident(
            source="dgt_datex2_v37",
            source_id="record-n260a",
            road_code="N-260A",
            title="Obras en N-260A",
            description="Obras en N-260A",
            incident_type="roadworks",
            status="active",
            severity="medium",
            start_km=None,
            end_km=None,
            direction=None,
            latitude=None,
            longitude=None,
            starts_at=None,
            ends_at=None,
            reported_at=None,
            updated_at=None,
            raw_payload={"source_id": "record-n260a"},
        )

        upsert_road_incident(db, incident, road_id=7)

        statement = str(db.execute.call_args.args[0])
        self.assertIn("SELECT code FROM roads WHERE id = :road_id", statement)

    def test_get_access_roads_orders_by_access_role_priority(self) -> None:
        db = Mock()
        result = Mock()
        result.mappings.return_value = []
        db.execute.return_value = result

        get_access_roads_by_resort_id(db, 1, include_route=False)

        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("WHEN 'final_access' THEN 1", sql)
        self.assertIn("WHEN 'primary' THEN 2", sql)
        self.assertIn("WHEN 'approach' THEN 3", sql)
        self.assertIn("resort_access_roads.priority", sql)
        self.assertEqual(params["resort_id"], 1)


if __name__ == "__main__":
    unittest.main()
