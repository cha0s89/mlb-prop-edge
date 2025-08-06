# evaluate_prop_v2.py

import random

# Load static multipliers or weights from other files (assumes you already imported them somewhere)
from bvp_data import bvp_lookup
from home_away_split import get_home_away_multiplier
from recent_trend import get_recent_trend_multiplier
from umpire_factors import get_umpire_multiplier
from stadium_factors import get_stadium_multiplier
from weather_factors import get_weather_multiplier


def evaluate_prop_v2(player_name, prop_type, line, side, is_home, ballpark, player_id):
    """
    Final prop evaluation function that combines all known factors into one prediction.
    Returns:
    - Probability (float 0–1)
    - Percent (0–100)
    - Confidence (string)
    - Recommendation (✅ / ❌)
    - Edge (probability - fair baseline of 0.5)
    """

    # 🔹 1. Start with base BvP data (0.5 if not found)
    bvp_prob = bvp_lookup(player_name, prop_type)
    if bvp_prob is None:
        bvp_prob = 0.50

    # 🔹 2. Apply home/away split
    home_away_mult = get_home_away_multiplier(player_name, is_home)

    # 🔹 3. Stadium multiplier
    stadium_mult = get_stadium_multiplier(ballpark, prop_type)

    # 🔹 4. Weather effect
    weather_mult = get_weather_multiplier(ballpark, prop_type)

    # 🔹 5. Umpire effect
    umpire_mult = get_umpire_multiplier(ballpark, prop_type)

    # 🔹 6. Recent trend adjustment
    trend_mult = get_recent_trend_multiplier(player_name, prop_type)

    # 🔹 7. Combine all
    final_prob = bvp_prob
    for mult in [home_away_mult, stadium_mult, weather_mult, umpire_mult, trend_mult]:
        final_prob *= mult

    # Clamp between 0.01 and 0.99 to avoid extremes
    final_prob = max(0.01, min(0.99, final_prob))

    # 🔹 8. Confidence and Recommendation
    if final_prob >= 0.75:
        confidence = "🔥 Very High"
        recommendation = "✅ Yes"
    elif final_prob >= 0.60:
        confidence = "✅ High"
        recommendation = "✅ Yes"
    elif final_prob >= 0.55:
        confidence = "🟡 Medium"
        recommendation = "⚠️ Cautious"
    else:
        confidence = "❌ Low"
        recommendation = "❌ No"

    edge = final_prob - 0.5

    return final_prob, final_prob * 100, confidence, recommendation, edge
