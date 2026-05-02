from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.services.clash_royale import fetch_user_clan_ranking

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(user: User = Depends(get_current_db_user), db: Session = Depends(get_db)):
    if not user.clan_tag:
        return {
            "message": "No clan tag saved for this user",
            "clan_name": None,
            "clan_tag": None,
            "leaderboard_rank": None,
            "trophies": None,
            "members": None,
            "location": user.location,
        }

    if not user.location_id:
        return {
            "message": "No location saved for this user",
            "clan_name": None,
            "clan_tag": user.clan_tag,
            "leaderboard_rank": None,
            "trophies": None,
            "members": None,
            "location": user.location,
        }

    user_clan = fetch_user_clan_ranking(user)
    if not user_clan:
        raise HTTPException(status_code=404, detail="Clan not found in ranking")

    user.clan_ranking = user_clan.get("rank")
    db.commit()
    db.refresh(user)

    return {
        "username": user.username,
        "clan_name": user_clan.get("name"),
        "clan_tag": user.clan_tag,
        "leaderboard_rank": user.clan_ranking,
        "trophies": user_clan.get("clanScore"),
        "members": user_clan.get("members"),
        "location": user.location,
    }

# @router.get("/dashboard/current-riverrace")
# def get_riverrace(user: User = Depends(get_current_db_user)):
#     return get_current_riverrace(user)
 
