"""
home_away_split.py

This module provides a simple helper function to compute a performance
multiplier based on whether a hitter is playing at home or on the road.

The approach here uses the ``pybaseball`` library to fetch batting
statistics broken down by home and away splits for the current season.
If ``pybaseball`` is not installed or fails, the multiplier defaults
to 1.0.  Users who wish to leverage home/away splits should add
``pybaseball`` to their requirements and ensure internet access.

Example
-------

>>> from home_away_split import get_home_away_multiplier
>>> get_home_away_multiplier("Freddie Freeman", is_home=True)
1.05  # meaning he hits about 5% better at home than on the road

If no data is available the function returns 1.0.
"""

from __future__ import annotations

from typing import Dict

try:
    from pybaseball import batting_stats
except Exception:
    batting_stats = None  # type: ignore

def get_home_away_multiplier(player_name: str, is_home: bool, season: int | None = None) -> float:
    """Return a performance multiplier based on a player's home/away split.

    If the ``pybaseball`` package is available, this function queries
    season‑long batting statistics and compares the player's batting
    average at home to their average on the road.  The ratio of these
    averages is returned as the multiplier when ``is_home`` is True;
    otherwise the reciprocal is returned.  A minimum of 30 at‑bats is
    required on both home and away samples to compute a meaningful ratio.

    Parameters
    ----------
    player_name : str
        Name of the hitter (e.g. ``"Mookie Betts"``).
    is_home : bool
        True if the player is playing at home; False if on the road.
    season : int, optional
        Season year to query (defaults to the current year).

    Returns
    -------
    float
        A multiplier representing how much better (or worse) the
        player hits at home relative to away.  A value of 1.05 means
        the player performs about 5% better at home; a value of 0.95
        means they perform about 5% worse.  If data is unavailable
        the function returns 1.0.
    """
    if batting_stats is None:
        # Without pybaseball we cannot compute splits
        return 1.0
    try:
        from datetime import datetime
        current_year = season or datetime.today().year
        # Fetch batting stats for all players and include split columns
        df = batting_stats(current_year, qual=1)
        row = df[df['Name'].str.lower() == player_name.lower()]
        if row.empty:
            return 1.0
        # pybaseball's batting_stats includes separate columns for home and
        # away at‑bats and hits: AB_home, H_home, AB_away, H_away
        h_ab = row.iloc[0].get('AB_home')
        h_hits = row.iloc[0].get('H_home')
        a_ab = row.iloc[0].get('AB_away')
        a_hits = row.iloc[0].get('H_away')
        if not (h_ab and h_hits and a_ab and a_hits) or h_ab < 30 or a_ab < 30:
            return 1.0
        home_avg = h_hits / h_ab
        away_avg = a_hits / a_ab
        # Avoid division by zero
        if home_avg == 0 or away_avg == 0:
            return 1.0
        ratio = home_avg / away_avg
        return ratio if is_home else (1 / ratio)
    except Exception:
        return 1.0
