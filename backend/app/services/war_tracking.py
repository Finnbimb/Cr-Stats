import asyncio

from time import time

from app.database import SessionLocal
from app.models import ClanSession, Members


from app.services.clash_royale import extract_riverrace_info, get_current_riverrace

last_section_index = None


def check_section_index(riverrace_info: dict):
    global last_section_index

    if not riverrace_info:
        return {
            "status": "missing_data",
            "section_changed": False,
            "previous_section_index": last_section_index,
            "current_section_index": None,
        }

    current_section_index = riverrace_info.get("section_index")

    if current_section_index is None:
        return {
            "status": "missing_section_index",
            "section_changed": False,
            "previous_section_index": last_section_index,
            "current_section_index": None,
        }

    if last_section_index is None:
        last_section_index = current_section_index
        return {
            "status": "initialized",
            "section_changed": False,
            "previous_section_index": None,
            "current_section_index": current_section_index,
        }

    if current_section_index != last_section_index:
        previous_section_index = last_section_index
        last_section_index = current_section_index
        return {
            "status": "section_changed",
            "section_changed": True,
            "previous_section_index": previous_section_index,
            "current_section_index": current_section_index,
        }

    return {
        "status": "same_section",
        "section_changed": False,
        "previous_section_index": last_section_index,
        "current_section_index": current_section_index,
    }


def sync_war_data_once(clan_data: dict | None = None):
    if clan_data is None:
        clan_data = get_current_riverrace()

    riverrace_info = extract_riverrace_info(clan_data)

    section_check = check_section_index(riverrace_info)

    if riverrace_info:
        update_database(riverrace_info)

    return section_check

async def poll_war_data_loop():
    while True:
        print("running")
        try:
            sync_war_data_once()
        except Exception as exc:
            print("Polling failed:", exc)

        await asyncio.sleep(60)
        
def update_database(riverrace_info: dict):
    if not riverrace_info:
        return

    db = SessionLocal()
    try:
        clan_tag = riverrace_info.get("clan_tag") or "#8R8U0VQG"
        timestamp = int(time())

        db.query(ClanSession).filter(ClanSession.clan_tag == clan_tag).delete()
        db.query(Members).filter(Members.clan_tag == clan_tag).delete()
        
        clan_session = ClanSession(
            clan_tag=clan_tag,
            section_index=riverrace_info.get("section_index"),
            period_type=riverrace_info.get("period_type"),
            updated_at=timestamp,
        )
        db.add(clan_session)
        
        member_rows = [
            Members(
                clan_tag=clan_tag,
                member_tag=member["tag"],
                name=member["name"],
                games_played=member["games_played"],
                games_played_today=member["games_played_today"],
                boat_attacks=member["boat_attacks"],
                updated_at=timestamp,
            )
            for member in riverrace_info.get("members", [])
        ]

        db.add_all(member_rows)
        db.commit()
        
    finally:
        db.close()
