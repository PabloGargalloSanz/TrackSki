from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
import unittest

from app.repositories.roads import (
    create_road_condition,
    get_best_road_id_by_code,
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
        _, params = db.execute.call_args.args
        self.assertEqual(params["road_code"], "A-136")

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


if __name__ == "__main__":
    unittest.main()
