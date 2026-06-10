from sqlalchemy import text
from sqlalchemy.orm import Session


def get_latest_snow_report_by_resort_id(db: Session, resort_id: int) -> dict | None:
    result = db.execute(
        text(
            """
            SELECT
                id,
                resort_id,
                open_lifts,
                total_lifts,
                open_km,
                total_km,
                snow_depth_min_cm,
                snow_depth_max_cm,
                avalanche_risk,
                access_status,
                open_green_trails,
                total_green_trails,
                open_blue_trails,
                total_blue_trails,
                open_red_trails,
                total_red_trails,
                open_black_trails,
                total_black_trails,
                data_source,
                is_verified,
                reported_at
            FROM snow_reports
            WHERE resort_id = :resort_id
            ORDER BY reported_at DESC, id DESC
            LIMIT 1
            """
        ),
        {"resort_id": resort_id},
    )

    row = result.mappings().one_or_none()
    return dict(row) if row else None


def get_snow_reports_by_resort_id(
    db: Session,
    resort_id: int,
    limit: int,
) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                id,
                resort_id,
                open_lifts,
                total_lifts,
                open_km,
                total_km,
                snow_depth_min_cm,
                snow_depth_max_cm,
                avalanche_risk,
                access_status,
                open_green_trails,
                total_green_trails,
                open_blue_trails,
                total_blue_trails,
                open_red_trails,
                total_red_trails,
                open_black_trails,
                total_black_trails,
                data_source,
                is_verified,
                reported_at
            FROM snow_reports
            WHERE resort_id = :resort_id
            ORDER BY reported_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {"resort_id": resort_id, "limit": limit},
    )

    return [dict(row) for row in result.mappings()]
