from sqlalchemy import text
from sqlalchemy.orm import Session


def get_roads_by_resort_id(db: Session, resort_id: int) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                roads.id,
                roads.resort_id,
                roads.name,
                ST_AsGeoJSON(roads.route)::json AS route,
                roads.data_source,
                roads.is_verified,
                latest_condition.status AS latest_status,
                latest_condition.details AS latest_details,
                latest_condition.reported_at AS latest_reported_at
            FROM roads
            LEFT JOIN LATERAL (
                SELECT
                    road_conditions.status,
                    road_conditions.details,
                    road_conditions.reported_at
                FROM road_conditions
                WHERE road_conditions.road_id = roads.id
                ORDER BY road_conditions.reported_at DESC, road_conditions.id DESC
                LIMIT 1
            ) AS latest_condition ON TRUE
            WHERE roads.resort_id = :resort_id
            ORDER BY roads.name
            """
        ),
        {"resort_id": resort_id},
    )

    return [dict(row) for row in result.mappings()]
