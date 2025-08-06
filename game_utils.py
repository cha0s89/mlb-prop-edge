# game_utils.py

import requests
from datetime import datetime
from typing import List, Dict, Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo

def build_player_team_mapping():
    """Builds mapping from player ID to team info using MLB API"""
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
                if pid:
                    mapping[pid] = {
                        "team_id": team_id,
                        "team_name": team.get("name")
                    }
        except Exception:
            continue
    return mapping


def get_today_schedule():
    try:
        today_date = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    except Exception:
        today_date = datetime.utcnow().date()
    try:
        resp = requests.get("https://statsapi.mlb.com/api/v1/schedule", params={"sportId": 1, "date": today_date.isoformat()}, timeout=10)
        data = resp.json()
    except Exception:
        data = {}
    games = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            games.append({
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "away_team_id": game["teams"]["away"]["team"]["id"],
                "ballpark": game["venue"]["name"],
            })
    return games


def get_game_info_for_player(player_name, roster_mapping, team_mapping, schedule):
    from prop_edge import get_player_id
    info = {"home_away": "N/A", "ballpark": "N/A"}
    pid = roster_mapping.get(player_name.lower()) or get_player_id(player_name, roster_mapping)
    if
