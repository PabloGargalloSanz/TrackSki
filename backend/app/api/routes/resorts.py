from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.resorts import get_resort_by_id, get_resorts
from app.schemas.resort import Coordinates, Resort

router = APIRouter()


def serialize_resort(row: dict) -> Resort:
    return Resort(
        id=row["id"],
        name=row["name"],
        country=row["country"],
        region=row["region"],
        location=Coordinates(
            latitude=row["latitude"],
            longitude=row["longitude"],
        ),
        data_source=row["data_source"],
        is_verified=row["is_verified"],
    )


@router.get("", response_model=list[Resort])
def list_resorts(db: Session = Depends(get_db)) -> list[Resort]:
    return [serialize_resort(row) for row in get_resorts(db)]


@router.get("/{resort_id}", response_model=Resort)
def retrieve_resort(resort_id: int, db: Session = Depends(get_db)) -> Resort:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    return serialize_resort(resort)
