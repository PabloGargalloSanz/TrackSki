from datetime import datetime, timezone
from unittest.mock import Mock, patch
import unittest

from app.api.routes.resorts import retrieve_resort_summary
from app.schemas.road import ResortAccessStatusResponse


class ResortSummaryRouteTest(unittest.TestCase):
    @patch("app.api.routes.resorts.build_resort_access_status")
    @patch("app.api.routes.resorts.get_active_weather_alerts")
    @patch("app.api.routes.resorts.get_aemet_area_for_resort")
    @patch("app.api.routes.resorts.get_roads_by_resort_id")
    @patch("app.api.routes.resorts.get_weather_forecasts_by_resort_id")
    @patch("app.api.routes.resorts.get_latest_weather_report_by_resort_id")
    @patch("app.api.routes.resorts.get_latest_snow_report_by_resort_id")
    @patch("app.api.routes.resorts.get_resort_by_id")
    def test_summary_includes_alerts_and_access_status(
        self,
        get_resort_by_id: Mock,
        get_latest_snow_report_by_resort_id: Mock,
        get_latest_weather_report_by_resort_id: Mock,
        get_weather_forecasts_by_resort_id: Mock,
        get_roads_by_resort_id: Mock,
        get_aemet_area_for_resort: Mock,
        get_active_weather_alerts: Mock,
        build_resort_access_status: Mock,
    ) -> None:
        db = Mock()
        now = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)
        get_resort_by_id.return_value = {
            "id": 1,
            "name": "Formigal",
            "country": "Spain",
            "region": "Huesca",
            "latitude": 42.7753,
            "longitude": -0.3632,
            "data_source": "dev_seed",
            "is_verified": False,
        }
        get_latest_snow_report_by_resort_id.return_value = None
        get_latest_weather_report_by_resort_id.return_value = None
        get_weather_forecasts_by_resort_id.return_value = [
            {
                "id": 20,
                "resort_id": 1,
                "forecast_date": now.date(),
                "temperature_min_celsius": -4,
                "temperature_max_celsius": 2,
                "precipitation_mm": 1.5,
                "snowfall_cm": 3,
                "wind_speed_max_kmh": 22,
                "weather": "Nevada ligera",
                "data_source": "open-meteo",
                "is_verified": False,
                "reported_at": now,
            }
        ]
        get_roads_by_resort_id.return_value = []
        get_aemet_area_for_resort.return_value = "62"
        get_active_weather_alerts.return_value = [
            {
                "id": 10,
                "identifier": "alert-1",
                "level": "naranja",
                "event": "Nevadas",
                "area": "Pirineo de Huesca",
                "onset": now,
                "expires": None,
                "headline": "Aviso naranja por nevadas",
                "description": None,
                "instruction": None,
                "data_source": "aemet",
                "created_at": now,
            }
        ]
        access_status = ResortAccessStatusResponse(
            resort_id=1,
            overall_status="open",
            roads=[],
            incidents=[],
            alternatives=[],
        )
        build_resort_access_status.return_value = access_status

        summary = retrieve_resort_summary(1, db=db)

        self.assertEqual(summary.weather_alerts[0].level, "naranja")
        self.assertEqual(summary.weather_forecasts[0].weather, "Nevada ligera")
        self.assertEqual(summary.access_status, access_status)
        get_weather_forecasts_by_resort_id.assert_called_once_with(db, 1)
        get_active_weather_alerts.assert_called_once_with(db, areas=["62"])
        build_resort_access_status.assert_called_once_with(db, 1)


if __name__ == "__main__":
    unittest.main()
