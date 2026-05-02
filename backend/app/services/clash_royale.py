import requests
from datetime import datetime, timezone
from fastapi import HTTPException

from app.core.config import get_cr_api_token
from app.models import User

from urllib.parse import quote

OUR_CLAN_TAG = "#8R8U0VQG"
GERMANY_LOCATION_NAME = "Germany"



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


def normalize_player_tag(player_tag: str):
    tag = player_tag.strip().upper()
    if not tag:
        raise HTTPException(status_code=400, detail="Player tag cannot be empty")

    if not tag.startswith("#"):
        tag = f"#{tag}"

    return tag

# used for clan-tag input, to save every tag equally
def normalize_clan_tag(clan_tag: str):
    tag = clan_tag.strip().upper()
    if not tag:
        raise HTTPException(status_code=400, detail="Clan tag cannot be empty")

    if not tag.startswith("#"):
        tag = f"#{tag}"

    return tag


def fetch_clan_by_tag(clan_tag: str):
    clan_tag = normalize_clan_tag(clan_tag)
    encoded_tag = quote(clan_tag)

    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/clans/{encoded_tag}",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load clan from Clash Royale API",
        ) from exc

    raise_for_clash_api_error(response, "Failed to load clan from Clash Royale API")

    clan_data = response.json()
    location = clan_data.get("location") or {}
    if not location.get("id") or not location.get("name"):
        raise HTTPException(status_code=400, detail="Clan has no valid location")

    return clan_data

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

def fetch_ranked_clan_for_location(*, ranking_path: str, fallback_detail: str, clan_tag: str = OUR_CLAN_TAG):
    locations = fetch_locations()
    germany = next((loc for loc in locations if loc["name"] == GERMANY_LOCATION_NAME), None)
    if not germany:
        return None

    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/locations/{germany['id']}/{ranking_path}",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=fallback_detail,
        ) from exc

    raise_for_clash_api_error(response, fallback_detail)

    clans = response.json().get("items", [])
    return next((clan for clan in clans if clan.get("tag") == clan_tag), None)


# USED BY BOT TO FETCH RANKING IN GERMANY LOCATION
def fetch_clan_ranking_germany():
    return fetch_ranked_clan_for_location(
        ranking_path="rankings/clans",
        fallback_detail="Failed to load clan ranking from Clash Royale API",
    )


def fetch_clanwar_ranking_germany():
    return fetch_ranked_clan_for_location(
        ranking_path="rankings/clanwars",
        fallback_detail="Failed to load clan war ranking from Clash Royale API",
    )

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
    
def fetch_player_by_tag(player_tag: str):
    player_tag = normalize_player_tag(player_tag)
    encoded_tag = quote(player_tag)
    
    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/players/{encoded_tag}",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load player from Clash Royale API",
        ) from exc
        
    raise_for_clash_api_error(response, "Failed to load player from Clash Royale API")
    player_data = response.json()
    clan_data = player_data.get("clan") or {}

    return {
        "tag": player_data.get("tag"),
        "name": player_data.get("name"),
        "clan_tag": clan_data.get("tag"),
        "clan_name": clan_data.get("name"),
    }
    
def fetch_current_clan_members():
    encoded_tag = quote(OUR_CLAN_TAG)
    
    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/clans/{encoded_tag}/members",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load clan members from Clash Royale API",
        ) from exc

    raise_for_clash_api_error(response, "Failed to load clan members from Clash Royale API")

    return response.json().get("items", [])

def get_current_riverrace():
    try:
        # "#" in clan tags must be URL-encoded as "%23"
        encoded_tag = quote(OUR_CLAN_TAG)
        
        response = requests.get(
            f"https://api.clashroyale.com/v1/clans/{encoded_tag}/currentriverrace",
            headers=get_cr_api_headers(),
            timeout=10,
        )
        raise_for_clash_api_error(response, "Failed to load current river race from Clash Royale API")
        response_data = response.json()
        own_clan = find_clan_by_tag(response_data.get("clans", []), OUR_CLAN_TAG)

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
    
    clan_members = fetch_current_clan_members()

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
            for member in participants if member.get("tag") in {m.get("tag") for m in clan_members}
        ],
    }
    
def parse_cr_timestamp(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def fetch_war_creation_date() -> int | None:
    """Returns Unix timestamp of when the current war week started."""
    encoded_tag = quote(OUR_CLAN_TAG)
    try:
        response = requests.get(
            f"https://api.clashroyale.com/v1/clans/{encoded_tag}/riverracelog",
            headers=get_cr_api_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to load river race log from Clash Royale API",
        ) from exc

    raise_for_clash_api_error(response, "Failed to load river race log from Clash Royale API")
    items = response.json().get("items", [])
    if not items:
        return None

    creation_date_str = items[0].get("creationTime") or items[0].get("creationDate")
    if not creation_date_str:
        return None

    return parse_cr_timestamp(creation_date_str)





def find_clan_by_tag(clans: list[dict], clan_tag: str):
    if not clans:
        return None

    return next((clan for clan in clans if clan.get("tag") == clan_tag), None)
