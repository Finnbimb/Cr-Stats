from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.schemas.profile import ClanTagRequest
from app.schemas.profile import PlayerTagRequest
from app.services.clash_royale import fetch_player_by_tag
from app.services.clash_royale import fetch_clan_by_tag, normalize_clan_tag
from app.services.clash_royale import check_player_tag

router = APIRouter()


@router.put("/profile/clan_tag")
def save_clan_tag(
    request: ClanTagRequest,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    tag = normalize_clan_tag(request.clan_tag)
    clan_data = fetch_clan_by_tag(tag)
    location = clan_data["location"]

    current_user.clan_tag = tag
    current_user.location_id = location["id"]
    current_user.location = location["name"]
    current_user.clan_ranking = None
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Clan tag updated successfully",
        "clan_tag": current_user.clan_tag,
        "location_id": current_user.location_id,
        "location": current_user.location,
    }


@router.post("/profile/check_player_tag")
def check_player_tag_exists(
    request: PlayerTagRequest,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    exists = check_player_tag(request.player_tag, request.token)
    return {"exists": exists}


@router.get("/profile")
def get_profile(user: User = Depends(get_current_db_user)):
    return {
        "username": user.username,
        "email": user.email,
        "clan_tag": user.clan_tag,
        "location_id": user.location_id,
        "location": user.location,
        "clan_ranking": user.clan_ranking,
    }
