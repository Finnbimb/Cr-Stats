from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_current_db_user, get_db
from app.models import User, ExcusedPlayer
from time import time

from app.schemas.excused import ExcusedRequest

router = APIRouter()

@router.post("/excused")
def excuse_player(
    request: ExcusedRequest,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    clan_tag = current_user.clan_tag
    now = int(time())
    excused_until = now
    if request.unit == "days":
        excused_until += request.amount * 86400
    else:
        excused_until += request.amount * 86400 * 7
        
    eintrag = ExcusedPlayer(
        player_tag=request.player_tag,
        name= request.name,
        clan_tag = clan_tag,
        reason = request.reason,
        excused_at = now,
        excused_until = excused_until,
    )
    
    db.add(eintrag)
    db.commit()
    
    return {
        "status": "success",
        "player_tag": request.player_tag,
        "name": request.name,
        "reason": request.reason,
        "excused_until": excused_until,
    }
    
@router.get("/excused")
def get_excused(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
):
    clan_tag = current_user.clan_tag
    now = int(time())
    excusedList = (
        db.query(ExcusedPlayer)
        .filter(
            ExcusedPlayer.clan_tag == clan_tag,
            ExcusedPlayer.excused_until > now,
        )
        .all()
    )
    
    return [
        {"player_tag": excusedPlayer.player_tag, "name": excusedPlayer.name, "reason": excusedPlayer.reason, "excused_at": excusedPlayer.excused_at, "excused_until": excusedPlayer.excused_until} 
        for excusedPlayer in excusedList
    ]
