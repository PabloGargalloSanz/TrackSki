from datetime import datetime, timezone
from unittest.mock import Mock, patch
import unittest

from app.commands.ingest_snow_reports import run
from app.services.snow.models import SnowReportData


class IngestSnowReportsTest(unittest.TestCase):
    @patch("app.commands.ingest_snow_reports.create_snow_report_if_missing")
    @patch("app.commands.ingest_snow_reports.AramonSnowScraper")
    @patch("app.commands.ingest_snow_reports.get_resorts")
    @patch("app.commands.ingest_snow_reports.SessionLocal")
    def test_imports_configured_snow_report(
        self,
        session_local: Mock,
        get_resorts: Mock,
        scraper_class: Mock,
        create_snow_report_if_missing: Mock,
    ) -> None:
        db = Mock()
        session_local.return_value = db
        get_resorts.return_value = [
            {
                "id": 3,
                "name": "Cerler",
            }
        ]
        report = SnowReportData(
            reported_at=datetime(2026, 9, 14, 18, 52, tzinfo=timezone.utc),
            open_lifts=12,
            total_lifts=21,
            data_source="aramon",
        )
        scraper = Mock()
        scraper.get_current.return_value = report
        scraper_class.return_value = scraper
        create_snow_report_if_missing.return_value = 33

        result = run()

        self.assertEqual(result.status, "success")
        self.assertEqual(result.processed, 1)
        self.assertEqual(result.inserted, 1)
        self.assertEqual(result.skipped, 0)
        scraper.get_current.assert_called_once()
        create_snow_report_if_missing.assert_called_once_with(
            db,
            resort_id=3,
            report=report,
        )
        db.commit.assert_called_once()
        scraper.close.assert_called_once()
        db.close.assert_called_once()

    def test_requires_name_and_url_together(self) -> None:
        result = run(resort_name="Cerler")

        self.assertEqual(result.status, "failed")
        self.assertIn("--resort-name y --url", result.message)


if __name__ == "__main__":
    unittest.main()
