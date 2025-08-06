# prop_edge.py

from pybaseball import playerid_lookup
from typing import Optional

def get_player_id(player_name: str, roster_mapping: dict) -> Optional[int]:
    """Return MLBAM player ID for a given name using roster or lookup fallback."""
    key = player_name.strip().lower()
    if key in roster_mapping:
        return roster_mapping[key]

    # Try lookup fallback using pybaseball
    try:
        name_parts = key.split()
        if len(name_parts) == 2:
            last, first = name_parts[1], name_parts[0]
            df = playerid_lookup(last, first)
            if not df.empty:
                return int(df["key_mlbam"].iloc[0])
    except Exception:
        pass
    return None


def build_roster_mapping() -> dict:
    """Builds player name to MLBAM ID mapping using all 30 team rosters."""
    from pybaseball import team_roster
    mapping = {}

    # Hardcoded MLB team IDs (30 total)
    team_ids = [
        108, 109, 110, 111, 112, 113, 114, 115, 116, 117,
        118, 119, 120, 121, 133, 134, 135, 136, 137, 138,
        139, 140, 141, 142, 143, 144, 145, 146, 147, 158
    ]

    for team_id in team_ids:
        try:
            df = team_roster(team_id)
            for _, row in df.iterrows():
                name = row.get("name_display_first_last", "").lower()
                pid = row.get("player_id")
                if name and pid:
                    mapping[name] = int(pid)
        except Exception:
            continue

    return mapping
