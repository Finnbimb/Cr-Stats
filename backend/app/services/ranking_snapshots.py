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
    clans = fetch_full_ranking(location_id, ranking_path)
    return find_clan_by_tag(clans, clan_tag)

def fetch_full_ranking(location_id: int, ranking_path: str):
    try:
        data = cached_get(
            f"https://api.clashroyale.com/v1/locations/{location_id}/{ranking_path}?limit=1000",
            ttl=600,
            fallback_detail="Failed to load ranking",
        )
    except HTTPException:
        return []
    clans = data.get("items", [])
    return clans


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

        clan_score = trophy_entry["clanScore"] if trophy_entry else None
        clan_war_trophies = war_entry["clanWarTrophies"] if war_entry else None

        if clan_score is None or clan_war_trophies is None:
            try:
                clan = fetch_clan_by_tag(clan_tag)
                clan_score = clan_score or clan["clanScore"]
                clan_war_trophies = clan_war_trophies or clan["clanWarTrophies"]
            except Exception:
                pass

        snapshot = ClanRankingSnapshot(
            clan_tag=clan_tag,
            location_id=location_id,
            location_name=location_name,
            snapshot_date=date,
            trophy_rank=trophy_entry["rank"] if trophy_entry else None,
            war_rank=war_entry["rank"] if war_entry else None,
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
        user_clans = (
            db.query(User.clan_tag, User.location_id, User.location)
            .filter(User.clan_tag.isnot(None), User.location_id.isnot(None))
            .distinct()
            .all()
        )
    finally:
        db.close()

    created = 0

    # All Top 999 Clans in a location
    locations = {location_id for (_, location_id, _) in user_clans}
    for location_id in locations: 
        try: 
            # Top 999 in trophy and war rankings for this location
            created += take_snapshots_for_location(location_id)
        except Exception as exc:
            print(f"Snapshot failed for location {location_id}: {exc}")

    for clan_tag, location_id, location_name in user_clans:
        try:
            if take_snapshot_for_clan(clan_tag, location_id, location_name):
                created += 1
        except Exception as exc:
            print(f"Snapshot failed for {clan_tag}: {exc}")
    return created

def take_snapshots_for_location(location_id: int):
    trophy_items = fetch_full_ranking(location_id, "rankings/clans")
    war_items = fetch_full_ranking(location_id, "rankings/clanwars")

    trophy_by_tag = {eintrag["tag"]: eintrag for eintrag in trophy_items}
    war_by_tag = {eintrag["tag"]: eintrag for eintrag in war_items}

    all_tags = set(trophy_by_tag) | set(war_by_tag)

    db = SessionLocal()
    try: 
        date = today_str()

        location_name = None
        if trophy_items:
            location_name = trophy_items[0]["location"]["name"]
        elif war_items:
            location_name = war_items[0]["location"]["name"]

        created = 0
        rows = db.query(ClanRankingSnapshot.clan_tag).filter(ClanRankingSnapshot.snapshot_date == date).all()
        existing = {row[0] for row in rows}
        for tag in all_tags:
            if tag in existing: 
                continue
            trophy_entry = trophy_by_tag.get(tag)
            war_entry = war_by_tag.get(tag)
            
            snapshot = ClanRankingSnapshot(
                clan_tag=tag,
                location_id=location_id,
                location_name=location_name,
                snapshot_date=date,
                trophy_rank=trophy_entry["rank"] if trophy_entry else None,
                war_rank=war_entry["rank"] if war_entry else None,
                clan_score=trophy_entry["clanScore"] if trophy_entry else None,
                clan_war_trophies=war_entry["clanScore"] if war_entry else None,
                captured_at=int(time()),
            )
            db.add(snapshot)
            created += 1
        db.commit()
        return created
    finally:
        db.close()

async def snapshot_loop():
    while True:
        try:
            created = take_snapshots_for_all_clans()
            if created:
                print(f"[snapshots] saved {created} new daily snapshot(s)")
        except Exception as exc:
            print(f"[snapshots] loop error: {exc}")
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
