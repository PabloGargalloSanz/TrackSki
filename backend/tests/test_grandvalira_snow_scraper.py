from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
import unittest

from app.scrapers.snow.grandvalira import (
    GRANDVALIRA_RESORTS,
    REQUEST_HEADERS,
    GrandvaliraSnowScraper,
    parse_grandvalira_snow_report,
)


class GrandvaliraSnowScraperTest(unittest.TestCase):
    def test_parses_badges_lifts_km_and_depth(self) -> None:
        html = """
        <section>
          <div class="badge--icon-green">
            <span class="badge__internal-text">4 / 6</span>
          </div>
          <div class="badge--icon-blue">
            <span class="badge__internal-text">12 / 20</span>
          </div>
          <div class="badge--icon-red">
            <span class="badge__internal-text">8 / 15</span>
          </div>
          <div class="badge--icon-black">
            <span class="badge__internal-text">1 / 7</span>
          </div>
          <div id="facilities-resort-status-grandvalira" value="42 / 75"></div>
          <div aria-label="Kilómetros esquiables">
            <span class="badge__internal-text">120 / 210</span>
          </div>
          <div aria-label="Espesores de nieve (cm)">
            <span class="badge__internal-text">30 - 90</span>
          </div>
        </section>
        """

        report = parse_grandvalira_snow_report(
            html,
            reported_at=datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(report.open_lifts, 42)
        self.assertEqual(report.total_lifts, 75)
        self.assertEqual(report.open_km, Decimal("120"))
        self.assertEqual(report.total_km, Decimal("210"))
        self.assertEqual(report.snow_depth_min_cm, 30)
        self.assertEqual(report.snow_depth_max_cm, 90)
        self.assertEqual(report.green_trails.open, 4)
        self.assertEqual(report.green_trails.total, 6)
        self.assertEqual(report.blue_trails.open, 12)
        self.assertEqual(report.blue_trails.total, 20)
        self.assertEqual(report.red_trails.open, 8)
        self.assertEqual(report.red_trails.total, 15)
        self.assertEqual(report.black_trails.open, 1)
        self.assertEqual(report.black_trails.total, 7)
        self.assertEqual(report.access_status, "Estacion abierta")
        self.assertEqual(report.data_source, "grandvalira")
        self.assertTrue(report.is_verified)

    def test_fetches_with_browser_headers(self) -> None:
        response = Mock()
        response.text = """
        <div aria-label="Kilómetros esquiables">
          <span class="badge__internal-text">10 / 20</span>
        </div>
        """
        response.raise_for_status.return_value = None
        client = Mock()
        client.get.return_value = response
        scraper = GrandvaliraSnowScraper(client=client)

        scraper.get_current(GRANDVALIRA_RESORTS[0])

        client.get.assert_called_once_with(
            "https://www.grandvalira.com/es/estacion/estado-pistas",
            headers=REQUEST_HEADERS,
            follow_redirects=True,
        )

    def test_raises_when_page_has_no_extractable_data(self) -> None:
        response = Mock()
        response.text = "<html></html>"
        response.raise_for_status.return_value = None
        client = Mock()
        client.get.return_value = response
        scraper = GrandvaliraSnowScraper(client=client)

        with self.assertRaises(ValueError):
            scraper.get_current(GRANDVALIRA_RESORTS[0])


if __name__ == "__main__":
    unittest.main()
