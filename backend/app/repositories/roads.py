from sqlalchemy import text
from sqlalchemy.orm import Session


def get_roads_by_resort_id(db: Session, resort_id: int) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                roads.id,
                roads.code,
                roads.name,
                ST_AsGeoJSON(roads.route)::json AS route,
                roads.data_source,
                roads.is_verified,
                latest_condition.status AS latest_status,
                latest_condition.severity AS latest_severity,
                latest_condition.details AS latest_details,
                latest_condition.reported_at AS latest_reported_at
            FROM roads
            INNER JOIN resort_access_roads
                ON resort_access_roads.road_id = roads.id
            LEFT JOIN LATERAL (
                SELECT
                    road_conditions.status,
                    road_conditions.severity,
                    road_conditions.details,
                    road_conditions.reported_at
                FROM road_conditions
                WHERE road_conditions.road_id = roads.id
                ORDER BY road_conditions.reported_at DESC, road_conditions.id DESC
                LIMIT 1
            ) AS latest_condition ON TRUE
            WHERE resort_access_roads.resort_id = :resort_id
              AND resort_access_roads.is_active = TRUE
            ORDER BY resort_access_roads.priority, roads.code
            """
        ),
        {"resort_id": resort_id},
    )

    return [dict(row) for row in result.mappings()]


def get_road_by_id(db: Session, road_id: int) -> dict | None:
    result = db.execute(
        text(
            """
            SELECT
                id,
                code,
                name,
                ST_AsGeoJSON(route)::json AS route,
                data_source,
                is_verified
            FROM roads
            WHERE id = :road_id
            """
        ),
        {"road_id": road_id},
    )

    row = result.mappings().one_or_none()
    return dict(row) if row else None


def get_latest_road_condition_by_road_id(db: Session, road_id: int) -> dict | None:
    result = db.execute(
        text(
            """
            SELECT
                id,
                road_id,
                status,
                severity,
                details,
                data_source,
                is_verified,
                reported_at
            FROM road_conditions
            WHERE road_id = :road_id
            ORDER BY reported_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"road_id": road_id},
    )

    row = result.mappings().one_or_none()
    return dict(row) if row else None
