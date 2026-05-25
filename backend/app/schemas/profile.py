from pydantic import BaseModel


class ClanTagRequest(BaseModel):
    clan_tag: str
    
class PlayerTagRequest(BaseModel):
    token: str
    player_tag: str
    
