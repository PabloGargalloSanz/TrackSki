from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class TrailBreakdown:
    open: int = 0
    total: int = 0


@dataclass(frozen=True)
class SnowReportData:
    reported_at: datetime
    open_lifts: int = 0
    total_lifts: int = 0
    open_km: Decimal = Decimal("0")
    total_km: Decimal = Decimal("0")
    snow_depth_min_cm: int | None = None
    snow_depth_max_cm: int | None = None
    avalanche_risk: int | None = None
    access_status: str | None = None
    green_trails: TrailBreakdown = TrailBreakdown()
    blue_trails: TrailBreakdown = TrailBreakdown()
    red_trails: TrailBreakdown = TrailBreakdown()
    black_trails: TrailBreakdown = TrailBreakdown()
    data_source: str = "manual"
    is_verified: bool = False
