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
