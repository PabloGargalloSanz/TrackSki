import unittest
from unittest.mock import Mock, patch

from app.commands.ingest_alerts import run
from app.services.weather.alerts import WeatherAlert


class IngestAlertsCommandTest(unittest.TestCase):
    @patch("app.commands.ingest_alerts.SessionLocal")
    @patch("app.commands.ingest_alerts.save_weather_alert")
    @patch("app.commands.ingest_alerts.is_actionable_alert")
    @patch("app.commands.ingest_alerts.read_aemet_alert_package")
    @patch("app.commands.ingest_alerts.AemetClient")
    @patch("app.commands.ingest_alerts.settings")
    def test_reports_saved_alerts_without_claiming_updates(
        self,
        settings: Mock,
        aemet_client: Mock,
        read_aemet_alert_package: Mock,
        is_actionable_alert: Mock,
        save_weather_alert: Mock,
        session_local: Mock,
    ) -> None:
        alert = WeatherAlert(
            identifier="alert-1",
            level="naranja",
            event="Nevadas",
            area="Pirineo",
            onset=None,
            expires=None,
            headline=None,
            description=None,
            instruction=None,
        )
        settings.AEMET_API_KEY = "test-key"
        aemet_client.return_value.__enter__.return_value.get_latest_alerts.return_value = (
            b"package"
        )
        read_aemet_alert_package.return_value = [alert]
        is_actionable_alert.return_value = True
        db = Mock()
        session_local.return_value = db

        result = run(areas=["62"])

        self.assertEqual(result.status, "success")
        self.assertEqual(result.processed, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.metadata["areas"], ["62"])
        self.assertEqual(result.metadata["saved"], 1)
        self.assertIn("Guardados 1 avisos", result.message)
        save_weather_alert.assert_called_once_with(db, alert)
        db.commit.assert_called_once()
        db.close.assert_called_once()

    @patch("app.commands.ingest_alerts.SessionLocal")
    @patch("app.commands.ingest_alerts.save_weather_alert")
    @patch("app.commands.ingest_alerts.is_actionable_alert")
    @patch("app.commands.ingest_alerts.read_aemet_alert_package")
    @patch("app.commands.ingest_alerts.AemetClient")
    @patch("app.commands.ingest_alerts.get_resorts")
    @patch("app.commands.ingest_alerts.settings")
    def test_derives_unique_areas_from_configured_resorts(
        self,
        settings: Mock,
        get_resorts: Mock,
        aemet_client: Mock,
        read_aemet_alert_package: Mock,
        is_actionable_alert: Mock,
        save_weather_alert: Mock,
        session_local: Mock,
    ) -> None:
        settings.AEMET_API_KEY = "test-key"
        get_resorts.return_value = [
            {"country": "Spain", "region": "Huesca"},
            {"country": "Spain", "region": "Granada"},
            {"country": "Andorra", "region": "Canillo"},
        ]
        aemet_client.return_value.__enter__.return_value.get_latest_alerts.return_value = (
            b"package"
        )
        read_aemet_alert_package.return_value = []
        is_actionable_alert.return_value = False
        db = Mock()
        session_local.return_value = db

        result = run()

        self.assertEqual(result.status, "success")
        self.assertEqual(result.metadata["areas"], ["61", "62"])
        self.assertEqual(
            aemet_client.return_value.__enter__.return_value.get_latest_alerts.call_count,
            2,
        )
        save_weather_alert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
