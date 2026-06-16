from decimal import Decimal
from unittest.mock import Mock, patch
import unittest

from app.scrapers.dgt_datex2 import (
    download_datex2_xml,
    extract_km_range,
    extract_road_code,
    make_stable_source_id,
    normalize_incident_type,
    normalize_severity,
    normalize_status,
    parse_datex2_incidents,
)


class DgtDatex2NormalizationTest(unittest.TestCase):
    def test_download_datex2_xml(self) -> None:
        response = Mock()
        response.content = b"<xml />"

        with patch("app.scrapers.dgt_datex2.httpx.get", return_value=response) as get:
            content = download_datex2_xml(
                url="https://example.test/datex2.xml",
                timeout_seconds=5,
            )

        self.assertEqual(content, b"<xml />")
        response.raise_for_status.assert_called_once_with()
        get.assert_called_once_with("https://example.test/datex2.xml", timeout=5)

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

    def test_parse_datex2_incidents(self) -> None:
        xml = """
        <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
          <d2:situation id="situation-1">
            <d2:situationRecord id="record-1">
              <d2:situationRecordCreationTime>
                2026-01-15T10:00:00Z
              </d2:situationRecordCreationTime>
              <d2:situationRecordVersionTime>
                2026-01-15T10:05:00Z
              </d2:situationRecordVersionTime>
              <d2:validityStatus>active</d2:validityStatus>
              <d2:severity>high</d2:severity>
              <d2:generalPublicComment>
                <d2:comment>
                  <d2:values>
                    <d2:value>
                      Uso obligatorio de cadenas en A-136 entre km 12 y 18
                    </d2:value>
                  </d2:values>
                </d2:comment>
              </d2:generalPublicComment>
              <d2:locationForDisplay>
                <d2:latitude>42.7753</d2:latitude>
                <d2:longitude>-0.3632</d2:longitude>
              </d2:locationForDisplay>
            </d2:situationRecord>
          </d2:situation>
        </d2:payload>
        """

        incidents = parse_datex2_incidents(xml)

        self.assertEqual(len(incidents), 1)
        incident = incidents[0]
        self.assertEqual(incident.source_id, "record-1")
        self.assertEqual(incident.road_code, "A-136")
        self.assertEqual(incident.incident_type, "chains_required")
        self.assertEqual(incident.status, "active")
        self.assertEqual(incident.severity, "high")
        self.assertEqual(incident.start_km, Decimal("12"))
        self.assertEqual(incident.end_km, Decimal("18"))
        self.assertEqual(incident.latitude, Decimal("42.7753"))
        self.assertEqual(incident.longitude, Decimal("-0.3632"))
        self.assertIsNotNone(incident.reported_at)
        self.assertIsNotNone(incident.updated_at)


if __name__ == "__main__":
    unittest.main()
