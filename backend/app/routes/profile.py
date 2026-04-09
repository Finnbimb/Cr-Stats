from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_db_user, get_db
from app.models import User
from app.schemas.profile import ClanTagRequest, LocationRequest
from app.services.clash_royale import fetch_location_name

router = APIRouter()


@router.put("/profile/clan_tag")
def save_clan_tag(
    request: ClanTagRequest,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    tag = request.clan_tag.strip().upper()
    if not tag:
        raise HTTPException(status_code=400, detail="Clan tag cannot be empty")
    if not tag.startswith("#"):
        tag = "#" + tag

    current_user.clan_tag = tag
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Clan tag updated successfully",
        "clan_tag": current_user.clan_tag
    }


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


@router.put("/profile/location")
def update_location(
    request: LocationRequest,
    user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    name = fetch_location_name(request.location_id)

    user.location_id = request.location_id
    user.location = name
    user.clan_ranking = None
    db.commit()
    db.refresh(user)

    return {
        "message": "Location updated successfully",
        "location_id": user.location_id,
        "location": user.location
    }

