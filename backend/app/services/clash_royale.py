import time
from threading import Lock

import requests
from datetime import datetime, timezone
from fastapi import HTTPException

from app.core.config import get_cr_api_token
from app.models import User

from urllib.parse import quote

OUR_CLAN_TAG = "#8R8U0VQG"
GERMANY_LOCATION_NAME = "Germany"


# Process-wide TTL cache for CR-API GET responses, keyed by URL. Lives for the
# lifetime of the uvicorn process (or bot process); flushed on restart.
# Mehrere User aus dem gleichen Clan teilen sich denselben Eintrag, was die
# CR-API-Last drastisch reduziert.
_api_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = Lock()


def get_cr_api_headers():
    cr_api_token = get_cr_api_token()

    if not cr_api_token:
        raise HTTPException(status_code=500, detail="CR_API_TOKEN is not configured")

    return {
        "Authorization": f"Bearer {cr_api_token}"
    }


def cached_get(url: str, ttl: int, fallback_detail: str) -> dict:
    """GET against the CR API with a shared in-memory TTL cache."""
    now = time.monotonic()

    with _cache_lock:
        entry = _api_cache.get(url)
        if entry and entry[0] > now:
            return entry[1]

    # Cache-Miss: HTTP-Call bewusst OHNE Lock — sonst blockiert ein langsamer
    # CR-Call alle anderen Reader für die Dauer der Anfrage.
    try:
        response = requests.get(url, headers=get_cr_api_headers(), timeout=10)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=fallback_detail) from exc

    raise_for_clash_api_error(response, fallback_detail)
    data = response.json()

    with _cache_lock:
        _api_cache[url] = (now + ttl, data)
    return data


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
    clan_data = cached_get(
        f"https://api.clashroyale.com/v1/clans/{encoded_tag}",
        ttl=300,
        fallback_detail="Failed to load clan from Clash Royale API",
    )
    location = clan_data.get("location") or {}
    if not location.get("id") or not location.get("name"):
        raise HTTPException(status_code=400, detail="Clan has no valid location")

    return clan_data

# ONLY USED FOR FRONTEND, BOT HAS ITS OWN FUNCTION
def fetch_user_clan_ranking(user: User):
    data = cached_get(
        f"https://api.clashroyale.com/v1/locations/{user.location_id}/rankings/clans",
        ttl=600,
        fallback_detail="Failed to load clan ranking from Clash Royale API",
    )
    clans = data.get("items", [])
    return find_clan_by_tag(clans, user.clan_tag)


def fetch_user_clanwar_ranking(user: User):
    data = cached_get(
        f"https://api.clashroyale.com/v1/locations/{user.location_id}/rankings/clanwars",
        ttl=600,
        fallback_detail="Failed to load clan war ranking from Clash Royale API",
    )
    clans = data.get("items", [])
    return find_clan_by_tag(clans, user.clan_tag)


def fetch_current_riverrace_for_tag(clan_tag: str) -> dict:
    clan_tag = normalize_clan_tag(clan_tag)
    encoded_tag = quote(clan_tag)
    data = cached_get(
        f"https://api.clashroyale.com/v1/clans/{encoded_tag}/currentriverrace",
        ttl=60,
        fallback_detail="Failed to load current river race",
    )
    periodLogs = data.get("periodLogs", [])
    clan = data.get("clan") or {}
    clans = data.get("clans", [])

    participants = clan.get("participants", [])
    if not participants and clans:
        own = find_clan_by_tag(clans, clan_tag)
        if own:
            participants = own.get("participants", [])

    war_rank = None
    race_clans = []
    if clans:
        # clan.fame ist außerhalb der Finalwoche oft Müll → echtes Total = Summe Spieler-Fame.
        def _total_fame(c):
            return sum((p or {}).get("fame", 0) for p in (c.get("participants") or []))
        sorted_clans = sorted(clans, key=_total_fame, reverse=True)
        sortiert = []
        for i, c in enumerate(sorted_clans):
            tag = c.get("tag")
            past_total = 0
            for day in periodLogs:
                for entry in day.get("items", []):
                    if entry["clan"]["tag"] == tag:
                        past_total += entry.get("pointsEarned", 0)
            
            is_own = bool(tag and normalize_clan_tag(tag) == clan_tag)
            race_clans.append({
                "tag": tag,
                "name": c.get("name"),
                "fame": _total_fame(c),
                "today" : _total_fame(c) - past_total,
                "is_own": is_own,
            })
            if is_own:
                war_rank = i + 1
                
        sortiert = sorted(race_clans, key=lambda punkte: punkte["today"], reverse=True)
        for i, e in enumerate(sortiert):
            e["rank"] = i + 1

        # einmaliger Debug, um die echten Werte zu sehen
        print(f"[debug today] periodLogs_count={len(periodLogs)}", flush=True)
        for e in sortiert:
            print(f"[debug today]   rank={e['rank']} name={e['name']:<22} fame={e['fame']} today={e['today']}", flush=True)

    return {
        "period_type": data.get("periodType"),
        "section_index": data.get("sectionIndex", 0),
        "clan_count": len(clans),
        "participants": participants,
        "war_rank": war_rank,
        "race_clans": sortiert,
        
    }


