from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.snow.models import SnowReportData


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


def create_snow_report_if_missing(
    db: Session,
    resort_id: int,
    report: SnowReportData,
) -> int | None:
    result = db.execute(
        text(
            """
            INSERT INTO snow_reports (
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
            )
            SELECT
                :resort_id,
                :open_lifts,
                :total_lifts,
                :open_km,
                :total_km,
                :snow_depth_min_cm,
                :snow_depth_max_cm,
                :avalanche_risk,
                :access_status,
                :open_green_trails,
                :total_green_trails,
                :open_blue_trails,
                :total_blue_trails,
                :open_red_trails,
                :total_red_trails,
                :open_black_trails,
                :total_black_trails,
                CAST(:data_source AS VARCHAR(100)),
                :is_verified,
                :reported_at
            WHERE NOT EXISTS (
                SELECT 1
                FROM snow_reports
                WHERE resort_id = :resort_id
                  AND data_source = CAST(:data_source AS VARCHAR(100))
                  AND reported_at = :reported_at
            )
            RETURNING id
            """
        ),
        {
            "resort_id": resort_id,
            "open_lifts": report.open_lifts,
            "total_lifts": report.total_lifts,
            "open_km": report.open_km,
            "total_km": report.total_km,
            "snow_depth_min_cm": report.snow_depth_min_cm,
            "snow_depth_max_cm": report.snow_depth_max_cm,
            "avalanche_risk": report.avalanche_risk,
            "access_status": report.access_status,
            "open_green_trails": report.green_trails.open,
            "total_green_trails": report.green_trails.total,
            "open_blue_trails": report.blue_trails.open,
            "total_blue_trails": report.blue_trails.total,
            "open_red_trails": report.red_trails.open,
            "total_red_trails": report.red_trails.total,
            "open_black_trails": report.black_trails.open,
            "total_black_trails": report.black_trails.total,
            "data_source": report.data_source,
            "is_verified": report.is_verified,
            "reported_at": report.reported_at,
        },
    )

    return result.scalar_one_or_none()
