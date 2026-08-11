from datetime import datetime, timezone
from decimal import Decimal
import unittest

from app.services.road_access import (
    compact_roadwork_incidents,
    km_ranges_overlap,
    most_relevant_access_role,
    overall_access_status,
    road_condition_status_from_incidents,
)


class RoadAccessTest(unittest.TestCase):
    def test_km_ranges_overlap(self) -> None:
        self.assertTrue(
            km_ranges_overlap(
                Decimal("10.000"),
                Decimal("20.000"),
                Decimal("15.000"),
                Decimal("25.000"),
            )
        )

    def test_km_ranges_do_not_overlap(self) -> None:
        self.assertFalse(
            km_ranges_overlap(
                Decimal("10.000"),
                Decimal("20.000"),
                Decimal("21.000"),
                Decimal("25.000"),
            )
        )

    def test_missing_km_data_is_considered_relevant(self) -> None:
        self.assertTrue(
            km_ranges_overlap(
                Decimal("10.000"),
                Decimal("20.000"),
                None,
                None,
            )
        )

    def test_overall_access_status(self) -> None:
        self.assertEqual(overall_access_status([]), "open")
        self.assertEqual(
            overall_access_status([{"severity": "medium"}]),
            "caution",
        )
        self.assertEqual(
            overall_access_status([{"severity": "high"}]),
            "affected",
        )

    def test_overall_access_status_for_direct_access_incidents(self) -> None:
        self.assertEqual(
            overall_access_status(
                [
                    {
                        "incident_type": "road_closed",
                        "severity": "critical",
                        "access_role": "final_access",
                    }
                ]
            ),
            "closed",
        )
        self.assertEqual(
            overall_access_status(
                [
                    {
                        "incident_type": "chains_required",
                        "severity": "high",
                        "access_role": "primary",
                    }
                ]
            ),
            "chains",
        )

    def test_overall_access_status_for_approach_incidents(self) -> None:
        self.assertEqual(
            overall_access_status(
                [
                    {
                        "incident_type": "road_closed",
                        "severity": "critical",
                        "access_role": "approach",
                    }
                ]
            ),
            "affected",
        )
        self.assertEqual(
            overall_access_status(
                [
                    {
                        "incident_type": "chains_required",
                        "severity": "high",
                        "access_role": "approach",
                    }
                ]
            ),
            "affected",
        )

    def test_most_relevant_access_role(self) -> None:
        self.assertEqual(
            most_relevant_access_role(
                [
                    {"access_role": "approach"},
                    {"access_role": "final_access"},
                ]
            ),
            "final_access",
        )
        self.assertIsNone(most_relevant_access_role([]))

    def test_road_condition_status_from_incidents(self) -> None:
        self.assertIsNone(road_condition_status_from_incidents([]))
        self.assertEqual(
            road_condition_status_from_incidents(
                [
                    {"incident_type": "road_closed", "severity": "critical"},
                    {"incident_type": "chains_required", "severity": "high"},
                ]
            ),
            "closed",
        )
        self.assertEqual(
            road_condition_status_from_incidents(
                [{"incident_type": "chains_required", "severity": "medium"}]
            ),
            "chains",
        )
        self.assertEqual(
            road_condition_status_from_incidents(
                [{"incident_type": "snow", "severity": "medium"}]
            ),
            "caution",
        )
        self.assertEqual(
            road_condition_status_from_incidents(
                [{"incident_type": "accident", "severity": "high"}]
            ),
            "affected",
        )

    def test_compact_roadwork_incidents_groups_same_road(self) -> None:
        incidents = [
            {
                "id": 1,
                "road_id": 10,
                "road_code": "A-136",
                "title": "Obras en A-136",
                "description": "Obras en A-136, km 0.0-17.5",
                "incident_type": "roadworks",
                "status": "active",
                "severity": "medium",
                "start_km": Decimal("0.0"),
                "end_km": Decimal("17.5"),
                "direction": "northBound",
                "updated_at": datetime(2026, 8, 11, 8, tzinfo=timezone.utc),
                "access_role": "final_access",
            },
            {
                "id": 2,
                "road_id": 10,
                "road_code": "A-136",
                "title": "Obras en A-136",
                "description": "Obras en A-136, km 0.0-26.9",
                "incident_type": "roadworks",
                "status": "active",
                "severity": "medium",
                "start_km": Decimal("0.0"),
                "end_km": Decimal("26.9"),
                "direction": "southBound",
                "updated_at": datetime(2026, 8, 11, 9, tzinfo=timezone.utc),
                "access_role": "final_access",
            },
        ]

        compacted = compact_roadwork_incidents(incidents)

        self.assertEqual(len(compacted), 1)
        self.assertEqual(compacted[0]["id"], 2)
        self.assertEqual(compacted[0]["road_code"], "A-136")
        self.assertEqual(compacted[0]["title"], "Obras en A-136")
        self.assertEqual(compacted[0]["start_km"], Decimal("0.0"))
        self.assertEqual(compacted[0]["end_km"], Decimal("26.9"))
        self.assertEqual(compacted[0]["direction"], "varios sentidos")
        self.assertIn("Agrupa 2 incidencias activas", compacted[0]["description"])

    def test_compact_roadwork_incidents_keeps_other_incidents(self) -> None:
        incidents = [
            {
                "id": 1,
                "road_id": 10,
                "road_code": "A-136",
                "incident_type": "roadworks",
                "severity": "medium",
                "start_km": Decimal("0.0"),
                "end_km": Decimal("17.5"),
                "updated_at": datetime(2026, 8, 11, 8, tzinfo=timezone.utc),
                "access_role": "final_access",
            },
            {
                "id": 2,
                "road_id": 10,
                "road_code": "A-136",
                "incident_type": "obstruction",
                "severity": "low",
                "updated_at": datetime(2026, 8, 11, 9, tzinfo=timezone.utc),
                "access_role": "final_access",
            },
        ]

        compacted = compact_roadwork_incidents(incidents)

        self.assertEqual(len(compacted), 2)


if __name__ == "__main__":
    unittest.main()
