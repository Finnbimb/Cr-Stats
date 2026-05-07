from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import ClanRankingSnapshot, User
from app.services.clash_royale import (
    fetch_riverracelog,
    normalize_clan_tag,
    parse_cr_timestamp,
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


def _nearest_war_rank_snapshot(snapshots: list, target_ts: int):
    """Find snapshot closest in time to target_ts whose war_rank is set."""
    if not snapshots or not target_ts:
        return None
    target_date = datetime.fromtimestamp(target_ts, tz=timezone.utc).date()
    best = None
    best_delta = None
    for s in snapshots:
        if s.war_rank is None:
            continue
        try:
            s_date = datetime.strptime(s.snapshot_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        delta = abs((s_date - target_date).days)
        if best_delta is None or delta < best_delta:
            best = s
            best_delta = delta
    if best is None or best_delta is None or best_delta > 14:
        return None
    return best


@router.get("/rankings/war-log")
def get_war_log(
    user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
):
    if not user.clan_tag:
        return {"wars": []}

    clan_tag = normalize_clan_tag(user.clan_tag)

    try:
        items = fetch_riverracelog(clan_tag)
    except HTTPException:
        return {"wars": []}

    snapshots = (
        db.query(ClanRankingSnapshot)
        .filter(ClanRankingSnapshot.clan_tag == clan_tag)
        .all()
    )

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
        race_rank = own.get("rank")
        # CR API's clan.fame is unreliable — bricht außer in der Finalwoche jeder
        # Season auf einen kleinen Bruchstückwert zusammen. Echtes Total
        # = Summe der Spieler-Fame.
        participants = clan.get("participants", []) or []
        fame = sum((p or {}).get("fame", 0) for p in participants)
        season = item.get("seasonId")
        section = item.get("sectionIndex")
        created_at_raw = item.get("createdDate")
        created_at = parse_cr_timestamp(created_at_raw) if created_at_raw else None

        nearest = _nearest_war_rank_snapshot(snapshots, created_at)
        leaderboard_rank = nearest.war_rank if nearest else None

        wars.append({
            "season_id": season,
            "section_index": section,
            "race_rank": race_rank,
            "leaderboard_rank": leaderboard_rank,
            "fame": fame,
            "created_at": created_at,
        })

    wars.sort(key=lambda w: (w["created_at"] or 0))

    return {"wars": wars}
