import asyncio
from datetime import datetime, timezone
from time import time

from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import ClanRankingSnapshot, User
from app.services.clash_royale import (
    cached_get,
    find_clan_by_tag,
    fetch_clan_by_tag,
)


SNAPSHOT_INTERVAL_SECONDS = 60 * 60  # check once per hour, dedupe by date


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch_clan_in_ranking(location_id: int, ranking_path: str, clan_tag: str):
    """Fetch a single ranking page, return our clan's entry or None."""
    try:
        data = cached_get(
            f"https://api.clashroyale.com/v1/locations/{location_id}/{ranking_path}",
            ttl=600,
            fallback_detail="Failed to load ranking",
        )
    except HTTPException:
        return None
    clans = data.get("items", [])
    return find_clan_by_tag(clans, clan_tag)


def take_snapshot_for_clan(clan_tag: str, location_id: int, location_name: str | None):
    """Snapshot current trophy + war rank for one clan into DB. Idempotent per day."""
    db = SessionLocal()
    try:
        date = today_str()

        existing = (
            db.query(ClanRankingSnapshot)
            .filter(
                ClanRankingSnapshot.clan_tag == clan_tag,
                ClanRankingSnapshot.snapshot_date == date,
            )
            .first()
        )
        if existing:
            return False

        trophy_entry = fetch_clan_in_ranking(location_id, "rankings/clans", clan_tag)
        war_entry = fetch_clan_in_ranking(location_id, "rankings/clanwars", clan_tag)

        clan_score = trophy_entry.get("clanScore") if trophy_entry else None
        clan_war_trophies = war_entry.get("clanWarTrophies") if war_entry else None

        if clan_score is None or clan_war_trophies is None:
            try:
                clan = fetch_clan_by_tag(clan_tag)
                clan_score = clan_score or clan.get("clanScore")
                clan_war_trophies = clan_war_trophies or clan.get("clanWarTrophies")
            except Exception:
                pass

        snapshot = ClanRankingSnapshot(
            clan_tag=clan_tag,
            location_id=location_id,
            location_name=location_name,
            snapshot_date=date,
            trophy_rank=trophy_entry.get("rank") if trophy_entry else None,
            war_rank=war_entry.get("rank") if war_entry else None,
            clan_score=clan_score,
            clan_war_trophies=clan_war_trophies,
            captured_at=int(time()),
        )
        db.add(snapshot)
        try:
             db.commit()
        except IntegrityError:
             db.rollback()
             return False
        return True
    finally:
        db.close()


def take_snapshots_for_all_clans():
    """Iterate over distinct clan tags from users and snapshot each."""
    db = SessionLocal()
    try:
        rows = (
            db.query(User.clan_tag, User.location_id, User.location)
            .filter(User.clan_tag.isnot(None), User.location_id.isnot(None))
            .distinct()
            .all()
        )
    finally:
        db.close()

    seen = set()
    created = 0
    for clan_tag, location_id, location_name in rows:
        key = (clan_tag, location_id)
        if key in seen:
            continue
        seen.add(key)
        try:
            if take_snapshot_for_clan(clan_tag, location_id, location_name):
                created += 1
        except Exception as exc:
            print(f"Snapshot failed for {clan_tag}: {exc}")
    return created


async def snapshot_loop():
    while True:
        try:
            created = take_snapshots_for_all_clans()
            if created:
                print(f"[snapshots] saved {created} new daily snapshot(s)")
        except Exception as exc:
            print(f"[snapshots] loop error: {exc}")
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
