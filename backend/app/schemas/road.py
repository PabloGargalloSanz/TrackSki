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
    access_role: str | None = None


class ResortAccessRoad(BaseModel):
    id: int
    road: Road
    access_role: str
    segment_description: str | None
    from_km: float | None
    to_km: float | None
    priority: int


class RoadAlternative(BaseModel):
    id: int
    affected_road_id: int | None
    alternative_road_id: int | None
    title: str
    description: str
    priority: int


class ResortAccessStatusResponse(BaseModel):
    resort_id: int
    overall_status: str
    roads: list[ResortAccessRoad]
    incidents: list[RoadIncident]
    alternatives: list[RoadAlternative]
