import json
from datetime import datetime
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.scrapers.dgt_datex2 import NormalizedRoadIncident


def get_roads(db: Session) -> list[dict]:
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
            ORDER BY roads.code, roads.id
            """
        )
    )

    return [dict(row) for row in result.mappings()]


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


def get_best_road_id_by_code(db: Session, road_code: str) -> int | None:
    result = db.execute(
        text(
            """
            SELECT id
            FROM roads
            WHERE code = :road_code
              AND data_source IN ('manual', 'dgt_datex2_v37', 'dgt')
            ORDER BY
                is_verified DESC,
                CASE data_source
                    WHEN 'manual' THEN 1
                    WHEN 'dgt_datex2_v37' THEN 2
                    WHEN 'dgt' THEN 3
                    ELSE 4
                END,
                id
            LIMIT 1
            """
        ),
        {"road_code": road_code},
    )

    return result.scalar_one_or_none()


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


def create_road_condition(
    db: Session,
    *,
    road_id: int,
    status: str,
    severity: str = "unknown",
    details: str | None = None,
    data_source: str = "manual",
    is_verified: bool = False,
    source_updated_at: datetime | None = None,
    raw_payload: dict[str, Any] | None = None,
    reported_at: datetime | None = None,
) -> int:
    result = db.execute(
        text(
            """
            INSERT INTO road_conditions (
                road_id,
                status,
                severity,
                details,
                data_source,
                is_verified,
                source_updated_at,
                raw_payload,
                reported_at
            )
            VALUES (
                :road_id,
                :status,
                :severity,
                :details,
                :data_source,
                :is_verified,
                :source_updated_at,
                CAST(:raw_payload AS JSONB),
                COALESCE(
                    CAST(:reported_at AS TIMESTAMP WITH TIME ZONE),
                    CURRENT_TIMESTAMP
                )
            )
            RETURNING id
            """
        ),
        {
            "road_id": road_id,
            "status": status,
            "severity": severity,
            "details": details,
            "data_source": data_source,
            "is_verified": is_verified,
            "source_updated_at": source_updated_at,
            "raw_payload": (
                json.dumps(raw_payload) if raw_payload is not None else None
            ),
            "reported_at": reported_at,
        },
    )

    return result.scalar_one()


def upsert_road_incident(
    db: Session,
    incident: NormalizedRoadIncident,
    road_id: int | None,
) -> int:
    result = db.execute(
        text(
            """
            INSERT INTO road_incidents (
                road_id,
                source,
                source_id,
                road_code,
                title,
                description,
                incident_type,
                status,
                severity,
                start_km,
                end_km,
                direction,
                location,
                starts_at,
                ends_at,
                reported_at,
                updated_at,
                raw_payload
            )
            VALUES (
                :road_id,
                :source,
                :source_id,
                :road_code,
                :title,
                :description,
                :incident_type,
                :status,
                :severity,
                :start_km,
                :end_km,
                :direction,
                CASE
                    WHEN :longitude IS NULL OR :latitude IS NULL THEN NULL
                    ELSE ST_SetSRID(
                        ST_MakePoint(:longitude, :latitude),
                        4326
                    )
                END,
                :starts_at,
                :ends_at,
                :reported_at,
                COALESCE(
                    CAST(:updated_at AS TIMESTAMP WITH TIME ZONE),
                    CURRENT_TIMESTAMP
                ),
                CAST(:raw_payload AS JSONB)
            )
            ON CONFLICT (source, source_id)
            DO UPDATE SET
                road_id = EXCLUDED.road_id,
                road_code = EXCLUDED.road_code,
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                incident_type = EXCLUDED.incident_type,
                status = EXCLUDED.status,
                severity = EXCLUDED.severity,
                start_km = EXCLUDED.start_km,
                end_km = EXCLUDED.end_km,
                direction = EXCLUDED.direction,
                location = EXCLUDED.location,
                starts_at = EXCLUDED.starts_at,
                ends_at = EXCLUDED.ends_at,
                reported_at = EXCLUDED.reported_at,
                updated_at = EXCLUDED.updated_at,
                raw_payload = EXCLUDED.raw_payload
            RETURNING id
            """
        ),
        {
            "road_id": road_id,
            "source": incident.source,
            "source_id": incident.source_id,
            "road_code": incident.road_code,
            "title": incident.title,
            "description": incident.description,
            "incident_type": incident.incident_type,
            "status": incident.status,
            "severity": incident.severity,
            "start_km": incident.start_km,
            "end_km": incident.end_km,
            "direction": incident.direction,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "starts_at": incident.starts_at,
            "ends_at": incident.ends_at,
            "reported_at": incident.reported_at,
            "updated_at": incident.updated_at,
            "raw_payload": json.dumps(incident.raw_payload),
        },
    )

    return result.scalar_one()


def get_active_road_incidents(db: Session) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                id,
                road_id,
                source,
                road_code,
                title,
                description,
                incident_type,
                status,
                severity,
                start_km,
                end_km,
                direction,
                ST_AsGeoJSON(location)::json AS location,
                ST_AsGeoJSON(affected_route)::json AS affected_route,
                starts_at,
                ends_at,
                reported_at,
                updated_at
            FROM road_incidents
            WHERE status IN ('active', 'planned')
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                updated_at DESC,
                id DESC
            """
        )
    )

    return [dict(row) for row in result.mappings()]


def get_access_roads_by_resort_id(db: Session, resort_id: int) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                resort_access_roads.id AS access_id,
                resort_access_roads.access_role,
                resort_access_roads.segment_description,
                resort_access_roads.from_km,
                resort_access_roads.to_km,
                resort_access_roads.priority,
                roads.id AS road_id,
                roads.code,
                roads.name,
                ST_AsGeoJSON(roads.route)::json AS route,
                roads.data_source,
                roads.is_verified,
                latest_condition.status AS latest_status,
                latest_condition.severity AS latest_severity,
                latest_condition.details AS latest_details,
                latest_condition.reported_at AS latest_reported_at
            FROM resort_access_roads
            INNER JOIN roads ON roads.id = resort_access_roads.road_id
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


def get_active_road_incidents_for_road_ids(
    db: Session,
    road_ids: list[int],
) -> list[dict]:
    if not road_ids:
        return []

    statement = text(
        """
            SELECT
                id,
                road_id,
                source,
                road_code,
                title,
                description,
                incident_type,
                status,
                severity,
                start_km,
                end_km,
                direction,
                ST_AsGeoJSON(location)::json AS location,
                ST_AsGeoJSON(affected_route)::json AS affected_route,
                starts_at,
                ends_at,
                reported_at,
                updated_at
            FROM road_incidents
            WHERE status IN ('active', 'planned')
              AND road_id IN :road_ids
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                updated_at DESC,
                id DESC
        """
    ).bindparams(bindparam("road_ids", expanding=True))

    result = db.execute(
        statement,
        {"road_ids": road_ids},
    )

    return [dict(row) for row in result.mappings()]


def get_road_alternatives_by_resort_id(db: Session, resort_id: int) -> list[dict]:
    result = db.execute(
        text(
            """
            SELECT
                id,
                affected_road_id,
                alternative_road_id,
                title,
                description,
                priority
            FROM road_alternatives
            WHERE resort_id = :resort_id
              AND is_active = TRUE
            ORDER BY priority, id
            """
        ),
        {"resort_id": resort_id},
    )

    return [dict(row) for row in result.mappings()]
