
# streamlit_app.py (CSV-enabled)

import streamlit as st
import pandas as pd
from evaluate_prop_v2 import evaluate_prop_v2
from prop_edge import build_roster_mapping, get_player_id
from streamlit_app import build_player_team_mapping, get_today_schedule, get_game_info_for_player

st.set_page_config(page_title="MLB Prop Evaluator", page_icon="⚾", layout="wide")
st.title("📊 MLB Prop Evaluator (v2)")
st.write("Supports single prop evaluation or full RotoWire CSV slates.")

@st.cache_data(ttl=43200)
def load_data():
    return build_roster_mapping(), build_player_team_mapping(), get_today_schedule()

roster_mapping, team_mapping, schedule_today = load_data()

tab1, tab2 = st.tabs(["🔍 Single Prop", "📂 RotoWire CSV Upload"])

with tab1:
    player_name = st.text_input("Player Name", help="e.g. Mookie Betts")
    prop_type = st.selectbox("Prop Type", [
        "hits", "total_bases", "walks", "batter_strikeouts",
        "strikeouts", "earned_runs", "outs", "hrr"
    ])
    line = st.number_input("Prop Line", min_value=0.0, value=1.5, step=0.5)
    side = st.radio("Betting Side", ["over", "under"])
    pitcher_name = st.text_input("Pitcher Name (optional)", help="For BvP matchups")
    umpire_name = st.text_input("Umpire Name (optional)", help="Optional: include if known")

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
                pitcher_name=pitcher_name if pitcher_name else None,
                is_home=is_home,
                ballpark=ballpark,
                umpire=umpire_name if umpire_name else None,
                player_id=player_id,
            )

            st.metric(f"📊 Probability of {side.capitalize()} {line}", f"{prob * 100:.1f}%")
            st.write(f"🔐 Confidence Score: `{confidence}`")
            st.write(f"🏟️ Ballpark: `{ballpark}` — 🏠 Home Game: `{is_home}`")
            
            with st.expander("🔍 Full Explanation"):
                for k, v in details.items():
                    st.write(f"**{k.replace('_', ' ').title()}**: {v}")

            if prob > 0.55:
                st.success("✅ Recommend taking the Over" if side == "over" else "✅ Recommend taking the Under")
            elif prob < 0.45:
                st.warning("❌ Low probability — fade this line")
            else:
                st.info("🟡 No edge — stay away or find more data")