def fetch_riverracelog(clan_tag: str) -> list[dict]:
    """Raw riverracelog items for a clan — cached, used by multiple consumers."""
    clan_tag = normalize_clan_tag(clan_tag)
    encoded_tag = quote(clan_tag)
    data = cached_get(
        f"https://api.clashroyale.com/v1/clans/{encoded_tag}/riverracelog",
        ttl=1800,
        fallback_detail="Failed to load river race log",
    )
    return data.get("items", [])


def fetch_riverracelog_participants(clan_tag: str) -> list[dict]:
    items = fetch_riverracelog(clan_tag)
    if not items:
        return []
    clan_tag_normalized = normalize_clan_tag(clan_tag)
    standings = items[0].get("standings", [])
    own = next(
        (s for s in standings if normalize_clan_tag(s.get("clan", {}).get("tag", "")) == clan_tag_normalized),
        None,
    )
    if not own:
        return []
    return own.get("clan", {}).get("participants", [])


def fetch_ranked_clan_for_location(*, ranking_path: str, fallback_detail: str, clan_tag: str = OUR_CLAN_TAG):
    locations = fetch_locations()
    germany = next((loc for loc in locations if loc["name"] == GERMANY_LOCATION_NAME), None)
    if not germany:
        return None

    data = cached_get(
        f"https://api.clashroyale.com/v1/locations/{germany['id']}/{ranking_path}",
        ttl=600,
        fallback_detail=fallback_detail,
    )
    clans = data.get("items", [])
    return find_clan_by_tag(clans, clan_tag)


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
    data = cached_get(
        "https://api.clashroyale.com/v1/locations",
        ttl=86400,
        fallback_detail="Failed to load locations from Clash Royale API",
    )
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

    player_data = cached_get(
        f"https://api.clashroyale.com/v1/players/{encoded_tag}",
        ttl=300,
        fallback_detail="Failed to load player from Clash Royale API",
    )
    clan_data = player_data.get("clan") or {}

    return {
        "tag": player_data.get("tag"),
        "name": player_data.get("name"),
        "clan_tag": clan_data.get("tag"),
        "clan_name": clan_data.get("name"),
    }

def fetch_clan_members(clan_tag: str) -> list[dict]:
    clan_tag = normalize_clan_tag(clan_tag)
    encoded_tag = quote(clan_tag)

    data = cached_get(
        f"https://api.clashroyale.com/v1/clans/{encoded_tag}/members",
        ttl=120,
        fallback_detail="Failed to load clan members from Clash Royale API",
    )
    return data.get("items", [])


def fetch_current_clan_members():
    return fetch_clan_members(OUR_CLAN_TAG)

def get_current_riverrace():
    encoded_tag = quote(OUR_CLAN_TAG)
    response_data = cached_get(
        f"https://api.clashroyale.com/v1/clans/{encoded_tag}/currentriverrace",
        ttl=60,
        fallback_detail="Failed to load current river race from Clash Royale API",
    )
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
    items = fetch_riverracelog(OUR_CLAN_TAG)
    if not items:
        return None

    creation_date_str = items[0].get("creationTime") or items[0].get("creationDate")
    if not creation_date_str:
        return None

    return parse_cr_timestamp(creation_date_str)




def find_clan_by_tag(clans: list[dict], clan_tag: str):
    if not clans:
        return None

    normalized_tag = normalize_clan_tag(clan_tag)
    return next(
        (
            clan for clan in clans
            if clan.get("tag") and normalize_clan_tag(clan.get("tag")) == normalized_tag
        ),
        None,
    )
