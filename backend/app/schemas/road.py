from datetime import datetime

from pydantic import BaseModel


class RoadConditionSummary(BaseModel):
    status: str
    details: str | None
    reported_at: datetime


class Road(BaseModel):
    id: int
    resort_id: int | None
    name: str
    route: dict
    latest_condition: RoadConditionSummary | None
    data_source: str
    is_verified: bool
