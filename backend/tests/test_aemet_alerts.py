import unittest
from datetime import datetime, timezone

from app.services.weather.alerts import read_aemet_alerts

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

if __name__ == "__main__":
    unittest.main()
