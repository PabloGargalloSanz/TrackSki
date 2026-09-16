from datetime import datetime, timezone
from unittest.mock import Mock
import unittest

from app.scrapers.snow.baqueira import (
    BAQUEIRA_RESORTS,
    REQUEST_HEADERS,
    BaqueiraSnowScraper,
    merge_baqueira_reports,
    parse_baqueira_snow_report,
)


class BaqueiraSnowScraperTest(unittest.TestCase):
    def test_parses_spolio_blocks(self) -> None:
        html = """
        <ul>
          <li class="spolio-block" data-class="pista-verde open groomed"></li>
          <li class="spolio-block" data-class="pista-azul closed"></li>
          <li class="spolio-block" data-class="pista-roja open"></li>
          <li class="spolio-block" data-class="pista-negra"></li>
          <li class="spolio-block" data-class="gondola open"></li>
          <li class="spolio-block" data-class="6-person"></li>
          <li class="spolio-block" data-class="access open"></li>
          <li class="spolio-block" data-class="parking open"></li>
        </ul>
        """

        report = parse_baqueira_snow_report(
            html,
            reported_at=datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(report.open_lifts, 1)
        self.assertEqual(report.total_lifts, 2)
        self.assertEqual(report.green_trails.open, 1)
        self.assertEqual(report.green_trails.total, 1)
        self.assertEqual(report.blue_trails.open, 0)
        self.assertEqual(report.blue_trails.total, 1)
        self.assertEqual(report.red_trails.open, 1)
        self.assertEqual(report.red_trails.total, 1)
        self.assertEqual(report.black_trails.open, 0)
        self.assertEqual(report.black_trails.total, 1)
        self.assertEqual(report.access_status, "Estacion abierta")
        self.assertEqual(report.data_source, "baqueira")
        self.assertTrue(report.is_verified)

    def test_returns_closed_when_access_exists_but_is_not_open(self) -> None:
        html = """
        <ul>
          <li class="spolio-block" data-class="access closed"></li>
        </ul>
        """

        report = parse_baqueira_snow_report(html)

        self.assertEqual(report.access_status, "Estacion cerrada")

    def test_merges_sector_reports(self) -> None:
        first = parse_baqueira_snow_report(
            """
            <li class="spolio-block" data-class="pista-verde open"></li>
            <li class="spolio-block" data-class="gondola open"></li>
            <li class="spolio-block" data-class="access open"></li>
            """,
            reported_at=datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc),
        )
        second = parse_baqueira_snow_report(
            """
            <li class="spolio-block" data-class="pista-verde"></li>
            <li class="spolio-block" data-class="pista-azul open"></li>
            <li class="spolio-block" data-class="4-person"></li>
            """,
            reported_at=datetime(2026, 9, 16, 11, 0, tzinfo=timezone.utc),
        )

        report = merge_baqueira_reports([first, second])

        self.assertEqual(report.open_lifts, 1)
        self.assertEqual(report.total_lifts, 2)
        self.assertEqual(report.green_trails.open, 1)
        self.assertEqual(report.green_trails.total, 2)
        self.assertEqual(report.blue_trails.open, 1)
        self.assertEqual(report.blue_trails.total, 1)
        self.assertEqual(report.access_status, "Estacion abierta")
        self.assertEqual(
            report.reported_at,
            datetime(2026, 9, 16, 11, 0, tzinfo=timezone.utc),
        )

    def test_fetches_pages_with_browser_headers(self) -> None:
        response = Mock()
        response.text = """
        <li class="spolio-block" data-class="access open"></li>
        """
        response.raise_for_status.return_value = None
        client = Mock()
        client.get.return_value = response
        scraper = BaqueiraSnowScraper(client=client)

        scraper.get_current(BAQUEIRA_RESORTS[0])

        client.get.assert_any_call(
            "https://www.baqueira.es/estado-pistas",
            headers=REQUEST_HEADERS,
            follow_redirects=True,
        )

    def test_raises_when_pages_do_not_include_extractable_data(self) -> None:
        response = Mock()
        response.text = "<html></html>"
        response.raise_for_status.return_value = None
        client = Mock()
        client.get.return_value = response
        scraper = BaqueiraSnowScraper(client=client)

        with self.assertRaises(ValueError):
            scraper.get_current(BAQUEIRA_RESORTS[0])


if __name__ == "__main__":
    unittest.main()
