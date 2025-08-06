# game_schedule.py

import requests
from datetime import datetime
import pytz


def get_today_game_schedule():
    """
    Fetches today's MLB game schedule from a public MLB API endpoint.
    Returns a dictionary of matchups with stadium names and UTC start times.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
        response = requests.get(url)
        data = response.json()

        games = {}
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                home_team = game["teams"]["home"]["team"]["name"]
                away_team = game["teams"]["away"]["team"]["name"]
                game_time_utc = game["gameDate"]  # already in UTC
                venue = game["venue"]["name"]
                matchup = f"{away_team} @ {home_team}"
                games[matchup] = {"stadium": venue, "game_time_utc": game_time_utc}

        return games

    except Exception as e:
        return {}
