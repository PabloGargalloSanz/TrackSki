import unittest
from datetime import datetime, timezone
from decimal import Decimal

from app.scrapers.snow.aramon import parse_aramon_snow_report


class AramonSnowScraperTest(unittest.TestCase):
    def test_parses_common_snow_report_items(self) -> None:
        html = """
        <ul>
          <li class="snow-report__item">
            <p class="snow-report__title">Remontes abiertos</p>
            <p class="snow-report__num">12 / 21</p>
            <p class="snow-report__info">Remontes disponibles</p>
          </li>
          <li class="snow-report__item">
            <p class="snow-report__title">Kilómetros esquiables</p>
            <p class="snow-report__num">43,5 / 145</p>
          </li>
          <li class="snow-report__item">
            <p class="snow-report__title">Espesor de la nieve</p>
            <p class="snow-report__num">20 - 75 cm</p>
          </li>
        </ul>
        <div class="snow-report__footer">
          <p class="snow-report__footer-txt">Riesgo de aludes 2/5 limitado</p>
        </div>
        """

        report = parse_aramon_snow_report(
            html,
            reported_at=datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(report.open_lifts, 12)
        self.assertEqual(report.total_lifts, 21)
        self.assertEqual(report.open_km, Decimal("43.5"))
        self.assertEqual(report.total_km, Decimal("145"))
        self.assertEqual(report.snow_depth_min_cm, 20)
        self.assertEqual(report.snow_depth_max_cm, 75)
        self.assertEqual(report.avalanche_risk, 2)
        self.assertEqual(report.data_source, "aramon")
        self.assertFalse(report.is_verified)


if __name__ == "__main__":
    unittest.main()
