import streamlit as st
import pandas as pd
import itertools
import requests

from evaluate_prop_v2 import evaluate_prop_v2
from prop_edge import get_player_id, build_roster_mapping
from game_utils import build_player_team_mapping, get_today_schedule, get_game_info_for_player

st.set_page_config(page_title="MLB Prop Evaluator", page_icon="⚾", layout="wide")
st.title("📊 MLB Prop Evaluator")

@st.cache_data(ttl=43200)
def load_data():
    return build_roster_mapping(), build_player_team_mapping(), get_today_schedule()

roster_mapping, team_mapping, schedule_today = load_data()

tab1, tab2, tab3 = st.tabs(["🔍 Single Prop", "📂 RotoWire CSV Upload", "🎯 Live Pick6"])

# ────────────────────────────── TAB 1 — Single Prop Evaluation ──────────────────────────────
with tab1:
    player_name = st.text_input("Player Name")
    prop_type = st.selectbox("Prop Type", [
        "hits", "total_bases", "walks", "batter_strikeouts",
        "strikeouts", "earned_runs", "outs", "hrr"
    ])
    line = st.number_input("Prop Line", min_value=0.0, value=1.5, step=0.5)
    side = st.radio("Betting Side", ["over", "under"])
    pitcher_name = st.text_input("Pitcher Name (optional)")
    umpire_name = st.text_input("Umpire Name (optional)")

    if st.button("Evaluate Prop"):
        player_id = get_player_id(player_name, roster_mapping)
        if not player_id:
            st.error("Player not found.")
        else:
            game_info = get_game_info_for_player(player_name, roster_mapping, team_mapping, schedule_today)
            is_home = game_info.get("home_away") == "Home"
            ballpark = game_info.get("ballpark")

            prob, details, confidence = evaluate_prop_v2(
                player_name=player_name,
                prop_type=prop_type,
                line=line,
                side=side,
                pitcher_name=pitcher_name or None,
                is_home=is_home,
                ballpark=ballpark,
                umpire=umpire_name or None,
                player_id=player_id,
            )

            st.metric(f"📊 Probability of {side.title()} {line}", f"{prob * 100:.1f}%")
            st.write(f"Confidence Score: {confidence}")
            st.write(f"Ballpark: `{ballpark}` | Home Game: `{is_home}`")

            with st.expander("Explanation"):
                for k, v in details.items():
                    st.write(f"**{k.replace('_', ' ').title()}**: {v}")

