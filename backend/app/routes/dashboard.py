from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.services.clash_royale import (
    fetch_user_clan_ranking,
    fetch_user_clanwar_ranking,
    fetch_current_riverrace_for_tag,
    fetch_clan_members,
    fetch_clan_by_tag,
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

    if user_clan:
        clan_name    = user_clan.get("name")
        clan_score   = user_clan.get("clanScore")
        member_count = user_clan.get("members")
        leaderboard  = user_clan.get("rank")
    else:
        # Clan außerhalb Top-1000 → kein Ranking-Eintrag, Fallback aufs Clan-Endpoint.
        # Trifft mit hoher Wahrscheinlichkeit den Cache aus Profile-/War-Aufrufen.
        clan = fetch_clan_by_tag(user.clan_tag)
        clan_name    = clan.get("name")
        clan_score   = clan.get("clanScore")
        member_count = clan.get("members")
        leaderboard  = None

    user.clan_ranking = leaderboard
    db.commit()
    db.refresh(user)

    return {
        "username": user.username,
        "clan_name": clan_name,
        "clan_tag": user.clan_tag,
        "leaderboard_rank": leaderboard,
        "trophies": clan_score,
        "members": member_count,
        "location": user.location,
        "war_rank": war_clan.get("rank") if war_clan else None,
    }


@router.get("/war-participants")
def get_war_participants(user: User = Depends(get_current_db_user)):
    if not user.clan_tag:
        return {"is_training": False, "section_index": 0, "war_rank": None,
                "clan_count": 0, "decks_today": 0, "decks_today_max": 0,
                "decks_total": 0, "decks_total_max": 0, "participants": []}

    race = fetch_current_riverrace_for_tag(user.clan_tag)
    is_training = race.get("period_type") == "training"
    section_index = race.get("section_index", 0)
    war_rank = race.get("war_rank")
    clan_count = race.get("clan_count", 0)
    participants = race.get("participants", [])

    current_tags = {m.get("tag") for m in fetch_clan_members(user.clan_tag)}
    days_elapsed = max(section_index + 1, 1)

    enriched = sorted([
        {
            "name": p.get("name"),
            "tag": p.get("tag"),
            "fame": p.get("fame", 0),
            "decks_used": p.get("decksUsed", 0),
            "decks_used_today": p.get("decksUsedToday", 0),
            "boat_attacks": p.get("boatAttacks", 0),
            "is_current_member": p.get("tag") in current_tags,
        }
        for p in participants
    ], key=lambda p: p["fame"], reverse=True)

    count = len(enriched)
    return {
        "is_training": is_training,
        "section_index": section_index,
        "war_rank": war_rank,
        "clan_count": clan_count,
        "decks_today": sum(p["decks_used_today"] for p in enriched),
        "decks_today_max": count * 4,
        "decks_total": sum(p["decks_used"] for p in enriched),
        "decks_total_max": count * 4 * days_elapsed,
        "participants": enriched,
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
    clan_count = race.get("clan_count", 0)

    participants = race.get("participants", [])

    top3 = sorted(participants, key=lambda p: p.get("fame", 0), reverse=True)[:3]

    count = len(participants)
    decks_today = sum(p.get("decksUsedToday", 0) for p in participants)
    decks_total = sum(p.get("decksUsed", 0) for p in participants)
    days_elapsed = max(section_index + 1, 1)
    if is_training:
        missing_today = []
    else:
        current_members = fetch_clan_members(user.clan_tag)
        current_tags = {m.get("tag") for m in current_members}
        missing_today = [
            p.get("name") for p in participants
            if p.get("decksUsedToday", 0) == 0 and p.get("tag") in current_tags
        ]

    return {
        "is_training": is_training,
        "section_index": section_index,
        "war_rank": war_rank,
        "clan_count": clan_count,
        "participant_count": count,
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
