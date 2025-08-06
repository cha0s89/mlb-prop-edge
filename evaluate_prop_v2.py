
# evaluate_prop_v2.py

from typing import Tuple, Optional, Dict, Any
from datetime import datetime
from bvp_data import get_bvp_stats
from home_away_split import get_home_away_multiplier
from recent_trend import get_recent_trend_multiplier
from stadium_factors import get_stadium_factor
from ballpark_factors import get_park_multiplier
from umpire_data import get_umpire_adjustment
from umpire_factors import get_umpire_factors
from weather_factors import get_weather_multiplier

from pybaseball import batting_stats, pitching_stats

def get_base_stats(player_name: str, prop_type: str, player_type: str = "batter") -> float:
    try:
        df = batting_stats(datetime.now().year) if player_type == "batter" else pitching_stats(datetime.now().year)
        row = df[df["Name"].str.lower() == player_name.lower()]
        if row.empty:
            return 0.0

        if player_type == "batter":
            if prop_type in {"hits", "total_bases", "hrr"}:
                return float(row["AVG"].values[0])
            elif prop_type == "walks":
                return float(row["BB%"].str.rstrip("%").astype(float).values[0]) / 100.0
            elif prop_type == "batter_strikeouts":
                return float(row["K%"].str.rstrip("%").astype(float).values[0]) / 100.0
        elif player_type == "pitcher":
            if prop_type == "strikeouts":
                return float(row["K/9"].values[0]) / 27.0
            elif prop_type == "earned_runs":
                return float(row["ERA"].values[0]) / 9.0
            elif prop_type == "outs":
                return float(row["IP"].values[0]) / row["G"].values[0] * 3

    except Exception:
        return 0.0
    return 0.0


def evaluate_prop_v2(
    player_name: str,
    prop_type: str,
    line: float,
    side: str,
    pitcher_name: Optional[str] = None,
    is_home: Optional[bool] = None,
    ballpark: Optional[str] = None,
    umpire: Optional[str] = None,
    player_id: Optional[int] = None
) -> Tuple[float, Dict[str, Any], float]:
    """
    Main engine to evaluate a player prop by combining base stats,
    BvP data, situational multipliers, and trends.
    """
    details: Dict[str, Any] = {}
    player_type = "pitcher" if prop_type in {"strikeouts", "earned_runs", "outs"} else "batter"

    base_rate = get_base_stats(player_name, prop_type, player_type=player_type)
    details["base_rate"] = round(base_rate, 3)

    if pitcher_name and player_type == "batter":
        bvp = get_bvp_stats(player_name, pitcher_name)
        if bvp["pa"] >= 5:
            bvp_avg = bvp["avg"]
            details["bvp_avg"] = round(bvp_avg, 3)
            base_rate = 0.7 * base_rate + 0.3 * bvp_avg

    try:
        trend_mult = get_recent_trend_multiplier(player_name)
        base_rate *= trend_mult
        details["trend_multiplier"] = round(trend_mult, 2)
    except Exception:
        pass

    if is_home is not None:
        try:
            home_mult = get_home_away_multiplier(player_name, is_home)
            base_rate *= home_mult
            details["home_away_multiplier"] = round(home_mult, 3)
        except Exception:
            pass

    if ballpark:
        stadium_mult = get_stadium_factor(ballpark)
        base_rate *= stadium_mult
        details["stadium_multiplier"] = round(stadium_mult, 2)

        park_prop_mult = get_park_multiplier(ballpark, prop_type)
        base_rate *= park_prop_mult
        details["ballpark_multiplier"] = round(park_prop_mult, 2)

    if umpire:
        if prop_type in {"strikeouts", "batter_strikeouts"}:
            ump_k_mult = get_umpire_adjustment(umpire, "strikeout")
            base_rate *= ump_k_mult
            details["umpire_k_factor"] = round(ump_k_mult, 2)
        if prop_type == "walks":
            ump_bb_mult = get_umpire_adjustment(umpire, "walk")
            base_rate *= ump_bb_mult
            details["umpire_bb_suppress"] = round(ump_bb_mult, 2)
        ump_factors = get_umpire_factors(umpire)
        details["umpire_over_tendency"] = ump_factors.get("over_tendency", 0.5)

    if ballpark:
        try:
            weather_mult = get_weather_multiplier(ballpark)
            base_rate *= weather_mult
            details["weather_multiplier"] = round(weather_mult, 2)
        except Exception:
            pass

    prob = base_rate if side == "over" else 1.0 - base_rate
    prob = max(0.01, min(0.99, prob))
    confidence = 0.5 + 0.5 * (1 - abs(prob - 0.5))

    return prob, details, round(confidence, 2)
