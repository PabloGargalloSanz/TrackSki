from datetime import datetime, timezone
from unittest.mock import Mock, patch
import unittest

from app.scrapers.snow.aramon import ARAMON_RESORTS
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
                "id": index + 1,
                "name": configured_resort.name,
            }
            for index, configured_resort in enumerate(ARAMON_RESORTS)
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
        self.assertEqual(result.processed, len(ARAMON_RESORTS))
        self.assertEqual(result.inserted, len(ARAMON_RESORTS))
        self.assertEqual(result.skipped, 0)
        self.assertEqual(scraper.get_current.call_count, len(ARAMON_RESORTS))
        self.assertEqual(
            create_snow_report_if_missing.call_count,
            len(ARAMON_RESORTS),
        )
        create_snow_report_if_missing.assert_any_call(
            db,
            resort_id=1,
            report=report,
        )
        self.assertEqual(db.commit.call_count, len(ARAMON_RESORTS))
        scraper.close.assert_called_once()
        db.close.assert_called_once()

    def test_requires_name_and_url_together(self) -> None:
        result = run(resort_name="Cerler")

        self.assertEqual(result.status, "failed")
        self.assertIn("--resort-name y --url", result.message)


if __name__ == "__main__":
    unittest.main()
