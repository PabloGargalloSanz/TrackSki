from sqlalchemy import text
from sqlalchemy.orm import Session


def get_resorts(db: Session) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                id,
                name,
                country,
                region,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                data_source,
                is_verified
            FROM ski_resorts
            ORDER BY name
            """
        )
    )

    return [dict(row) for row in result.mappings()]


def get_resort_by_id(db: Session, resort_id: int) -> dict | None:
    result = db.execute(
        text(
            """
            SELECT
                id,
                name,
                country,
                region,
                ST_X(location::geometry) AS longitude,
                ST_Y(location::geometry) AS latitude,
                data_source,
                is_verified
            FROM ski_resorts
            WHERE id = :resort_id
            """
        ),
        {"resort_id": resort_id},
    )

    row = result.mappings().one_or_none()
    return dict(row) if row else None
