from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.roads import (
    get_latest_road_condition_by_road_id,
    get_road_by_id,
)
from app.schemas.road import RoadCondition

router = APIRouter()


def serialize_road_condition(row: dict) -> RoadCondition:
    return RoadCondition(
        id=row["id"],
        road_id=row["road_id"],
        status=row["status"],
        details=row["details"],
        data_source=row["data_source"],
        is_verified=row["is_verified"],
        reported_at=row["reported_at"],
    )


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
