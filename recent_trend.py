# recent_trend.py

from pybaseball import batting_stats_range, statcast_batter, statcast_pitcher
from datetime import datetime, timedelta
import pandas as pd


def get_recent_trend_multiplier(player_name: str, long_days: int = 15, short_days: int = 5) -> float:
    """
    Compares recent short-term (e.g. 5-day) batting average to longer-term (e.g. 15-day) average.
    Returns a multiplier to adjust projections based on 'heating up' or 'cooling down'.
    """
    try:
        today = datetime.today()
        long_start = today - timedelta(days=long_days)
        short_start = today - timedelta(days=short_days)

        long_df = batting_stats_range(long_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        short_df = batting_stats_range(short_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

        long_row = long_df[long_df['Name'].str.lower() == player_name.lower()]
        short_row = short_df[short_df['Name'].str.lower() == player_name.lower()]

        if long_row.empty or short_row.empty:
            return 1.0

        long_avg = long_row['AVG'].values[0]
        short_avg = short_row['AVG'].values[0]

        if pd.isna(long_avg) or pd.isna(short_avg) or long_avg == 0:
            return 1.0

        ratio = short_avg / long_avg
        return round(ratio, 2)

    except Exception:
        return 1.0


def get_recent_streak_form(player_id, player_type="batter"):
    """
    Adds streak/momentum info for a player over last 5–10 days.
    """
    try:
        end_date = datetime.today()
        start_5 = end_date - timedelta(days=5)
        start_10 = end_date - timedelta(days=10)
        end_str = end_date.strftime("%Y-%m-%d")
        start_5_str = start_5.strftime("%Y-%m-%d")
        start_10_str = start_10.strftime("%Y-%m-%d")

        if player_type == "batter":
            df5 = statcast_batter(start_5_str, end_str, player_id)
            df10 = statcast_batter(start_10_str, end_str, player_id)
            hits = df5["events"].isin(["single", "double", "triple", "home_run"]).sum()
            hr = (df5["events"] == "home_run").sum()
            rbi = df5["rbi"].fillna(0).sum()
            streak_len = len(df10[df10["events"].isin(["single", "double", "triple", "home_run"])])
            return {
                "last_5_hits": hits,
                "last_5_hr": hr,
                "last_5_rbi": int(rbi),
                "10g_streak_hits": streak_len
            }

        elif player_type == "pitcher":
            df5 = statcast_pitcher(start_5_str, end_str, player_id)
            df10 = statcast_pitcher(start_10_str, end_str, player_id)
            strikeouts = df5["description"].str.contains("strikeout", na=False).sum()
            innings = df5["inning"].nunique() / 2.0
            return {
                "last_5_k": int(strikeouts),
                "last_5_ip": round(innings, 1),
                "10g_total_k": df10["description"].str.contains("strikeout", na=False).sum()
            }

    except Exception:
        return {}
