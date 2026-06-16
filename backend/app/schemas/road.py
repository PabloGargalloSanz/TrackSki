from datetime import datetime

from pydantic import BaseModel


class RoadConditionSummary(BaseModel):
    status: str
    severity: str
    details: str | None
    reported_at: datetime


class RoadCondition(BaseModel):
    id: int
    road_id: int
    status: str
    severity: str
    details: str | None
    data_source: str
    is_verified: bool
    reported_at: datetime


class Road(BaseModel):
    id: int
    code: str
    name: str | None
    route: dict | None
    latest_condition: RoadConditionSummary | None
    data_source: str
    is_verified: bool


class RoadIncident(BaseModel):
    id: int
    road_id: int | None
    road_code: str | None
    title: str | None
    description: str | None
    incident_type: str
    status: str
    severity: str
    start_km: float | None
    end_km: float | None
    direction: str | None
    location: dict | None
    affected_route: dict | None
    starts_at: datetime | None
    ends_at: datetime | None
    reported_at: datetime | None
    updated_at: datetime
    source: str
