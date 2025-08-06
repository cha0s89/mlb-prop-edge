# bvp_data.py (dynamic with pybaseball fallback)

"""
This module provides a helper for retrieving batter‑vs‑pitcher (BvP) matchup
statistics.  It attempts to query the Statcast endpoint via ``pybaseball`` to
obtain head‑to‑head data between a hitter and pitcher for the current
season.  If no data is found or the player–pitcher matchup has fewer than
``min_pa`` plate appearances, a fallback sample dataset is consulted.  The
fallback can be extended or customized as needed.

Note: ``pybaseball`` may not be installed in all environments.  If it is
unavailable or raises an error during import the fallback will always be
used.  Users can install ``pybaseball`` (e.g. via ``pip install
pybaseball``) to enable live Statcast queries.
"""

try:
    from pybaseball import statcast_batter_vs_pitcher
except Exception:
    # Provide a dummy function if pybaseball is unavailable
    statcast_batter_vs_pitcher = None

import os
from datetime import datetime

# Optional: disable pybaseball cache if needed
os.environ['PYBASEBALL_CACHE'] = 'False'

# Fallback sample data for players with no matchups found (customizable)
BVP_SAMPLE_DATA = {
    ("Freddie Freeman", "Yu Darvish"): {"pa": 18, "avg": 0.444, "hr": 2, "so": 3, "bb": 2},
    ("Mookie Betts", "Yu Darvish"): {"pa": 12, "avg": 0.250, "hr": 1, "so": 2, "bb": 1},
    ("Bryce Harper", "Kodai Senga"): {"pa": 10, "avg": 0.600, "hr": 3, "so": 1, "bb": 0},
    # Expand as needed
}


def get_bvp_stats(batter_name: str, pitcher_name: str, min_pa: int = 5) -> dict:
    """Returns current season BvP stats from Statcast or fallback if unavailable.

    Parameters
    ----------
    batter_name : str
        Full name of the hitter (e.g. "Freddie Freeman").
    pitcher_name : str
        Full name of the pitcher (e.g. "Yu Darvish").
    min_pa : int, optional
        Minimum number of plate appearances required to use the Statcast
        data; if fewer are found the fallback is used.  Default is 5.

    Returns
    -------
    dict
        Dictionary containing keys ``pa`` (plate appearances), ``avg``
        (batting average), ``hr`` (home runs), ``so`` (strikeouts) and
        ``bb`` (walks).  If no data is available all values will be zero.
    """
    # If pybaseball is not available, fall back immediately
    if statcast_batter_vs_pitcher is None:
        return BVP_SAMPLE_DATA.get((batter_name, pitcher_name), {"pa": 0, "avg": 0.0, "hr": 0, "so": 0, "bb": 0})
    try:
        current_year = datetime.today().year
        start_date = f"{current_year}-03-01"
        end_date = datetime.today().strftime('%Y-%m-%d')

        df = statcast_batter_vs_pitcher(batter_name, pitcher_name, start_dt=start_date, end_dt=end_date)
        if df is None or df.empty:
            raise ValueError("No data")

        pa = len(df)
        if pa < min_pa:
            raise ValueError("Insufficient PA")

        hits = df['events'].isin(['single', 'double', 'triple', 'home_run']).sum()
        hr = df['events'].eq('home_run').sum()
        so = df['events'].eq('strikeout').sum()
        bb = df['events'].eq('walk').sum()
        avg = hits / pa if pa > 0 else 0.0

        return {"pa": pa, "avg": round(avg, 3), "hr": int(hr), "so": int(so), "bb": int(bb)}

    except Exception:
        return BVP_SAMPLE_DATA.get((batter_name, pitcher_name), {"pa": 0, "avg": 0.0, "hr": 0, "so": 0, "bb": 0})
