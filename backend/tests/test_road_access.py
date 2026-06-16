from decimal import Decimal
import unittest

from app.services.road_access import km_ranges_overlap, overall_access_status


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


if __name__ == "__main__":
    unittest.main()
