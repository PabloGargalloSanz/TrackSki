from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TrailStatus(BaseModel):
    open: int
    total: int


class SnowReport(BaseModel):
    id: int
    resort_id: int
    open_lifts: int
    total_lifts: int
    open_km: Decimal
    total_km: Decimal
    snow_depth_min_cm: int | None
    snow_depth_max_cm: int | None
    avalanche_risk: int | None
    access_status: str | None
    green_trails: TrailStatus
    blue_trails: TrailStatus
    red_trails: TrailStatus
    black_trails: TrailStatus
    data_source: str
    is_verified: bool
    reported_at: datetime
