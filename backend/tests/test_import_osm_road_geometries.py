import unittest

from app.jobs.import_osm_road_geometries import (
    ROAD_GEOMETRY_QUERIES,
    RoadGeometryQuery,
    build_overpass_query,
    build_road_geometry_queries,
    ref_matches_code,
    ways_to_linestring_wkts,
)


class ImportOsmRoadGeometriesTest(unittest.TestCase):
    def test_initial_road_queries_include_configured_access_roads(self) -> None:
        expected_codes = {
            "VF-TE-01",
            "A-228",
            "CG-2",
            "CG-1",
            "N-145",
            "N-260",
            "C-14",
            "C-28",
            "N-230",
            "A-2617",
            "A-139",
            "N-123a",
            "N-123",
            "A-2606",
            "A-136",
            "N-260a",
            "SC-22130-09",
            "N-330a",
            "N-330",
            "A-23",
        }
        codes = [query["code"] for query in ROAD_GEOMETRY_QUERIES]

        self.assertEqual(set(codes), expected_codes)
        self.assertEqual(len(codes), len(set(codes)))

    def test_build_road_geometry_queries_can_filter_by_code(self) -> None:
        queries = build_road_geometry_queries(["A-136", "A-2606"])

        self.assertEqual([query.code for query in queries], ["A-136", "A-2606"])

    def test_build_overpass_query_uses_exact_ref_and_bbox(self) -> None:
        query = build_overpass_query(
            RoadGeometryQuery(code="A-136", bbox=(42.60, -0.55, 42.95, -0.20))
        )

        self.assertIn('[out:json][timeout:60];', query)
        self.assertIn('way["highway"]["ref"="A-136"](42.6,-0.55,42.95,-0.2);', query)

    def test_build_overpass_query_can_use_broad_ref_search(self) -> None:
        query = build_overpass_query(
            RoadGeometryQuery(code="A-136", bbox=(42.60, -0.55, 42.95, -0.20)),
            exact_ref=False,
        )

        self.assertIn('way["highway"]["ref"](42.6,-0.55,42.95,-0.2);', query)

    def test_ref_matches_code_supports_semicolon_separated_refs(self) -> None:
        self.assertTrue(ref_matches_code("A-136", "A-136"))
        self.assertTrue(ref_matches_code("E-7; A-136", "A-136"))
        self.assertFalse(ref_matches_code("A-138", "A-136"))

    def test_ways_to_linestring_wkts_uses_lon_lat_order(self) -> None:
        wkts = ways_to_linestring_wkts(
            [
                {
                    "type": "way",
                    "geometry": [
                        {"lat": 42.1, "lon": -0.3},
                        {"lat": 42.2, "lon": -0.4},
                    ],
                }
            ]
        )

        self.assertEqual(wkts, ["LINESTRING(-0.3 42.1, -0.4 42.2)"])

    def test_ways_to_linestring_wkts_skips_invalid_geometry(self) -> None:
        wkts = ways_to_linestring_wkts(
            [
                {"type": "way", "geometry": [{"lat": 42.1, "lon": -0.3}]},
                {"type": "way"},
            ]
        )

        self.assertEqual(wkts, [])


if __name__ == "__main__":
    unittest.main()
