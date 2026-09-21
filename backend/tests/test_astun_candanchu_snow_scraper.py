from datetime import datetime, timezone
from decimal import Decimal
import unittest

from app.scrapers.snow.astun_candanchu import parse_astun_candanchu_snow_report


class AstunCandanchuSnowScraperTest(unittest.TestCase):
    def test_parses_astun_mobile_fields_and_trails(self) -> None:
        html = """
        <section>
          <span id="1_LabDatoRemontesR">10 / 15</span>
          <span id="1_lblMovilKm">32,5 / 50</span>
          <span id="1_lblMovilEspesorMin">20 cm</span>
          <span id="1_lblMovilEspesorMax">80 cm</span>
          <span id="1_lblMovilRiesgo">2</span>
          <span id="1_lblMovilAccesos">Accesos abiertos</span>
          <table id="RepPistasVerdes">
            <tr><th>Pista</th><th>Estado</th></tr>
            <tr><td>Pista 1</td><td class="estado_abierto">Abierta</td></tr>
            <tr><td>Pista 2</td><td>Cerrada</td></tr>
          </table>
          <table id="RepPistasAzules">
            <tr><td>Pista 3</td><td class="text-success">Abierta</td></tr>
          </table>
        </section>
        """

        report = parse_astun_candanchu_snow_report(
            html,
            "Astún",
            reported_at=datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(report.open_lifts, 10)
        self.assertEqual(report.total_lifts, 15)
        self.assertEqual(report.open_km, Decimal("32.5"))
        self.assertEqual(report.total_km, Decimal("50"))
        self.assertEqual(report.snow_depth_min_cm, 20)
        self.assertEqual(report.snow_depth_max_cm, 80)
        self.assertEqual(report.avalanche_risk, 2)
        self.assertEqual(report.access_status, "Accesos abiertos")
        self.assertEqual(report.green_trails.open, 1)
        self.assertEqual(report.green_trails.total, 2)
        self.assertEqual(report.blue_trails.open, 1)
        self.assertEqual(report.blue_trails.total, 1)
        self.assertEqual(report.data_source, "astun_candanchu")
        self.assertTrue(report.is_verified)

    def test_parses_candanchu_fields(self) -> None:
        html = """
        <section>
          <span id="1_LabDatoRemontesRCan">8 / 20</span>
          <span id="1_lblMovilKmCan">25 / 42</span>
          <span id="1_lblMovilEspesorMinCan">15 cm</span>
          <span id="1_lblMovilEspesorMaxCan">60 cm</span>
          <span id="1_lblMovilRiesgoCan">3</span>
          <span id="1_lblMovilAccesosCan">Estacion abierta</span>
        </section>
        """

        report = parse_astun_candanchu_snow_report(html, "Candanchú")

        self.assertEqual(report.open_lifts, 8)
        self.assertEqual(report.total_lifts, 20)
        self.assertEqual(report.open_km, Decimal("25"))
        self.assertEqual(report.total_km, Decimal("42"))
        self.assertEqual(report.access_status, "Estacion abierta")

    def test_returns_closed_status_when_expected_fields_are_missing(self) -> None:
        html = """
        <section>
          <h1>Parte de nieve</h1>
          <p>Estacion cerrada por fin de temporada.</p>
        </section>
        """

        report = parse_astun_candanchu_snow_report(html, "Astún")

        self.assertEqual(report.open_lifts, 0)
        self.assertEqual(report.total_lifts, 0)
        self.assertEqual(report.open_km, Decimal("0"))
        self.assertEqual(report.total_km, Decimal("0"))
        self.assertEqual(report.access_status, "Estacion cerrada")

    def test_closed_status_forces_counters_to_zero(self) -> None:
        html = """
        <section>
          <span id="1_LabDatoRemontesR">15</span>
          <span id="1_lblMovilAccesos">Estacion cerrada</span>
        </section>
        """

        report = parse_astun_candanchu_snow_report(html, "Astún")

        self.assertEqual(report.open_lifts, 0)
        self.assertEqual(report.total_lifts, 0)
        self.assertEqual(report.open_km, Decimal("0"))
        self.assertEqual(report.total_km, Decimal("0"))
        self.assertEqual(report.access_status, "Estacion cerrada")


if __name__ == "__main__":
    unittest.main()
