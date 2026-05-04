from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.services.clash_royale import (
    fetch_user_clan_ranking,
    fetch_user_clanwar_ranking,
    fetch_current_riverrace_for_tag,
    fetch_clan_members,
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
        return {"is_training": False, "performers": [], "decks_today": 0,
                "decks_today_max": 0, "decks_total": 0, "decks_total_max": 0,
                "missing_today": [], "section_index": 0}

    race = fetch_current_riverrace_for_tag(user.clan_tag)
    is_training = race.get("period_type") == "training"
    section_index = race.get("section_index", 0)
    war_rank = race.get("war_rank")

    participants = race.get("participants", [])

    top3 = sorted(participants, key=lambda p: p.get("fame", 0), reverse=True)[:3]

    count = len(participants)
    decks_today = sum(p.get("decksUsedToday", 0) for p in participants)
    decks_total = sum(p.get("decksUsed", 0) for p in participants)
    days_elapsed = max(section_index + 1, 1)
    if is_training:
        missing_today = []
    else:
        current_tags = {m.get("tag") for m in fetch_clan_members(user.clan_tag)}
        missing_today = [
            p.get("name") for p in participants
            if p.get("decksUsedToday", 0) == 0 and p.get("tag") in current_tags
        ]

    return {
        "is_training": is_training,
        "section_index": section_index,
        "war_rank": war_rank,
        "performers": [
            {
                "rank": i + 1,
                "name": p.get("name"),
                "tag": p.get("tag"),
                "fame": p.get("fame", 0),
            }
            for i, p in enumerate(top3)
        ],
        "decks_today": decks_today,
        "decks_today_max": count * 4,
        "decks_total": decks_total,
        "decks_total_max": count * 4 * days_elapsed,
        "missing_today": missing_today,
    }
