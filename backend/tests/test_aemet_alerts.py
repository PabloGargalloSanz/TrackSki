import unittest
from datetime import datetime, timezone
from io import BytesIO
from tarfile import open as open_tar
from zipfile import ZipFile

from app.services.weather.alerts import (
    read_aemet_alert_package,
    read_aemet_alerts,
)

CAP_ALERT = b"""<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>2.49.0.0.724.0.ES.20260615.1</identifier>
  <sender>AEMET</sender>
  <sent>2026-06-15T08:00:00+00:00</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <language>es-ES</language>
    <category>Met</category>
    <event>Nevadas</event>
    <urgency>Expected</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <onset>2026-06-15T12:00:00Z</onset>
    <expires>2026-06-16T00:00:00Z</expires>
    <headline>Aviso naranja por nevadas</headline>
    <description>Acumulacion de nieve en cotas altas.</description>
    <instruction>Extreme las precauciones.</instruction>
    <parameter>
      <valueName>Nivel</valueName>
      <value>naranja</value>
    </parameter>
    <area>
      <areaDesc>Pirineo de Huesca</areaDesc>
    </area>
  </info>
</alert>
"""


class AemetAlertsTest(unittest.TestCase):
    def test_reads_alert_level_and_validity(self) -> None:
        alerts = read_aemet_alerts(CAP_ALERT)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].level, "naranja")
        self.assertEqual(alerts[0].event, "Nevadas")
        self.assertEqual(alerts[0].area, "Pirineo de Huesca")
        self.assertEqual(
            alerts[0].onset,
            datetime(2026, 6, 15, 12, tzinfo=timezone.utc),
        )
        self.assertEqual(alerts[0].source, "aemet")

    def test_reads_all_xml_alerts_from_zip_package(self) -> None:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr("first-alert.xml", CAP_ALERT)
            archive.writestr("second-alert.XML", CAP_ALERT)
            archive.writestr("readme.txt", "ignored")

        alerts = read_aemet_alert_package(buffer.getvalue())

        self.assertEqual(len(alerts), 2)
        self.assertTrue(all(alert.level == "naranja" for alert in alerts))

    def test_reads_all_xml_alerts_from_tar_package(self) -> None:
        buffer = BytesIO()
        with open_tar(fileobj=buffer, mode="w") as archive:
            document = BytesIO(CAP_ALERT)
            info = archive.tarinfo()
            info.name = "alert.xml"
            info.size = len(CAP_ALERT)
            archive.addfile(info, document)

        alerts = read_aemet_alert_package(buffer.getvalue())

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].event, "Nevadas")


if __name__ == "__main__":
    unittest.main()
