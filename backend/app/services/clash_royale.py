import requests
from fastapi import HTTPException

from app.core.config import get_cr_api_token
from app.models import User

from urllib.parse import quote


def get_cr_api_headers():
    cr_api_token = get_cr_api_token()

    if not cr_api_token:
        raise HTTPException(status_code=500, detail="CR_API_TOKEN is not configured")

    return {
        "Authorization": f"Bearer {cr_api_token}"
    }


def raise_for_clash_api_error(response: requests.Response, fallback_detail: str):
    if response.ok:
        return

    detail = fallback_detail

    try:
        error_data = response.json()
    except ValueError:
        error_data = None

    if response.status_code in {401, 403}:
        api_message = None
        if isinstance(error_data, dict):
            api_message = error_data.get("message") or error_data.get("reason")

        detail = (
            "Clash Royale API authorization failed. "
            "Check CR_API_TOKEN and the allowed public IP in the Clash Royale developer portal."
        )
        if api_message:
            detail = f"{detail} API message: {api_message}"

        raise HTTPException(status_code=502, detail=detail)

    if response.status_code == 404:
        if isinstance(error_data, dict):
            api_message = error_data.get("message") or error_data.get("reason")
            if api_message:
                detail = f"{fallback_detail} API message: {api_message}"

        raise HTTPException(status_code=404, detail=detail)

    if isinstance(error_data, dict):
        api_message = error_data.get("message") or error_data.get("reason")
        if api_message:
            detail = f"{fallback_detail} API message: {api_message}"

    raise HTTPException(status_code=502, detail=detail)


def fetch_location_name(location_id: int):
    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/locations/{location_id}",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load location from Clash Royale API",
        ) from exc

    raise_for_clash_api_error(response, "Failed to load location from Clash Royale API")

    name = response.json().get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Invalid location ID")

    return name

# ONLY USED FOR FRONTEND, BOT HAS ITS OWN FUNCTION 
def fetch_user_clan_ranking(user: User):
    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/locations/{user.location_id}/rankings/clans",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load clan ranking from Clash Royale API",
        ) from exc

    raise_for_clash_api_error(response, "Failed to load clan ranking from Clash Royale API")

    clans = response.json().get("items", [])
    return next((clan for clan in clans if clan.get("tag") == user.clan_tag), None)

# USED BY BOT TO FETCH RANKING IN GERMANY LOCATION
def fetch_clan_ranking_germany():
    clan_tag = "#8R8U0VQG" 
    
    # should be "57000094" for Germany, but we fetch all locations to be sure and to have the name for error messages
    locations = fetch_locations()
    germany = next((loc for loc in locations if loc["name"] == "Germany"), None)
    if not germany:
        return None
    
    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/locations/{germany['id']}/rankings/clans",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Clan is not ranked in Germany or error fetching clan ranking!",
        ) from exc
        
    raise_for_clash_api_error(response, "Failed to load clan ranking from Clash Royale API")

    clans = response.json().get("items", [])
    return next((clan for clan in clans if clan.get("tag") == clan_tag), None)

def fetch_locations():
    try:
        locations = requests.get(
            "https://api.clashroyale.com/v1/locations",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load locations from Clash Royale API",
        ) from exc

    raise_for_clash_api_error(locations, "Failed to load locations from Clash Royale API")

    data = locations.json()
    return [
        {
            "id": item["id"],
            "name": item["name"]
        }
        for item in data.get("items", [])
        if "id" in item and "name" in item
    ]

def get_current_riverrace():
    try:
        # "#" in clan tags must be URL-encoded as "%23"
        clan_tag = "#8R8U0VQG"
        encoded_tag = "%238R8U0VQG"
        
        response = requests.get(
            f"https://api.clashroyale.com/v1/clans/{encoded_tag}/currentriverrace",
            headers=get_cr_api_headers(),
            timeout=10,
        )
        raise_for_clash_api_error(response, "Failed to load current river race from Clash Royale API")
        response_data = response.json()
        own_clan = find_clan_by_tag(response_data.get("clans", []), clan_tag)

        if own_clan is None:
            own_clan = response_data.get("clan")

        if own_clan is None:
            return None

        # everything of our clan  + sectionIndex(day), periodtype(training, war), state
        return {
            **own_clan,
            "sectionIndex": response_data.get("sectionIndex"),
            "periodType": response_data.get("periodType"),
            "state": response_data.get("state"),
        }
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502, 
            detail="Failed to load current river race from Clash Royale API",
        ) from exc
        
        
def extract_riverrace_info(clan_data: dict):
    if not clan_data:
        return None

    participants = clan_data.get("participants", [])

    return {
        "clan_tag": clan_data.get("tag"),
        "clan_name": clan_data.get("name"),
        "section_index": clan_data.get("sectionIndex"),
        "period_type": clan_data.get("periodType"),
        "state": clan_data.get("state"),
        "members": [
            {
                "tag": member.get("tag"),
                "name": member.get("name"),
                "games_played": member.get("decksUsed", 0),
                "games_played_today": member.get("decksUsedToday", 0),
                "boat_attacks": member.get("boatAttacks", 0),
            }
            for member in participants
        ],
    }
        
def find_clan_by_tag(clans: list[dict], clan_tag: str):
    if not clans:
        return None

    return next((clan for clan in clans if clan.get("tag") == clan_tag), None)
