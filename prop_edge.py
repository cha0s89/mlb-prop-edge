# prop_edge.py

import requests

def get_player_id(player_name, roster_mapping):
    """Return MLBAM player ID for a given name using roster or fallback."""
    key = player_name.strip().lower()
    if key in roster_mapping:
        return roster_mapping[key]

    try:
        # Fallback: basic name match via MLB API (slower, less reliable)
        url = "https://statsapi.mlb.com/api/v1/people/search"
        response = requests.get(url, params={"names": player_name})
        data = response.json()
        people = data.get("people", [])
        if people:
            return people[0].get("id")
    except Exception:
        pass

    return None


def build_roster_mapping():
    """Fetch player name to MLBAM ID mapping using MLB API (no pybaseball)."""
    mapping = {}
    try:
        teams_resp = requests.get("https://statsapi.mlb.com/api/v1/teams", params={"sportId": 1}, timeout=10)
        teams = teams_resp.json().get("teams", [])
    except Exception:
        teams = []

    for team in teams:
        team_id = team.get("id")
        try:
            roster_resp = requests.get(
                f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster",
                params={"rosterType": "active"},
                timeout=10,
            )
            for player in roster_resp.json().get("roster", []):
                pid = player.get("person", {}).get("id")
                name = player.get("person", {}).get("fullName", "").lower()
                if pid and name:
                    mapping[name] = pid
        except Exception:
            continue

    return mapping
