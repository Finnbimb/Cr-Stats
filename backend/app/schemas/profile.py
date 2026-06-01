from pydantic import BaseModel


class ClanTagRequest(BaseModel):
    clan_tag: str
