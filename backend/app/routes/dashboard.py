from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.services.clash_royale import (
    fetch_user_clan_ranking,
    fetch_user_clanwar_ranking,
    fetch_current_riverrace_for_tag,
    fetch_riverracelog_participants,
)

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(user: User = Depends(get_current_db_user), db: Session = Depends(get_db)):
    if not user.clan_tag:
        return {
            "message": "No clan tag saved for this user",
            "clan_name": None, "clan_tag": None, "leaderboard_rank": None,
            "trophies": None, "members": None, "location": user.location,
            "war_rank": None,
        }

    if not user.location_id:
        return {
            "message": "No location saved for this user",
            "clan_name": None, "clan_tag": user.clan_tag, "leaderboard_rank": None,
            "trophies": None, "members": None, "location": user.location,
            "war_rank": None,
        }

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_clan = ex.submit(fetch_user_clan_ranking, user)
        f_war  = ex.submit(fetch_user_clanwar_ranking, user)
        user_clan = f_clan.result()
        war_clan  = f_war.result()

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
        "war_rank": war_clan.get("rank") if war_clan else None,
    }


@router.get("/war-performers")
def get_war_performers(user: User = Depends(get_current_db_user)):
    if not user.clan_tag:
        return {"is_training": False, "performers": []}

    race = fetch_current_riverrace_for_tag(user.clan_tag)
    is_training = race.get("period_type") == "training"

    participants = (
        fetch_riverracelog_participants(user.clan_tag)
        if is_training
        else race.get("participants", [])
    )

    top3 = sorted(participants, key=lambda p: p.get("fame", 0), reverse=True)[:3]

    return {
        "is_training": is_training,
        "performers": [
            {
                "rank": i + 1,
                "name": p.get("name"),
                "tag": p.get("tag"),
                "fame": p.get("fame", 0),
            }
            for i, p in enumerate(top3)
        ],
    }
