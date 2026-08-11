import argparse
import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import text

from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT_SECONDS = 60
OVERPASS_REQUEST_DELAY_SECONDS = 3
OVERPASS_RETRY_DELAY_SECONDS = 20
OVERPASS_MAX_ATTEMPTS = 3
OVERPASS_RETRY_STATUS_CODES = {429, 502, 503, 504}

# Geometries come from OpenStreetMap and must be attributed to:
# © OpenStreetMap contributors.
ROAD_GEOMETRY_QUERIES = [
    {
        "code": "VF-TE-01",
        "bbox": (40.35, -0.72, 40.47, -0.55),
    },
    {
        "code": "A-228",
        "bbox": (40.20, -0.95, 40.45, -0.55),
    },
    {
        "code": "CG-2",
        "bbox": (42.50, 1.50, 42.60, 1.75),
    },
    {
        "code": "CG-1",
        "bbox": (42.43, 1.43, 42.52, 1.55),
    },
    {
        "code": "N-145",
        "bbox": (42.35, 1.39, 42.48, 1.50),
    },
    {
        "code": "N-260",
        "bbox": (42.25, 1.15, 42.45, 1.55),
    },
    {
        "code": "C-14",
        "bbox": (41.90, 1.00, 42.40, 1.50),
    },
    {
        "code": "C-28",
        "bbox": (42.60, 0.70, 42.82, 1.10),
    },
    {
        "code": "N-230",
        "bbox": (42.00, 0.45, 42.80, 0.90),
    },
    {
        "code": "A-2617",
        "bbox": (42.56, 0.50, 42.62, 0.58),
    },
    {
        "code": "A-139",
        "bbox": (42.25, 0.30, 42.70, 0.65),
    },
    {
        "code": "N-123a",
        "bbox": (42.00, 0.10, 42.30, 0.45),
    },
    {
        "code": "N-123",
        "bbox": (41.95, 0.00, 42.30, 0.45),
    },
    {
        "code": "A-136",
        "bbox": (42.60, -0.55, 42.95, -0.20),
    },
    {
        "code": "A-2606",
        "bbox": (42.65, -0.35, 42.80, -0.20),
    },
    {
        "code": "N-260a",
        "bbox": (42.45, -0.45, 42.68, -0.25),
    },
    {
        "code": "SC-22130-09",
        "bbox": (42.76, -0.58, 42.84, -0.48),
    },
    {
        "code": "N-330a",
        "bbox": (42.50, -0.60, 42.85, -0.40),
    },
    {
        "code": "N-330",
        "bbox": (42.35, -0.65, 42.85, -0.25),
    },
    {
        "code": "A-23",
        "bbox": (41.60, -1.10, 42.60, -0.20),
    },
]


@dataclass(frozen=True)
class RoadGeometryQuery:
    code: str
    bbox: tuple[float, float, float, float]


@dataclass
class ImportSummary:
    processed: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0


def main() -> int:
    args = parse_args()
    result = run(codes=args.code)
    print_job_result(result)
    return 0 if result.status in {"success", "partial"} else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa geometrias reales de carreteras desde OpenStreetMap/Overpass."
    )
    parser.add_argument(
        "--code",
        action="append",
        help=(
            "Codigo de carretera a importar, por ejemplo A-136. "
            "Se puede repetir. Si se omite, importa todas las configuradas."
        ),
    )
    return parser.parse_args()


def run(codes: list[str] | None = None) -> JobResult:
    queries = build_road_geometry_queries(codes)
    summary = ImportSummary(processed=len(queries))

    db = SessionLocal()
    try:
        for query_config in queries:
            print(f"Importando geometria OSM para {query_config.code}...", flush=True)
            try:
                ways = fetch_overpass_ways(query_config)
                linestring_wkts = ways_to_linestring_wkts(ways)

                if not linestring_wkts:
                    summary.skipped += 1
                    print(
                        f"AVISO: Overpass no devolvio geometria usable para {query_config.code}.",
                        flush=True,
                    )
                    continue

                update_result = update_road_route(
                    db,
                    code=query_config.code,
                    linestring_wkts=linestring_wkts,
                )
                db.commit()

                if not update_result:
                    summary.skipped += 1
                    print(
                        f"AVISO: no existe road manual para {query_config.code}.",
                        flush=True,
                    )
                    continue

                summary.updated += 1
                print(
                    (
                        f"OK: {query_config.code} actualizada "
                        f"({update_result['num_geometries']} tramos, "
                        f"{update_result['length_km']:.2f} km)."
                    ),
                    flush=True,
                )
            except Exception as error:
                db.rollback()
                summary.errors += 1
                print(f"ERROR: {query_config.code}: {error}", flush=True)

            time.sleep(OVERPASS_REQUEST_DELAY_SECONDS)
    finally:
        db.close()

    status = "success"
    if summary.errors and summary.updated:
        status = "partial"
    elif summary.errors and not summary.updated:
        status = "failed"

    return JobResult(
        job_name="OSM road geometries",
        status=status,
        processed=summary.processed,
        updated=summary.updated,
        skipped=summary.skipped,
        errors=[] if not summary.errors else [f"{summary.errors} carreteras fallaron"],
        message="Geometrias OSM importadas. Atribucion: © OpenStreetMap contributors.",
        metadata={
            "source": "openstreetmap_overpass",
            "osm_attribution": "© OpenStreetMap contributors",
        },
    )


