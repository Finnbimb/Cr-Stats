from pydantic import BaseModel


class ClanTagRequest(BaseModel):
    clan_tag: str


class LocationRequest(BaseModel):
    location_id: int

