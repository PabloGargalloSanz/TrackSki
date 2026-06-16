from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.roads import (
    get_active_road_incidents,
    get_latest_road_condition_by_road_id,
    get_road_by_id,
)
from app.schemas.road import RoadCondition, RoadIncident

router = APIRouter()


def serialize_road_condition(row: dict) -> RoadCondition:
    return RoadCondition(
        id=row["id"],
        road_id=row["road_id"],
        status=row["status"],
        severity=row["severity"],
        details=row["details"],
        data_source=row["data_source"],
        is_verified=row["is_verified"],
        reported_at=row["reported_at"],
    )


def serialize_road_incident(row: dict) -> RoadIncident:
    return RoadIncident(
        id=row["id"],
        road_id=row["road_id"],
        road_code=row["road_code"],
        title=row["title"],
        description=row["description"],
        incident_type=row["incident_type"],
        status=row["status"],
        severity=row["severity"],
        start_km=row["start_km"],
        end_km=row["end_km"],
        direction=row["direction"],
        location=row["location"],
        affected_route=row["affected_route"],
        starts_at=row["starts_at"],
        ends_at=row["ends_at"],
        reported_at=row["reported_at"],
        updated_at=row["updated_at"],
        source=row["source"],
    )


@router.get("/incidents/active", response_model=list[RoadIncident])
def list_active_road_incidents(
    db: Session = Depends(get_db),
) -> list[RoadIncident]:
    return [serialize_road_incident(row) for row in get_active_road_incidents(db)]


@router.get("/{road_id}/conditions/latest", response_model=RoadCondition)
def retrieve_latest_road_condition(
    road_id: int,
    db: Session = Depends(get_db),
) -> RoadCondition:
    road = get_road_by_id(db, road_id)
    if not road:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found",
        )

    condition = get_latest_road_condition_by_road_id(db, road_id)
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road condition not found",
        )

    return serialize_road_condition(condition)