with tab2:
    st.subheader("📂 Upload RotoWire CSV")
    csv_file = st.file_uploader("Upload RotoWire-style CSV", type=["csv"])
    if csv_file is not None:
        df = pd.read_csv(csv_file)
        st.write("Preview of uploaded props:")
        st.dataframe(df.head())

        result_rows = []
        for _, row in df.iterrows():
            name = row.get("Player")
            market_name = row.get("Market Name")
            line_val = row.get("Line")
            lean = row.get("Lean") or row.get("Prediction")

            if pd.isna(name) or pd.isna(market_name) or pd.isna(line_val) or pd.isna(lean):
                continue

            # Normalize fields
            prop_type_map = {
                "Hits": "hits", "Total Bases": "total_bases", "Singles": "hits", "Outs": "outs",
                "Earned Runs": "earned_runs", "Pitcher Strikeouts": "strikeouts", "Strikeouts": "strikeouts",
                "Walks": "walks", "Home Runs": "hrr", "Hits + Runs + RBIs": "hrr", "Hits+Runs+RBIs": "hrr"
            }
            lean_map = {"more": "over", "less": "under", "over": "over", "under": "under"}

            prop_type = prop_type_map.get(str(market_name).strip())
            side = lean_map.get(str(lean).strip().lower())

            if not prop_type or not side:
                continue

            try:
                line_float = float(line_val)
            except Exception:
                continue

            player_id = get_player_id(name, roster_mapping)
            if not player_id:
                continue

            game_info = get_game_info_for_player(name, roster_mapping, team_mapping, schedule_today)
            is_home = game_info.get("home_away") == "Home"
            ballpark = game_info.get("ballpark")

            try:
                prob, details, confidence = evaluate_prop_v2(
                    player_name=name,
                    prop_type=prop_type,
                    line=line_float,
                    side=side,
                    is_home=is_home,
                    ballpark=ballpark,
                    player_id=player_id
                )
            except Exception:
                continue

            result_rows.append({
                "Player": name,
                "Prop": prop_type,
                "Line": line_float,
                "Side": side.title(),
                "Prob %": f"{prob * 100:.1f}%",
                "Confidence": confidence,
                "Recommendation": "✅" if prob > 0.55 else "❌" if prob < 0.45 else "🟡",
                "Ballpark": ballpark,
                "Home/Away": "Home" if is_home else "Away"
            })

        if result_rows:
            result_df = pd.DataFrame(result_rows)
            result_df = result_df.sort_values(by="Prob %", ascending=False)
            st.success(f"Evaluated {len(result_df)} props")
            st.dataframe(result_df)
        else:
            st.warning("No valid props could be evaluated.")


        if result_rows:
            result_df = pd.DataFrame(result_rows)
            result_df["Prob Val"] = result_df["Prob %"].str.rstrip("%").astype(float)
            result_df = result_df.sort_values(by=["Recommendation", "Prob Val"], ascending=[False, False])
            st.success(f"Evaluated {len(result_df)} props")

            # Grouped display
            st.subheader("🔥 Top Tier Props (Prob ≥ 65%)")
            st.dataframe(result_df[result_df["Prob Val"] >= 65])

            st.subheader("✅ Recommended (55%–64%)")
            st.dataframe(result_df[(result_df["Prob Val"] >= 55) & (result_df["Prob Val"] < 65)])

            st.subheader("🟡 No Edge (45%–54%)")
            st.dataframe(result_df[(result_df["Prob Val"] >= 45) & (result_df["Prob Val"] < 55)])

            st.subheader("❌ Avoid (< 45%)")
            st.dataframe(result_df[result_df["Prob Val"] < 45])


            # Add Value Edge column assuming Pick6 2-pick payout (3x)
            # Breakeven probability for 2-pick 3x payout = ~0.667
            st.subheader("📈 Value Edge Estimation (Pick6 - 3x Payout)")

            def calc_edge(prob_pct):
                prob = prob_pct / 100
                edge = (3 * prob**2) - 1  # Expected payout for 2-leg entry
                return round(edge, 2)

            result_df["Edge"] = result_df["Prob Val"].apply(calc_edge)
            top_edge_df = result_df.sort_values(by="Edge", ascending=False)

            st.dataframe(top_edge_df[["Player", "Prop", "Line", "Side", "Prob %", "Edge", "Recommendation"]])

            st.caption("🔍 Positive edge means profitable on 2-pick Pick6 entries")

        else:
            st.warning("No valid props could be evaluated.")

    st.divider()
    st.markdown("### 🔌 Coming Soon: Live Pick6 Integration")
    st.info("We'll soon pull live props directly from Pick6 and auto-evaluate them for you daily!")

            st.subheader("🧠 Multi-Leg Optimizer (Pick6 Combos)")
            st.caption("Top combinations by expected return (Pick6 payout rules assumed)")

            def expected_payout(picks, payout_multiplier):
                prob_product = 1.0
                for p in picks:
                    prob = p["Prob Val"] / 100
                    prob_product *= prob
                return round((payout_multiplier * prob_product) - 1, 3)  # Net profit vs breakeven

            def get_top_combos(n, payout, top_n=5):
                combos = list(itertools.combinations(result_rows, n))
                evaluated = []
                for combo in combos:
                    payout_val = expected_payout(combo, payout)
                    players = [p["Player"] for p in combo]
                    props = [f"{p['Prop']} {p['Side']} {p['Line']}" for p in combo]
                    prob_string = " x ".join([f"{p['Prob %']}" for p in combo])
                    evaluated.append({
                        "Players": ", ".join(players),
                        "Props": " | ".join(props),
                        "Probabilities": prob_string,
                        "Expected Edge": payout_val
                    })
                top_sorted = sorted(evaluated, key=lambda x: x["Expected Edge"], reverse=True)
                return top_sorted[:top_n]

            st.markdown("#### 🔢 Best 2-Leg Combos (3x payout)")
            best_2 = get_top_combos(2, payout=3)
            st.dataframe(best_2)

            st.markdown("#### 🔢 Best 3-Leg Combos (5x payout)")
            best_3 = get_top_combos(3, payout=5)
            st.dataframe(best_3)

            st.markdown("#### 🔢 Best 5-Leg Combos (10x payout)")
            best_5 = get_top_combos(5, payout=10)
            st.dataframe(best_5)

    st.divider()
    st.markdown("## 🎯 Live Pick6 Slate (Beta)")
    st.caption("Evaluating today's current props from Pick6 (via Odds API)...")

    if st.button("📡 Fetch Live Pick6 Props"):
        try:
            import requests
            base_url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
            params = {
                "apiKey": "831866f1ee85b3cd5265ff2572ddecc6",
                "regions": "us",
                "markets": "player_props",
                "oddsFormat": "american",
            }
            response = requests.get(base_url, params=params, timeout=10)
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
                                side = "over"  # default fallback

                            live_props.append({
                                "player_name": player_name,
                                "prop_type": market["key"],
                                "line": line,
                                "side": side,
                            })

            st.success(f"Pulled {len(live_props)} live props from Pick6")
            evaluated = []
            for p in live_props:
                player = p["player_name"]
                ptype = p["prop_type"]
                line = p["line"]
                side = p["side"]
                if not player or not line or not ptype:
                    continue

                player_id = get_player_id(player, roster_mapping)
                if not player_id:
                    continue

                game_info = get_game_info_for_player(player, roster_mapping, team_mapping, schedule_today)
                is_home = game_info.get("home_away") == "Home"
                ballpark = game_info.get("ballpark")

                try:
                    prob, details, confidence = evaluate_prop_v2(
                        player_name=player,
                        prop_type=ptype,
                        line=line,
                        side=side,
                        is_home=is_home,
                        ballpark=ballpark,
                        player_id=player_id
                    )
                except Exception:
                    continue

                evaluated.append({
                    "Player": player,
                    "Prop": ptype,
                    "Side": side.title(),
                    "Line": line,
                    "Prob %": f"{prob * 100:.1f}%",
                    "Confidence": confidence,
                    "Ballpark": ballpark,
                    "Home/Away": "Home" if is_home else "Away",
                    "Edge": round((3 * (prob**2)) - 1, 2)
                })

            if evaluated:
                df_live = pd.DataFrame(evaluated)
                df_live = df_live.sort_values(by="Edge", ascending=False)
                st.dataframe(df_live)
            else:
                st.warning("No valid live props were evaluable.")

        except Exception as e:
            st.error(f"Error fetching live props: {e}")
