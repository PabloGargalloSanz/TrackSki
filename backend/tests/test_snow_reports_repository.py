from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
import unittest

from app.repositories.snow_reports import create_snow_report_if_missing
from app.services.snow.models import SnowReportData, TrailBreakdown


class SnowReportsRepositoryTest(unittest.TestCase):
    def test_create_snow_report_if_missing_maps_report_data(self) -> None:
        db = Mock()
        result = Mock()
        result.scalar_one_or_none.return_value = 42
        db.execute.return_value = result
        reported_at = datetime(2026, 9, 14, 18, 52, tzinfo=timezone.utc)
        report = SnowReportData(
            reported_at=reported_at,
            open_lifts=12,
            total_lifts=21,
            open_km=Decimal("43.5"),
            total_km=Decimal("145"),
            snow_depth_min_cm=20,
            snow_depth_max_cm=75,
            avalanche_risk=2,
            access_status="Abierto",
            green_trails=TrailBreakdown(open=3, total=5),
            blue_trails=TrailBreakdown(open=8, total=12),
            red_trails=TrailBreakdown(open=6, total=9),
            black_trails=TrailBreakdown(open=1, total=3),
            data_source="aramon",
            is_verified=False,
        )

        report_id = create_snow_report_if_missing(db, resort_id=7, report=report)

        self.assertEqual(report_id, 42)
        statement, params = db.execute.call_args.args
        sql = str(statement)
        self.assertIn("INSERT INTO snow_reports", sql)
        self.assertIn("WHERE NOT EXISTS", sql)
        self.assertEqual(params["resort_id"], 7)
        self.assertEqual(params["open_lifts"], 12)
        self.assertEqual(params["total_lifts"], 21)
        self.assertEqual(params["open_km"], Decimal("43.5"))
        self.assertEqual(params["total_km"], Decimal("145"))
        self.assertEqual(params["snow_depth_min_cm"], 20)
        self.assertEqual(params["snow_depth_max_cm"], 75)
        self.assertEqual(params["avalanche_risk"], 2)
        self.assertEqual(params["access_status"], "Abierto")
        self.assertEqual(params["open_green_trails"], 3)
        self.assertEqual(params["total_green_trails"], 5)
        self.assertEqual(params["open_blue_trails"], 8)
        self.assertEqual(params["total_blue_trails"], 12)
        self.assertEqual(params["open_red_trails"], 6)
        self.assertEqual(params["total_red_trails"], 9)
        self.assertEqual(params["open_black_trails"], 1)
        self.assertEqual(params["total_black_trails"], 3)
        self.assertEqual(params["data_source"], "aramon")
        self.assertFalse(params["is_verified"])
        self.assertEqual(params["reported_at"], reported_at)


if __name__ == "__main__":
    unittest.main()
