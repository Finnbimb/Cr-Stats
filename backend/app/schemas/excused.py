from typing import Literal

from pydantic import BaseModel

class ExcusedRequest(BaseModel):
    player_tag : str
    name : str
    amount: int
    unit : Literal["days", "weeks"]
    reason: str