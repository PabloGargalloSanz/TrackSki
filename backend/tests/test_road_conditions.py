from datetime import datetime, timezone
from unittest.mock import Mock
import unittest

from app.repositories.roads import create_road_condition


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


if __name__ == "__main__":
    unittest.main()
