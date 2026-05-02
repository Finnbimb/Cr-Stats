from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.services.clash_royale import (
    GERMANY_LOCATION_NAME,
    fetch_ranked_clan_for_location,
    fetch_user_clan_ranking,
)

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(user: User = Depends(get_current_db_user), db: Session = Depends(get_db)):
    if not user.clan_tag:
        return {
            "message": "No clan tag saved for this user",
            "clan_name": None, "clan_tag": None, "leaderboard_rank": None,
            "trophies": None, "members": None, "location": user.location,
            "germany_rank": None, "germany_war_rank": None,
        }

    if not user.location_id:
        return {
            "message": "No location saved for this user",
            "clan_name": None, "clan_tag": user.clan_tag, "leaderboard_rank": None,
            "trophies": None, "members": None, "location": user.location,
            "germany_rank": None, "germany_war_rank": None,
        }

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_clan     = ex.submit(fetch_user_clan_ranking, user)
        f_germany  = ex.submit(fetch_ranked_clan_for_location,
                        ranking_path="rankings/clans",
                        fallback_detail="Failed to load Germany trophy ranking",
                        clan_tag=user.clan_tag)
        f_war      = ex.submit(fetch_ranked_clan_for_location,
                        ranking_path="rankings/clanwars",
                        fallback_detail="Failed to load Germany war ranking",
                        clan_tag=user.clan_tag)
        user_clan    = f_clan.result()
        germany_clan = f_germany.result()
        germany_war  = f_war.result()

    if not user_clan:
        raise HTTPException(status_code=404, detail="Clan not found in ranking")

    user.clan_ranking = user_clan.get("rank")
    db.commit()
    db.refresh(user)

    germany_rank = germany_clan.get("rank") if germany_clan else None
    if germany_rank is None and user.location == GERMANY_LOCATION_NAME:
        germany_rank = user_clan.get("rank")

    return {
        "username": user.username,
        "clan_name": user_clan.get("name"),
        "clan_tag": user.clan_tag,
        "leaderboard_rank": user.clan_ranking,
        "trophies": user_clan.get("clanScore"),
        "members": user_clan.get("members"),
        "location": user.location,
        "germany_rank": germany_rank,
        "germany_war_rank": germany_war.get("rank") if germany_war else None,
    }
