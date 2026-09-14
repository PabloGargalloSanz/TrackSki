from datetime import datetime, timezone
from unittest.mock import Mock, patch
import unittest

from app.api.routes.resorts import retrieve_resort_map


class ResortMapRouteTest(unittest.TestCase):
    @patch("app.api.routes.resorts.get_active_road_incidents_for_road_ids")
    @patch("app.api.routes.resorts.get_access_roads_by_resort_id")
    @patch("app.api.routes.resorts.get_resort_by_id")
    def test_map_includes_access_roads_with_routes_and_relevant_incidents(
        self,
        get_resort_by_id: Mock,
        get_access_roads_by_resort_id: Mock,
        get_active_road_incidents_for_road_ids: Mock,
    ) -> None:
        db = Mock()
        now = datetime(2026, 9, 14, 10, tzinfo=timezone.utc)
        get_resort_by_id.return_value = {
            "id": 1,
            "name": "Astun",
            "country": "Spain",
            "region": "Huesca",
            "latitude": 42.8,
            "longitude": -0.5,
            "data_source": "dev_seed",
            "is_verified": False,
        }
        get_access_roads_by_resort_id.return_value = [
            {
                "access_id": 11,
                "access_role": "final_access",
                "segment_description": "Acceso final",
                "from_km": 0,
                "to_km": 10,
                "priority": 1,
                "road_id": 4,
                "code": "N-330",
                "name": "N-330 acceso",
                "route": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 42], [1, 43]]],
                },
                "data_source": "manual",
                "is_verified": False,
                "latest_status": None,
                "latest_severity": None,
                "latest_details": None,
                "latest_reported_at": None,
            }
        ]
        get_active_road_incidents_for_road_ids.return_value = [
            {
                "id": 30,
                "road_id": 4,
                "source": "dgt_datex2_v37",
                "road_code": "N-330",
                "title": "Obras en N-330",
                "description": "Obras en N-330, km 5",
                "incident_type": "roadworks",
                "status": "active",
                "severity": "medium",
                "start_km": 5,
                "end_km": 6,
                "direction": None,
                "location": None,
                "affected_route": None,
                "starts_at": None,
                "ends_at": None,
                "reported_at": now,
                "updated_at": now,
            },
            {
                "id": 31,
                "road_id": 4,
                "source": "dgt_datex2_v37",
                "road_code": "N-330",
                "title": "Obras fuera de tramo",
                "description": "Obras en N-330, km 20",
                "incident_type": "roadworks",
                "status": "active",
                "severity": "medium",
                "start_km": 20,
                "end_km": 21,
                "direction": None,
                "location": None,
                "affected_route": None,
                "starts_at": None,
                "ends_at": None,
                "reported_at": now,
                "updated_at": now,
            },
        ]

        response = retrieve_resort_map(1, db=db)

        self.assertEqual(response.roads[0].road.route["type"], "MultiLineString")
        self.assertEqual(len(response.incidents), 1)
        self.assertEqual(response.incidents[0].id, 30)
        self.assertEqual(response.incidents[0].access_role, "final_access")
        get_access_roads_by_resort_id.assert_called_once_with(
            db,
            1,
            include_route=True,
        )
        get_active_road_incidents_for_road_ids.assert_called_once_with(
            db,
            [4],
            limit=50,
        )


if __name__ == "__main__":
    unittest.main()
