from decimal import Decimal
from unittest.mock import Mock, patch
import unittest

from app.scrapers.dgt_datex2 import (
    download_datex2_xml,
    extract_datex2_km,
    extract_datex2_point,
    extract_direction,
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

    def test_extracts_fields_from_dgt_technical_text(self) -> None:
        text = (
            "112_112_GV 2026-08-06T12:06:11.000+02:00 certain 112 active "
            "obstruction objectOnTheRoad ayora N-330 northEastBound "
            "nonLinkedPoint 39.231632 -1.0751014 Comunitat Valenciana "
            "137.703 Cofrentes Valencia positive incident"
        )

        self.assertEqual(extract_direction(text), "northEastBound")
        self.assertEqual(
            extract_datex2_point(text),
            (Decimal("39.231632"), Decimal("-1.0751014")),
        )
        self.assertEqual(
            extract_datex2_km(text),
            (Decimal("137.703"), Decimal("137.703")),
        )

    def test_extracts_fields_from_dgt_segment_text(self) -> None:
        text = (
            "2026-04-30T00:19:18.000+02:00 certain DGT active "
            "environmentalObstruction rockfalls unspecifiedCarriageway rightLane "
            "A-139 northBound segment 42.655514 0.5758349 Aragon 68.4 "
            "Benasque Huesca 42.654667 0.57571375 Aragon 68.3 "
            "Benasque Huesca positive mandatory anyVehicle "
            "singleAlternateLineTraffic"
        )

        self.assertEqual(extract_direction(text), "northBound")
        self.assertEqual(
            extract_datex2_point(text),
            (Decimal("42.655514"), Decimal("0.5758349")),
        )
        self.assertEqual(
            extract_datex2_km(text),
            (Decimal("68.3"), Decimal("68.4")),
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

    def test_parse_datex2_incident_without_public_description(self) -> None:
        xml = """
        <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
          <d2:situationRecord id="record-2">
            <d2:validityStatus>active</d2:validityStatus>
            <d2:severity>low</d2:severity>
            <d2:roadIdentifier>N-400</d2:roadIdentifier>
            <d2:latitude>41.772926</d2:latitude>
            <d2:longitude>-4.620479</d2:longitude>
          </d2:situationRecord>
        </d2:payload>
        """

        incidents = parse_datex2_incidents(xml)

        self.assertEqual(len(incidents), 1)
        incident = incidents[0]
        self.assertEqual(incident.road_code, "N-400")
        self.assertIsNone(incident.description)
        self.assertIn("N-400", incident.raw_payload["search_text"])

    def test_parse_datex2_ignores_technical_description_dump(self) -> None:
        technical_description = (
            "GRU_2026-9369290_9 2026-06-16T11:09:45.000+02:00 "
            "2026-06-16T11:09:45.000+02:00 certain DGT3.0 active "
            "vehicleObstruction vehicleStuck CV-655 eastBound nonLinkedPoint "
            "38.79487 -0.7064533 Comunitat Valenciana positive incident"
        )
        xml = f"""
        <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
          <d2:situationRecord id="record-3">
            <d2:value>{technical_description}</d2:value>
          </d2:situationRecord>
        </d2:payload>
        """

        incidents = parse_datex2_incidents(xml)

        self.assertEqual(len(incidents), 1)
        incident = incidents[0]
        self.assertEqual(incident.road_code, "CV-655")
        self.assertEqual(incident.incident_type, "obstruction")
        self.assertEqual(incident.severity, "low")
        self.assertIsNotNone(incident.description)
        self.assertIn("CV-655", incident.raw_payload["search_text"])

    def test_parse_datex2_fills_columns_from_generic_situation_record(self) -> None:
        text = (
            "112_112_GV 2026-08-06T12:06:11.000+02:00 certain 112 active "
            "2026-08-06T12:03:00.000+02:00 obstruction objectOnTheRoad "
            "ayora N-330 northEastBound nonLinkedPoint 39.231632 -1.0751014 "
            "Comunitat Valenciana 137.703 Cofrentes Valencia positive incident"
        )
        xml = f"""
        <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
          <d2:situationRecord id="26392454">
            <d2:value>{text}</d2:value>
          </d2:situationRecord>
        </d2:payload>
        """

        incidents = parse_datex2_incidents(xml)

        self.assertEqual(len(incidents), 1)
        incident = incidents[0]
        self.assertEqual(incident.source_id, "26392454")
        self.assertEqual(incident.road_code, "N-330")
        self.assertEqual(incident.incident_type, "obstruction")
        self.assertEqual(incident.severity, "low")
        self.assertEqual(incident.start_km, Decimal("137.703"))
        self.assertEqual(incident.end_km, Decimal("137.703"))
        self.assertEqual(incident.direction, "northEastBound")
        self.assertEqual(incident.latitude, Decimal("39.231632"))
        self.assertEqual(incident.longitude, Decimal("-1.0751014"))
        self.assertEqual(incident.title, "Obstaculo en la calzada en N-330")
        self.assertIn("km 137.703", incident.description)

    def test_parse_datex2_fills_columns_from_segment_record(self) -> None:
        text = (
            "2026-04-30T00:19:18.000+02:00 certain DGT active "
            "environmentalObstruction rockfalls unspecifiedCarriageway rightLane "
            "A-139 northBound segment 42.655514 0.5758349 Aragon 68.4 "
            "Benasque Huesca 42.654667 0.57571375 Aragon 68.3 "
            "Benasque Huesca positive mandatory anyVehicle "
            "singleAlternateLineTraffic"
        )
        xml = f"""
        <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
          <d2:situationRecord id="22587561">
            <d2:value>{text}</d2:value>
          </d2:situationRecord>
        </d2:payload>
        """

        incidents = parse_datex2_incidents(xml)

        self.assertEqual(len(incidents), 1)
        incident = incidents[0]
        self.assertEqual(incident.source_id, "22587561")
        self.assertEqual(incident.road_code, "A-139")
        self.assertEqual(incident.incident_type, "obstruction")
        self.assertEqual(incident.severity, "low")
        self.assertEqual(incident.start_km, Decimal("68.3"))
        self.assertEqual(incident.end_km, Decimal("68.4"))
        self.assertEqual(incident.direction, "northBound")
        self.assertEqual(incident.latitude, Decimal("42.655514"))
        self.assertEqual(incident.longitude, Decimal("0.5758349"))
        self.assertIn("km 68.3-68.4", incident.description)

    def test_parse_datex2_fills_columns_from_closed_road_segment_record(self) -> None:
        text = (
            "2026-08-06T12:13:06.000+02:00 "
            "2026-08-06T12:13:06.000+02:00 certain highest DGT active "
            "2026-08-06T12:13:06.000+02:00 roadMaintenance roadworks "
            "unspecifiedCarriageway allLanesCompleteCarriageway A-2606 unknown "
            "segment 42.755314 -0.23901579 Aragon 10.0 Panticosa Huesca "
            "42.72634 -0.27810314 Aragon 4.0 Panticosa Huesca both mandatory "
            "anyVehicle roadClosed"
        )
        xml = f"""
        <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
          <d2:situationRecord id="26392959">
            <d2:value>{text}</d2:value>
          </d2:situationRecord>
        </d2:payload>
        """

        incidents = parse_datex2_incidents(xml)

        self.assertEqual(len(incidents), 1)
        incident = incidents[0]
        self.assertEqual(incident.road_code, "A-2606")
        self.assertEqual(incident.incident_type, "road_closed")
        self.assertEqual(incident.severity, "critical")
        self.assertEqual(incident.start_km, Decimal("4.0"))
        self.assertEqual(incident.end_km, Decimal("10.0"))
        self.assertEqual(incident.latitude, Decimal("42.755314"))
        self.assertEqual(incident.longitude, Decimal("-0.23901579"))

    def test_parse_datex2_normalizes_real_dgt_flat_records(self) -> None:
        cases = [
            (
                "26397452",
                "vehicleObstruction vehicleStuck A-23 northEastBound "
                "nonLinkedPoint 42.01694 -0.615543 Aragon 337.634 "
                "Almudevar Huesca positive incident",
                "A-23",
                "obstruction",
                "low",
                Decimal("337.634"),
                Decimal("337.634"),
                "northEastBound",
            ),
            (
                "26396914",
                "vehicleObstruction vehicleStuck A-23 northEastBound "
                "nonLinkedPoint 41.75557 -0.83631 Aragon 300.829 "
                "Villanueva de Gallego Zaragoza positive incident",
                "A-23",
                "obstruction",
                "low",
                Decimal("300.829"),
                Decimal("300.829"),
                "northEastBound",
            ),
            (
                "26396760",
                "vehicleObstruction vehicleStuck A-23 northEastBound "
                "nonLinkedPoint 41.8558 -0.80277 Aragon 312.788 "
                "Zuera Zaragoza positive incident",
                "A-23",
                "obstruction",
                "low",
                Decimal("312.788"),
                Decimal("312.788"),
                "northEastBound",
            ),
            (
                "26392959",
                "certain highest DGT active roadMaintenance roadworks "
                "unspecifiedCarriageway allLanesCompleteCarriageway A-2606 unknown "
                "segment 42.755314 -0.23901579 Aragon 10.0 Panticosa Huesca "
                "42.72634 -0.27810314 Aragon 4.0 Panticosa Huesca both mandatory "
                "anyVehicle roadClosed",
                "A-2606",
                "road_closed",
                "critical",
                Decimal("4.0"),
                Decimal("10.0"),
                "both",
            ),
            (
                "26392454",
                "obstruction objectOnTheRoad ayora N-330 northEastBound "
                "nonLinkedPoint 39.231632 -1.0751014 Comunitat Valenciana "
                "137.703 Cofrentes Valencia positive incident",
                "N-330",
                "obstruction",
                "low",
                Decimal("137.703"),
                Decimal("137.703"),
                "northEastBound",
            ),
            (
                "26384417",
                "roadMaintenance roadworks unspecifiedCarriageway _extended "
                "N-330 southWestBound segment 39.276245 -1.079356 "
                "Comunitat Valenciana 144.0 Cofrentes Valencia "
                "39.28761 -1.0740322 Comunitat Valenciana 145.7 "
                "Cofrentes Valencia negative mandatory anyVehicle laneClosures",
                "N-330",
                "roadworks",
                "medium",
                Decimal("144.0"),
                Decimal("145.7"),
                "southWestBound",
            ),
            (
                "26384350",
                "roadMaintenance roadworks unspecifiedCarriageway rightLane "
                "A-23 northEastBound segment 41.408405 -1.1743668 Aragon "
                "245.6 Longares Zaragoza 41.401222 -1.1794292 Aragon "
                "244.7 Longares Zaragoza positive mandatory anyVehicle laneClosures",
                "A-23",
                "roadworks",
                "medium",
                Decimal("244.7"),
                Decimal("245.6"),
                "northEastBound",
            ),
            (
                "26380005",
                "roadMaintenance roadworks unspecifiedCarriageway rightLane "
                "A-23 southWestBound segment 41.407032 -1.1760099 Aragon "
                "245.4 Longares Zaragoza 41.4121 -1.1691488 Aragon "
                "246.2 Longares Zaragoza negative mandatory anyVehicle laneClosures",
                "A-23",
                "roadworks",
                "medium",
                Decimal("245.4"),
                Decimal("246.2"),
                "southWestBound",
            ),
            (
                "26378880",
                "roadMaintenance roadworks unspecifiedCarriageway leftLane "
                "A-23 southBound segment 40.479595 -1.2440635 Aragon "
                "134.0 Cella Teruel 40.51424 -1.253868 Aragon "
                "138.0 Villarquemado Teruel negative mandatory anyVehicle laneClosures",
                "A-23",
                "roadworks",
                "medium",
                Decimal("134.0"),
                Decimal("138.0"),
                "southBound",
            ),
            (
                "26376161",
                "roadMaintenance roadworks unspecifiedCarriageway rightLane "
                "A-23 southEastBound segment 40.31346 -1.0032905 Aragon "
                "104.6 Teruel Teruel 40.32014 -1.0068275 Aragon "
                "105.4 Teruel Teruel negative mandatory anyVehicle laneClosures",
                "A-23",
                "roadworks",
                "medium",
                Decimal("104.6"),
                Decimal("105.4"),
                "southEastBound",
            ),
            (
                "26376125",
                "roadMaintenance roadworks unspecifiedCarriageway rightLane "
                "A-23 northWestBound segment 40.37144 -1.1018562 Aragon "
                "116.3 Teruel Teruel 40.368202 -1.0978736 Aragon "
                "115.8 Teruel Teruel positive mandatory anyVehicle laneClosures",
                "A-23",
                "roadworks",
                "medium",
                Decimal("115.8"),
                Decimal("116.3"),
                "northWestBound",
            ),
            (
                "26307860",
                "accident accident onRoundabout unspecifiedCarriageway rightLane "
                "N-260 southEastBound segment 42.50135 -0.11846098 Aragon "
                "463.9 Fiscal Huesca 42.501293 -0.11848253 Aragon "
                "463.95 Fiscal Huesca negative mandatory anyVehicle narrowLanes",
                "N-260",
                "accident",
                "medium",
                Decimal("463.9"),
                Decimal("463.95"),
                "southEastBound",
            ),
            (
                "26405457",
                "certain DGT active poorEnvironment hail unspecifiedCarriageway "
                "allLanesCompleteCarriageway A-23 unknown segment "
                "40.21489 -0.9356637 Aragon 92.0 La Puebla de Valverde Teruel "
                "40.157925 -0.833142 Aragon 81.0 Sarrion Teruel both slipperyRoad",
                "A-23",
                "hail",
                "high",
                Decimal("81.0"),
                Decimal("92.0"),
                "both",
            ),
        ]

        for (
            source_id,
            text,
            road_code,
            incident_type,
            severity,
            start_km,
            end_km,
            direction,
        ) in cases:
            with self.subTest(source_id=source_id):
                xml = f"""
                <d2:payload xmlns:d2="http://datex2.eu/schema/3/common">
                  <d2:situationRecord id="{source_id}">
                    <d2:value>{text}</d2:value>
                  </d2:situationRecord>
                </d2:payload>
                """

                incident = parse_datex2_incidents(xml)[0]

                self.assertEqual(incident.road_code, road_code)
                self.assertEqual(incident.incident_type, incident_type)
                self.assertEqual(incident.severity, severity)
                self.assertEqual(incident.start_km, start_km)
                self.assertEqual(incident.end_km, end_km)
                self.assertEqual(incident.direction, direction)
                self.assertIsNotNone(incident.title)
                self.assertIsNotNone(incident.description)
                self.assertIsNotNone(incident.raw_payload["text"])
                if incident.incident_type == "hail":
                    self.assertEqual(incident.title, "Granizo en la calzada en A-23")
                    self.assertIn("km 81.0-92.0", incident.description)


if __name__ == "__main__":
    unittest.main()
