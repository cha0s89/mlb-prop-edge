# streamlit_app.py

import streamlit as st
import pandas as pd
from prop_edge import get_player_id, build_roster_mapping
from game_utils import (
    build_player_team_mapping,
    get_today_schedule,
    get_game_info_for_player
)
from evaluate_prop_v2 import evaluate_prop_v2


# --- Load Data Once ---
@st.cache_data
def load_data():
    roster_mapping = build_roster_mapping()
    team_mapping = build_player_team_mapping()
    schedule_today = get_today_schedule()
    return roster_mapping, team_mapping, schedule_today


roster_mapping, team_mapping, schedule_today = load_data()

st.set_page_config(page_title="MLB Prop Evaluator", layout="wide")
st.title("⚾ MLB Prop Bet Evaluator")
st.markdown("Upload a RotoWire CSV to get model-based predictions for today's props.")

# --- CSV Upload + Evaluation ---
csv_file = st.file_uploader("📤 Upload RotoWire CSV", type=["csv"])

if csv_file:
    st.subheader("📥 Uploaded CSV Evaluation")
    df = pd.read_csv(csv_file)

    results = []

    for _, row in df.iterrows():
        name = str(row.get("Player", "")).strip()
        prop_type = str(row.get("Market Name", "")).strip()
        side = str(row.get("Lean", "")).strip().lower()
        line_val = row.get("Line", "")
        line_float = float(line_val) if pd.notna(line_val) else None

        # Default output values
        prob, prob_val, conf, rec = 0.0, 0, "N/A", "❌"
        ballpark, home_away, note = "N/A", "N/A", ""
        edge = -1

        # Get player ID
        pid = roster_mapping.get(name.lower()) or get_player_id(name, roster_mapping)
        if not pid:
            note = "❌ Player ID not found"
        else:
            # Get game info (home/away, ballpark)
            info = get_game_info_for_player(name, roster_mapping, team_mapping, schedule_today)
            home_away = info.get("home_away", "N/A")
            ballpark = info.get("ballpark", "N/A")

            try:
                prob, prob_val, conf, rec, edge = evaluate_prop_v2(
                    player_name=name,
                    prop_type=prop_type,
                    line=line_float,
                    side=side,
                    is_home=(home_away == "Home"),
                    ballpark=ballpark,
                    player_id=pid
                )
            except Exception as e:
                note = f"⚠️ Eval failed: {str(e)}"

        results.append({
            "Player": name,
            "Prop": prop_type or "N/A",
            "Line": line_val,
            "Side": side.title() if side else "N/A",
            "Prob %": f"{prob_val:.1f}%" if prob_val else "N/A",
            "Confidence": conf,
            "Recommendation": rec,
            "Ballpark": ballpark,
            "Home/Away": home_away,
            "Edge": edge,
            "Note": note
        })

    # Convert to DataFrame and sort
    result_df = pd.DataFrame(results)
    result_df.sort_values(by="Edge", ascending=False, inplace=True)

    st.dataframe(result_df)

    st.download_button("📥 Download Full Evaluation", result_df.to_csv(index=False), file_name="evaluated_props.csv")

else:
    st.info("Upload a CSV to begin analysis.")
