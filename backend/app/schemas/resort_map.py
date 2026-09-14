from pydantic import BaseModel

from app.schemas.resort import Resort
from app.schemas.road import ResortAccessRoad, RoadIncident


class ResortMap(BaseModel):
    resort: Resort
    overall_status: str
    roads: list[ResortAccessRoad]
    incidents: list[RoadIncident]