def build_road_geometry_queries(codes: list[str] | None = None) -> list[RoadGeometryQuery]:
    selected_codes = {code.upper() for code in codes} if codes else None
    queries = []

    for item in ROAD_GEOMETRY_QUERIES:
        code = item["code"]
        if selected_codes and code.upper() not in selected_codes:
            continue

        queries.append(RoadGeometryQuery(code=code, bbox=item["bbox"]))

    return queries


def build_overpass_query(query_config: RoadGeometryQuery, *, exact_ref: bool = True) -> str:
    south, west, north, east = query_config.bbox
    ref_filter = (
        f'["ref"="{query_config.code}"]'
        if exact_ref
        else '["ref"]'
    )

    return f"""
[out:json][timeout:{OVERPASS_TIMEOUT_SECONDS}];
(
  way["highway"]{ref_filter}({south},{west},{north},{east});
);
out geom;
""".strip()


def fetch_overpass_ways(query_config: RoadGeometryQuery) -> list[dict[str, Any]]:
    exact_ways = fetch_overpass_ways_for_query(
        build_overpass_query(query_config, exact_ref=True),
        query_config.code,
    )
    if exact_ways:
        return exact_ways

    print(
        (
            f"AVISO: no se encontraron ways con ref exacto para {query_config.code}. "
            "Probando busqueda amplia en la bbox."
        ),
        flush=True,
    )
    return fetch_overpass_ways_for_query(
        build_overpass_query(query_config, exact_ref=False),
        query_config.code,
    )


def fetch_overpass_ways_for_query(
    query: str,
    code: str,
) -> list[dict[str, Any]]:
    response = post_overpass_query(query)

    payload = response.json()
    elements = payload.get("elements", [])
    return [
        element
        for element in elements
        if element.get("type") == "way"
        and ref_matches_code(element.get("tags", {}).get("ref"), code)
    ]


def post_overpass_query(query: str) -> httpx.Response:
    last_error: Exception | None = None
    last_response: httpx.Response | None = None

    for attempt in range(1, OVERPASS_MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(
                OVERPASS_API_URL,
                data={"data": query},
                headers={
                    "Accept": "application/json",
                    "User-Agent": "TrackSki/0.1 road geometry import",
                },
                timeout=OVERPASS_TIMEOUT_SECONDS,
            )
            last_response = response
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as error:
            last_error = error
            status_code = error.response.status_code
            if status_code not in OVERPASS_RETRY_STATUS_CODES:
                break

            if attempt < OVERPASS_MAX_ATTEMPTS:
                print(
                    (
                        f"AVISO: Overpass devolvio HTTP {status_code}. "
                        f"Reintentando en {OVERPASS_RETRY_DELAY_SECONDS}s "
                        f"({attempt}/{OVERPASS_MAX_ATTEMPTS})..."
                    ),
                    flush=True,
                )
                time.sleep(OVERPASS_RETRY_DELAY_SECONDS)
        except httpx.HTTPError as error:
            last_error = error
            if attempt < OVERPASS_MAX_ATTEMPTS:
                print(
                    (
                        "AVISO: no se pudo conectar con Overpass. "
                        f"Reintentando en {OVERPASS_RETRY_DELAY_SECONDS}s "
                        f"({attempt}/{OVERPASS_MAX_ATTEMPTS})..."
                    ),
                    flush=True,
                )
                time.sleep(OVERPASS_RETRY_DELAY_SECONDS)

    if last_response is not None:
        details = last_response.text.strip().replace("\n", " ")[:500]
        raise ValueError(
            f"Overpass devolvio HTTP {last_response.status_code}: {details}"
        ) from last_error

    raise ValueError(f"No se pudo conectar con Overpass: {last_error}") from last_error


def ways_to_linestring_wkts(ways: list[dict[str, Any]]) -> list[str]:
    wkts: list[str] = []

    for way in ways:
        geometry = way.get("geometry")
        if not isinstance(geometry, list) or len(geometry) < 2:
            continue

        coordinates = []
        for point in geometry:
            lat = point.get("lat")
            lon = point.get("lon")
            if lat is None or lon is None:
                continue
            coordinates.append(f"{float(lon)} {float(lat)}")

        if len(coordinates) < 2:
            continue

        wkts.append(f"LINESTRING({', '.join(coordinates)})")

    return wkts


def ref_matches_code(ref: str | None, code: str) -> bool:
    if not ref:
        return False

    refs = [part.strip().upper() for part in ref.split(";")]
    return code.upper() in refs


def update_road_route(
    db,
    *,
    code: str,
    linestring_wkts: list[str],
) -> dict[str, Any] | None:
    result = db.execute(
        text(
            """
            WITH geometries AS (
                SELECT ST_GeomFromText(wkt, 4326) AS geom
                FROM unnest(CAST(:wkts AS text[])) AS wkt
            ),
            merged AS (
                SELECT ST_Multi(
                    ST_CollectionExtract(
                        ST_LineMerge(ST_Union(geom)),
                        2
                    )
                ) AS geom
                FROM geometries
            )
            UPDATE roads
            SET
                route = merged.geom,
                updated_at = CURRENT_TIMESTAMP
            FROM merged
            WHERE roads.code = :code
              AND roads.data_source = 'manual'
            RETURNING
                roads.id,
                ST_NumGeometries(roads.route) AS num_geometries,
                ST_Length(roads.route::geography) / 1000 AS length_km
            """
        ),
        {"code": code, "wkts": linestring_wkts},
    )
    row = result.mappings().first()
    return dict(row) if row else None


if __name__ == "__main__":
    raise SystemExit(main())
