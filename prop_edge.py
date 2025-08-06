# prop_edge.py

from pybaseball import playerid_lookup

def get_player_id(player_name: str, roster_mapping: dict) -> int | None:
    """Return MLBAM player ID for a given name using roster or lookup fallback."""
    key = player_name.strip().lower()
    if key in roster_mapping:
        return roster_mapping[key]

    # Try lookup fallback
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
    """Return a mapping from lowercase player name to MLBAM ID using pybaseball team rosters."""
    from pybaseball import team_ids, team_roster
    mapping = {}

    for team_id in team_ids():
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
