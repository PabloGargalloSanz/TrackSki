from decimal import Decimal
import unittest

from app.scrapers.dgt_datex2 import (
    extract_km_range,
    extract_road_code,
    make_stable_source_id,
    normalize_incident_type,
    normalize_severity,
    normalize_status,
)


class DgtDatex2NormalizationTest(unittest.TestCase):
    def test_extract_road_code(self) -> None:
        self.assertEqual(
            extract_road_code("Incidencia en A-136 sentido Francia"),
            "A-136",
        )
        self.assertEqual(
            extract_road_code("Corte en la carretera N260 por nieve"),
            "N260",
        )

    def test_extract_km_range(self) -> None:
        self.assertEqual(
            extract_km_range("corte entre km 12,5 y 18"),
            (Decimal("12.5"), Decimal("18")),
        )
        self.assertEqual(
            extract_km_range("incidencia en PK 21"),
            (Decimal("21"), Decimal("21")),
        )
        self.assertEqual(
            extract_km_range("del km 20 al 10"),
            (Decimal("10"), Decimal("20")),
        )

    def test_normalize_incident_type(self) -> None:
        self.assertEqual(
            normalize_incident_type(None, "Uso obligatorio de cadenas"),
            "chains_required",
        )
        self.assertEqual(
            normalize_incident_type(None, "Carretera cortada por nieve"),
            "road_closed",
        )
        self.assertEqual(
            normalize_incident_type("roadworks", "obras en calzada"),
            "roadworks",
        )

    def test_normalize_status(self) -> None:
        self.assertEqual(normalize_status("active"), "active")
        self.assertEqual(normalize_status("previsto"), "planned")
        self.assertEqual(normalize_status("finalizado"), "resolved")
        self.assertEqual(normalize_status(None), "unknown")

    def test_normalize_severity(self) -> None:
        self.assertEqual(
            normalize_severity(None, "road_closed", None),
            "critical",
        )
        self.assertEqual(
            normalize_severity(None, "chains_required", None),
            "high",
        )
        self.assertEqual(
            normalize_severity("leve", "other", None),
            "low",
        )

    def test_make_stable_source_id(self) -> None:
        first_id = make_stable_source_id("A-136", "cadenas", None)
        second_id = make_stable_source_id("A-136", "cadenas", None)

        self.assertEqual(first_id, second_id)


if __name__ == "__main__":
    unittest.main()
