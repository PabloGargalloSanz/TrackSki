import unittest

from app.services.weather.aemet_areas import (
    get_aemet_area_for_resort,
    get_aemet_areas_for_resorts,
)


class AemetAreasTest(unittest.TestCase):
    def test_resolves_known_spanish_resort_regions(self) -> None:
        self.assertEqual(
            get_aemet_area_for_resort({"country": "Spain", "region": "Huesca"}),
            "62",
        )
        self.assertEqual(
            get_aemet_area_for_resort({"country": "Spain", "region": "Granada"}),
            "61",
        )
        self.assertEqual(
            get_aemet_area_for_resort({"country": "Spain", "region": "Val d'Aran"}),
            "69",
        )

    def test_ignores_non_spanish_resorts(self) -> None:
        self.assertIsNone(
            get_aemet_area_for_resort(
                {"country": "Andorra", "region": "Canillo / Encamp"}
            )
        )

    def test_returns_unique_sorted_areas(self) -> None:
        areas = get_aemet_areas_for_resorts(
            [
                {"country": "Spain", "region": "Huesca"},
                {"country": "Spain", "region": "Huesca"},
                {"country": "Spain", "region": "Granada"},
            ]
        )

        self.assertEqual(areas, ["61", "62"])


if __name__ == "__main__":
    unittest.main()