# ────────────────────────────── TAB 2 — RotoWire CSV Upload ──────────────────────────────
with tab2:
    csv_file = st.file_uploader("Upload RotoWire-style CSV", type=["csv"])

    if csv_file:
        df = pd.read_csv(csv_file)
        st.dataframe(df.head())

        prop_type_map = {
            "Hits": "hits", "Total Bases": "total_bases", "Singles": "hits", "Outs": "outs",
            "Earned Runs": "earned_runs", "Pitcher Strikeouts": "strikeouts", "Strikeouts": "strikeouts",
            "Walks": "walks", "Home Runs": "hrr", "Hits + Runs + RBIs": "hrr", "Hits+Runs+RBIs": "hrr"
        }
        lean_map = {"more": "over", "less": "under", "over": "over", "under": "under"}

        results = []
        for _, row in df.iterrows():
            name = row.get("Player")
            market = row.get("Market Name")
            line_val = row.get("Line")
            lean = row.get("Lean") or row.get("Prediction")
            if pd.isna(name) or pd.isna(market) or pd.isna(line_val) or pd.isna(lean):
                continue

            prop_type = prop_type_map.get(str(market).strip())
            side = lean_map.get(str(lean).strip().lower())
            if not prop_type or not side:
                continue

            try:
                line_float = float(line_val)
                pid = get_player_id(name, roster_mapping)
                if not pid:
                    continue
                game_info = get_game_info_for_player(name, roster_mapping, team_mapping, schedule_today)
                is_home = game_info.get("home_away") == "Home"
                ballpark = game_info.get("ballpark")

                prob, details, confidence = evaluate_prop_v2(
                    player_name=name,
                    prop_type=prop_type,
                    line=line_float,
                    side=side,
                    is_home=is_home,
                    ballpark=ballpark,
                    player_id=pid,
                )

                results.append({
                    "Player": name,
                    "Prop": prop_type,
                    "Line": line_float,
                    "Side": side.title(),
                    "Prob %": f"{prob * 100:.1f}%",
                    "Prob Val": prob * 100,
                    "Confidence": confidence,
                    "Recommendation": "✅" if prob > 0.55 else "❌" if prob < 0.45 else "🟡",
                    "Ballpark": ballpark,
                    "Home/Away": "Home" if is_home else "Away",
                    "Edge": round((3 * prob**2) - 1, 2)
                })

            except Exception:
                continue

        if results:
            df_results = pd.DataFrame(results)
            st.subheader("Grouped Results")
            st.dataframe(df_results.sort_values(by="Prob Val", ascending=False))

            st.subheader("Top Tier Picks (Prob ≥ 65%)")
            st.dataframe(df_results[df_results["Prob Val"] >= 65])

            st.subheader("✅ Recommended (55–64%)")
            st.dataframe(df_results[(df_results["Prob Val"] >= 55) & (df_results["Prob Val"] < 65)])

            st.subheader("❌ Avoid (< 45%)")
            st.dataframe(df_results[df_results["Prob Val"] < 45])

            st.subheader("💰 Value Edge: 2-Pick (3x payout)")
            st.dataframe(df_results.sort_values(by="Edge", ascending=False)[["Player", "Prop", "Line", "Side", "Prob %", "Edge"]])

            st.subheader("🧠 Multi-Leg Optimizer")

            def expected_edge(picks, multiplier):
                p = 1.0
                for pick in picks:
                    p *= pick["Prob Val"] / 100
                return round((multiplier * p) - 1, 3)

            def get_best_combos(n, payout):
                combos = list(itertools.combinations(results, n))
                ranked = []
                for combo in combos:
                    ranked.append({
                        "Players": ", ".join([p["Player"] for p in combo]),
                        "Props": " | ".join([f"{p['Prop']} {p['Side']} {p['Line']}" for p in combo]),
                        "Edge": expected_edge(combo, payout)
                    })
                return sorted(ranked, key=lambda x: x["Edge"], reverse=True)[:5]

            st.markdown("Top 2-Leg Combos (3x)")
            st.dataframe(get_best_combos(2, payout=3))

            st.markdown("Top 3-Leg Combos (5x)")
            st.dataframe(get_best_combos(3, payout=5))

            st.markdown("Top 5-Leg Combos (10x)")
            st.dataframe(get_best_combos(5, payout=10))

# ────────────────────────────── TAB 3 — Live Pick6 Props ──────────────────────────────
with tab3:
    if st.button("Fetch Live Props from Odds API"):
        try:
            odds_key = "831866f1ee85b3cd5265ff2572ddecc6"
            response = requests.get(
                "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds",
                params={
                    "apiKey": odds_key,
                    "regions": "us",
                    "markets": "player_props",
                    "oddsFormat": "american",
                },
                timeout=10,
            )
            games = response.json()
            evaluated = []

            for game in games:
                for book in game.get("bookmakers", []):
                    for market in book.get("markets", []):
                        for outcome in market.get("outcomes", []):
                            name = outcome.get("name", "")
                            line = outcome.get("point")
                            if not name or line is None:
                                continue
                            tokens = name.split()
                            side = tokens[-1].lower() if tokens[-1].lower() in {"over", "under"} else "over"
                            player_name = " ".join(tokens[:-1]) if side in tokens[-1].lower() else name
                            prop_type = market["key"]

                            pid = get_player_id(player_name, roster_mapping)
                            if not pid:
                                continue
                            game_info = get_game_info_for_player(player_name, roster_mapping, team_mapping, schedule_today)
                            is_home = game_info.get("home_away") == "Home"
                            ballpark = game_info.get("ballpark")

                            prob, details, confidence = evaluate_prop_v2(
                                player_name=player_name,
                                prop_type=prop_type,
                                line=line,
                                side=side,
                                is_home=is_home,
                                ballpark=ballpark,
                                player_id=pid,
                            )

                            evaluated.append({
                                "Player": player_name,
                                "Prop": prop_type,
                                "Side": side.title(),
                                "Line": line,
                                "Prob %": f"{prob * 100:.1f}%",
                                "Edge": round((3 * prob**2) - 1, 2),
                            })

            if evaluated:
                st.success("Live props evaluated")
                st.dataframe(pd.DataFrame(evaluated).sort_values(by="Edge", ascending=False))
            else:
                st.warning("No valid live props were returned.")

        except Exception as e:
            st.error(f"Error fetching or evaluating live props: {e}")
