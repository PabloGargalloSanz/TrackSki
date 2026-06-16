from decimal import Decimal
import unittest

from app.services.road_access import (
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


if __name__ == "__main__":
    unittest.main()
