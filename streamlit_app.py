import streamlit as st
import pandas as pd
import itertools
from evaluate_prop_v2 import evaluate_prop_v2
from prop_edge import build_roster_mapping, get_player_id
from streamlit_app import build_player_team_mapping, get_today_schedule, get_game_info_for_player

st.set_page_config(page_title="MLB Prop Evaluator", page_icon="⚾", layout="wide")
st.title("📊 MLB Prop Evaluator (v2)")
st.write("Supports single prop evaluation, RotoWire CSV slates, live Pick6 props, and combo optimization.")

@st.cache_data(ttl=43200)
def load_data():
    return build_roster_mapping(), build_player_team_mapping(), get_today_schedule()

roster_mapping, team_mapping, schedule_today = load_data()

tab1, tab2, tab3 = st.tabs(["🔍 Single Prop", "📂 RotoWire CSV Upload", "🎯 Live Pick6 Slate"])

# ----------- SINGLE PROP TAB -----------
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
                player_name, prop_type, line, side,
                pitcher_name=pitcher_name or None,
                is_home=is_home,
                ballpark=ballpark,
                umpire=umpire_name or None,
                player_id=player_id
            )

            st.metric(f"📊 Probability of {side.capitalize()} {line}", f"{prob * 100:.1f}%")
            st.write(f"🔐 Confidence: {confidence}")
            st.write(f"🏟️ Ballpark: {ballpark} — 🏠 Home: {is_home}")

            with st.expander("🔍 Explanation"):
                for k, v in details.items():
                    st.write(f"**{k.replace('_', ' ').title()}**: {v}")

            if prob > 0.55:
                st.success("✅ Recommended")
            elif prob < 0.45:
                st.warning("❌ Avoid")
            else:
                st.info("🟡 No edge")

# ----------- ROTOWIRE CSV TAB -----------
with tab2:
    st.subheader("Upload RotoWire CSV")
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

        result_rows = []
        for _, row in df.iterrows():
            name = row.get("Player")
            market = row.get("Market Name")
            line_val = row.get("Line")
            lean = row.get("Lean") or row.get("Prediction")

            prop_type = prop_type_map.get(str(market).strip())
            side = lean_map.get(str(lean).strip().lower())

            if not all([name, prop_type, line_val, side]):
                continue

            try:
                line_float = float(line_val)
                player_id = get_player_id(name, roster_mapping)
                if not player_id:
                    continue

                game_info = get_game_info_for_player(name, roster_mapping, team_mapping, schedule_today)
                is_home = game_info.get("home_away") == "Home"
                ballpark = game_info.get("ballpark")

                prob, details, confidence = evaluate_prop_v2(
                    name, prop_type, line_float, side,
                    is_home=is_home, ballpark=ballpark, player_id=player_id
                )

                result_rows.append({
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
                    "Edge": round((3 * (prob**2)) - 1, 2)
                })

            except Exception:
                continue

        if result_rows:
            df_all = pd.DataFrame(result_rows).sort_values(by="Prob Val", ascending=False)

            st.subheader("🔥 Top Tier Props (Prob ≥ 65%)")
            st.dataframe(df_all[df_all["Prob Val"] >= 65])

            st.subheader("✅ Recommended (55–64%)")
            st.dataframe(df_all[(df_all["Prob Val"] >= 55) & (df_all["Prob Val"] < 65)])

            st.subheader("🟡 No Edge (45–54%)")
            st.dataframe(df_all[(df_all["Prob Val"] >= 45) & (df_all["Prob Val"] < 55)])

            st.subheader("❌ Avoid (< 45%)")
            st.dataframe(df_all[df_all["Prob Val"] < 45])

            st.subheader("💰 Value Edge (2-leg 3x Payout)")
            df_sorted = df_all.sort_values(by="Edge", ascending=False)
            st.dataframe(df_sorted[["Player", "Prop", "Line", "Side", "Prob %", "Edge", "Recommendation"]])

            st.subheader("🧠 Multi-Leg Optimizer (Pick6 Combos)")
            def expected_payout(picks, multiplier):
                prob_product = 1.0
                for p in picks:
                    prob = p["Prob Val"] / 100
                    prob_product *= prob
                return round(multiplier * prob_product - 1, 3)

            def get_top_combos(n, payout):
                combos = list(itertools.combinations(result_rows, n))
                ranked = []
                for c in combos:
                    ranked.append({
                        "Players": ", ".join(p["Player"] for p in c),
                        "Props": " | ".join(f"{p['Prop']} {p['Side']} {p['Line']}" for p in c),
                        "Probabilities": " x ".join(p["Prob %"] for p in c),
                        "Expected Edge": expected_payout(c, payout)
                    })
                return sorted(ranked, key=lambda x: x["Expected Edge"], reverse=True)[:5]

            st.markdown("#### 🔢 Best 2-Leg Combos (3x payout)")
            st.dataframe(get_top_combos(2, payout=3))

            st.markdown("#### 🔢 Best 3-Leg Combos (5x payout)")
            st.dataframe(get_top_combos(3, payout=5))

            st.markdown("#### 🔢 Best 5-Leg Combos (10x payout)")
            st.dataframe(get_top_combos(5, payout=10))

# ----------- LIVE PICK6 TAB -----------
with tab3:
    st.markdown("## 🎯 Live Pick6 Slate (Beta)")
    st.caption("Fetches props from The Odds API (free plan, beta support).")

    if st.button("📡 Fetch Live Pick6 Props"):
        try:
            import requests
            response = requests.get(
                "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds",
                params={
                    "apiKey": "831866f1ee85b3cd5265ff2572ddecc6",
                    "regions": "us",
                    "markets": "player_props",
                    "oddsFormat": "american"
                },
                timeout=10
            )
            games = response.json()
            live_props = []

            for game in games:
                for bookmaker in game.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        for outcome in market.get("outcomes", []):
                            name = outcome.get("name")
                            line = outcome.get("point")
                            if not name or line is None:
                                continue
                            tokens = name.split()
                            if tokens[-1].lower() in {"over", "under"}:
                                side = tokens[-1].lower()
                                player_name = " ".join(tokens[:-1])
                            else:
                                player_name = name
                                side = "over"
                            live_props.append({
                                "player_name": player_name,
                                "prop_type": market["key"],
                                "line": line,
                                "side": side,
                            })

            evaluated = []
            for p in live_props:
                pid = get_player_id(p["player_name"], roster_mapping)
                if not pid:
                    continue
                game_info = get_game_info_for_player(p["player_name"], roster_mapping, team_mapping, schedule_today)
                is_home = game_info.get("home_away") == "Home"
                ballpark = game_info.get("ballpark")

                try:
                    prob, details, confidence = evaluate_prop_v2(
                        player_name=p["player_name"],
                        prop_type=p["prop_type"],
                        line=p["line"],
                        side=p["side"],
                        is_home=is_home,
                        ballpark=ballpark,
                        player_id=pid
                    )
                except Exception:
                    continue

                evaluated.append({
                    "Player": p["player_name"],
                    "Prop": p["prop_type"],
                    "Line": p["line"],
                    "Side": p["side"].title(),
                    "Prob %": f"{prob * 100:.1f}%",
                    "Edge": round((3 * (prob**2)) - 1, 2)
                })

            if evaluated:
                st.success(f"Evaluated {len(evaluated)} live props.")
                st.dataframe(pd.DataFrame(evaluated).sort_values(by="Edge", ascending=False))
            else:
                st.warning("No valid props could be evaluated.")

        except Exception as e:
            st.error(f"Error fetching props: {e}")
