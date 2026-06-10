from pydantic import BaseModel


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class Resort(BaseModel):
    id: int
    name: str
    country: str
    region: str | None
    location: Coordinates
    data_source: str
    is_verified: bool
