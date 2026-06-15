from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.roads import get_roads_by_resort_id
from app.repositories.resorts import get_resort_by_id, get_resorts
from app.repositories.snow_reports import (
    get_latest_snow_report_by_resort_id,
    get_snow_reports_by_resort_id,
)
from app.repositories.weather_reports import (
    get_latest_weather_report_by_resort_id,
    get_weather_reports_by_resort_id,
)
from app.schemas.road import Road, RoadConditionSummary
from app.schemas.resort import Coordinates, Resort
from app.schemas.resort_summary import ResortSummary
from app.schemas.snow_report import SnowReport, TrailStatus
from app.schemas.weather_report import WeatherReport

router = APIRouter()
ReportLimit = Annotated[int, Query(ge=1, le=100)]


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


def serialize_snow_report(row: dict) -> SnowReport:
    return SnowReport(
        id=row["id"],
        resort_id=row["resort_id"],
        open_lifts=row["open_lifts"],
        total_lifts=row["total_lifts"],
        open_km=row["open_km"],
        total_km=row["total_km"],
        snow_depth_min_cm=row["snow_depth_min_cm"],
        snow_depth_max_cm=row["snow_depth_max_cm"],
        avalanche_risk=row["avalanche_risk"],
        access_status=row["access_status"],
        green_trails=TrailStatus(
            open=row["open_green_trails"],
            total=row["total_green_trails"],
        ),
        blue_trails=TrailStatus(
            open=row["open_blue_trails"],
            total=row["total_blue_trails"],
        ),
        red_trails=TrailStatus(
            open=row["open_red_trails"],
            total=row["total_red_trails"],
        ),
        black_trails=TrailStatus(
            open=row["open_black_trails"],
            total=row["total_black_trails"],
        ),
        data_source=row["data_source"],
        is_verified=row["is_verified"],
        reported_at=row["reported_at"],
    )


def serialize_weather_report(row: dict) -> WeatherReport:
    return WeatherReport(
        id=row["id"],
        resort_id=row["resort_id"],
        temperature_celsius=row["temperature_celsius"],
        wind_speed_kmh=row["wind_speed_kmh"],
        wind_direction=row["wind_direction"],
        precipitation_mm=row["precipitation_mm"],
        visibility_m=row["visibility_m"],
        weather=row["weather"],
        data_source=row["data_source"],
        is_verified=row["is_verified"],
        reported_at=row["reported_at"],
    )


def serialize_road(row: dict) -> Road:
    latest_condition = None
    if row["latest_status"] and row["latest_reported_at"]:
        latest_condition = RoadConditionSummary(
            status=row["latest_status"],
            details=row["latest_details"],
            reported_at=row["latest_reported_at"],
        )

    return Road(
        id=row["id"],
        resort_id=row["resort_id"],
        name=row["name"],
        route=row["route"],
        latest_condition=latest_condition,
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


@router.get("/{resort_id}/summary", response_model=ResortSummary)
def retrieve_resort_summary(
    resort_id: int,
    db: Session = Depends(get_db),
) -> ResortSummary:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    snow_report = get_latest_snow_report_by_resort_id(db, resort_id)
    weather_report = get_latest_weather_report_by_resort_id(db, resort_id)
    roads = get_roads_by_resort_id(db, resort_id)

    return ResortSummary(
        resort=serialize_resort(resort),
        latest_snow_report=(
            serialize_snow_report(snow_report) if snow_report else None
        ),
        latest_weather_report=(
            serialize_weather_report(weather_report) if weather_report else None
        ),
        roads=[serialize_road(row) for row in roads],
    )


@router.get("/{resort_id}/snow-reports/latest", response_model=SnowReport)
def retrieve_latest_snow_report(
    resort_id: int,
    db: Session = Depends(get_db),
) -> SnowReport:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    snow_report = get_latest_snow_report_by_resort_id(db, resort_id)
    if not snow_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snow report not found",
        )

    return serialize_snow_report(snow_report)


@router.get("/{resort_id}/snow-reports", response_model=list[SnowReport])
def list_snow_reports(
    resort_id: int,
    limit: ReportLimit = 20,
    db: Session = Depends(get_db),
) -> list[SnowReport]:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    return [
        serialize_snow_report(row)
        for row in get_snow_reports_by_resort_id(db, resort_id, limit)
    ]


@router.get("/{resort_id}/weather/latest", response_model=WeatherReport)
def retrieve_latest_weather_report(
    resort_id: int,
    db: Session = Depends(get_db),
) -> WeatherReport:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    weather_report = get_latest_weather_report_by_resort_id(db, resort_id)
    if not weather_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weather report not found",
        )

    return serialize_weather_report(weather_report)


@router.get("/{resort_id}/weather", response_model=list[WeatherReport])
def list_weather_reports(
    resort_id: int,
    limit: ReportLimit = 20,
    db: Session = Depends(get_db),
) -> list[WeatherReport]:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    return [
        serialize_weather_report(row)
        for row in get_weather_reports_by_resort_id(db, resort_id, limit)
    ]


@router.get("/{resort_id}/roads", response_model=list[Road])
def list_resort_roads(
    resort_id: int,
    db: Session = Depends(get_db),
) -> list[Road]:
    resort = get_resort_by_id(db, resort_id)
    if not resort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resort not found",
        )

    return [serialize_road(row) for row in get_roads_by_resort_id(db, resort_id)]
