from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_db_user
from app.models import User
from app.services.clash_royale import fetch_clan_by_tag

router = APIRouter()


@router.get("/members")
def get_members(user: User = Depends(get_current_db_user)):
    if not user.clan_tag:
        raise HTTPException(status_code=400, detail="Kein Clan-Tag gespeichert")

    clan_data = fetch_clan_by_tag(user.clan_tag)
    members = clan_data.get("memberList", [])

    return {
        "members": [
            {
                "tag": m.get("tag"),
                "name": m.get("name"),
                "trophies": m.get("trophies"),
                "role": m.get("role"),
                "clan_rank": m.get("clanRank"),
                "last_seen": m.get("lastSeen"),
            }
            for m in members
        ]
    }
