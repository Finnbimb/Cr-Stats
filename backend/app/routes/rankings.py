import requests
from urllib.parse import quote
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import ClanRankingSnapshot, User
from app.services.clash_royale import (
    get_cr_api_headers,
    raise_for_clash_api_error,
    normalize_clan_tag,
    parse_cr_timestamp,
    find_clan_by_tag,
)
from app.services.ranking_snapshots import take_snapshot_for_clan

router = APIRouter()


@router.get("/rankings/history")
def get_rankings_history(
    user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
):
    if not user.clan_tag or not user.location_id:
        return {
            "clan_tag": user.clan_tag,
            "location": user.location,
            "snapshots": [],
            "has_clan": bool(user.clan_tag),
            "has_location": bool(user.location_id),
        }

    try:
        take_snapshot_for_clan(user.clan_tag, user.location_id, user.location)
    except Exception as exc:
        print(f"[rankings] inline snapshot failed: {exc}")

    rows = (
        db.query(ClanRankingSnapshot)
        .filter(ClanRankingSnapshot.clan_tag == user.clan_tag)
        .order_by(ClanRankingSnapshot.snapshot_date.asc())
        .all()
    )

    snapshots = [
        {
            "date": r.snapshot_date,
            "trophy_rank": r.trophy_rank,
            "war_rank": r.war_rank,
            "clan_score": r.clan_score,
            "clan_war_trophies": r.clan_war_trophies,
        }
        for r in rows
    ]

    return {
        "clan_tag": user.clan_tag,
        "location": user.location,
        "snapshots": snapshots,
        "has_clan": True,
        "has_location": True,
    }


@router.get("/rankings/war-log")
def get_war_log(user: User = Depends(get_current_db_user)):
    if not user.clan_tag:
        return {"wars": []}

    clan_tag = normalize_clan_tag(user.clan_tag)
    encoded_tag = quote(clan_tag)

    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/clans/{encoded_tag}/riverracelog",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException:
        return {"wars": []}

    raise_for_clash_api_error(response, "Failed to load river race log")
    items = response.json().get("items", [])

    wars = []
    for item in items:
        standings = item.get("standings", []) or []
        own = next(
            (
                s for s in standings
                if normalize_clan_tag((s.get("clan") or {}).get("tag", "") or "#") == clan_tag
            ),
            None,
        )
        if not own:
            continue

        clan = own.get("clan", {})
        rank = own.get("rank")
        fame = clan.get("fame")
        season = item.get("seasonId")
        section = item.get("sectionIndex")
        created_at = item.get("createdDate")

        wars.append({
            "season_id": season,
            "section_index": section,
            "rank": rank,
            "fame": fame,
            "created_at": parse_cr_timestamp(created_at) if created_at else None,
        })

    wars.sort(key=lambda w: (w["created_at"] or 0))

    return {"wars": wars}
