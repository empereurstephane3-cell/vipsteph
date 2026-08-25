import streamlit as st
import requests
import time
import textwrap

# ==========================================
# 1. CONFIGURATION & DESIGN PREMIUM
# ==========================================
st.set_page_config(
    page_title="VIPSTEPH - Premium Match Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        :root {
            --bg-main: #090d12;
            --bg-card: #111822;
            --border-color: #1f293d;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        .stApp { background-color: var(--bg-main); color: var(--text-main); }
        
        .match-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        }
        .badge-live {
            background-color: rgba(239, 68, 68, 0.2);
            color: var(--accent-red);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }
        .badge-ns {
            background-color: rgba(156, 163, 175, 0.1);
            color: var(--text-muted);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-ft {
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }
        .stat-box {
            background-color: #0d121b;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            font-size: 12px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONNEXION API & RECUPÉRATION DES DONNÉES
# ==========================================
@st.cache_data(ttl=60)
def fetch_api_matches(sport_category):
    # Données simulées (prêtes à être branchées sur ta vraie API)
    mock_api_data = [
        {
            "id": "101",
            "sport": "Football",
            "competition": "Premier League",
            "country": "Angleterre",
            "status": "1H",
            "time": "34'",
            "home": {"name": "Arsenal", "logo": "https://media.api-sports.io/football/teams/42.png", "goals": 1},
            "away": {"name": "Chelsea", "logo": "https://media.api-sports.io/football/teams/49.png", "goals": 0},
            "stats": {"corners_exp": 10.5, "goals_exp": 2.8, "shots_on_target_exp": 9.2, "scores": ["2 - 1", "3 - 1"], "rec": "Victoire Arsenal ou Plus de 1.5 buts"}
        },
        {
            "id": "102",
            "sport": "Basketball",
            "competition": "NBA",
            "country": "USA",
            "status": "NS",
            "time": "02:00",
            "home": {"name": "Los Angeles Lakers", "logo": "https://media.api-sports.io/basketball/teams/145.png", "goals": "-"},
            "away": {"name": "Boston Celtics", "logo": "https://media.api-sports.io/basketball/teams/138.png", "goals": "-"},
            "stats": {"corners_exp": "N/A", "goals_exp": "224.5 pts", "shots_on_target_exp": "N/A", "scores": ["112 - 108", "115 - 110"], "rec": "Victoire Celtics (Handicap)"}
        },
        {
            "id": "103",
            "sport": "FIFA / Esport",
            "competition": "EA FC Pro League",
            "country": "Esport",
            "status": "FT",
            "time": "Terminé",
            "home": {"name": "Umut", "logo": "https://media.api-sports.io/team-default.png", "goals": 4},
            "away": {"name": "F2Tekkz", "logo": "https://media.api-sports.io/team-default.png", "goals": 2},
            "stats": {"corners_exp": 6.0, "goals_exp": 5.5, "shots_on_target_exp": 12.0, "scores": ["4 - 2", "5 - 2"], "rec": "Plus de 3.5 buts (Validé ✅)"}
        }
    ]
    
    if sport_category == "TOUS":
        return mock_api_data
    return [m for m in mock_api_data if sport_category.lower() in m["sport"].lower()]

# ==========================================
# 3. INTERFACE PRINCIPALE & ACTUALISATION LIVE
# ==========================================
st.title("⚽ VIPSTEPH - Match Analyzer API")
st.markdown("Plateforme professionnelle multi-sports connectée en temps réel.")

st.sidebar.header("⚙️ Paramètres & API")
sport_filter = st.sidebar.selectbox(
    "Filtrer par Sport / Type", 
    ["TOUS", "Football", "Basketball", "FIFA / Esport", "Virtuel"]
)
auto_refresh = st.sidebar.checkbox("Actualisation Automatique (Live)", value=True)

@st.fragment(run_every=15 if auto_refresh else None)
def render_matches_dashboard(selected_sport):
    matches = fetch_api_matches(selected_sport)
    
    if not matches:
        st.warning("Aucun match disponible pour le moment via l'API.")
        return

    st.caption(f"Dernière synchronisation API : {time.strftime('%H:%M:%S')}")

    for match in matches:
        status = match["status"]
        if status in ["1H", "2H", "HT"]:
            status_badge = f"<span class='badge-live'>🔴 LIVE {match['time']}</span>"
        elif status == "FT":
            status_badge = f"<span class='badge-ft'>🏁 TERMINÉ</span>"
        else:
            status_badge = f"<span class='badge-ns'>⏳ {match['time']}</span>"

        # Utilisation de textwrap.dedent pour forcer Streamlit à interpréter le HTML correctement
        card_html = textwrap.dedent(f"""
            <div class='match-card'>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #9ca3af; text-transform: uppercase; margin-bottom: 12px;">
                    <span><b>{match['competition']}</b> ({match['country']})</span>
                    <span>{status_badge}</span>
                </div>
                
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px; width: 40%;">
                        <img src="{match['home']['logo']}" width="28" height="28" style="object-fit: contain;">
                        <span style="font-weight: 700; font-size: 15px;">{match['home']['name']}</span>
                    </div>
                    <div style="font-family: monospace; font-weight: bold; font-size: 18px; background: #070a0f; padding: 4px 14px; border-radius: 8px; border: 1px solid #1f293d;">
                        {match['home']['goals']} - {match['away']['goals']}
                    </div>
                    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; width: 40%;">
                        <span style="font-weight: 700; font-size: 15px; text-align: right;">{match['away']['name']}</span>
                        <img src="{match['away']['logo']}" width="28" height="28" style="object-fit: contain;">
                    </div>
                </div>
            </div>
        """)
        
        st.markdown(card_html, unsafe_allow_html=True)

        # Volet des marchés spécifiques
        with st.expander(f"📊 Analyses & Marchés ciblés : {match['home']['name']} vs {match['away']['name']}"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(textwrap.dedent(f"""
                    <div class='stat-box'>
                        <p style='color: #9ca3af; margin-bottom: 2px;'>BUTS ATTENDUS (xG)</p>
                        <p style='font-size: 15px; font-weight: bold; color: #10b981;'>{match['stats']['goals_exp']}</p>
                    </div>
                """), unsafe_allow_html=True)
            with c2:
                st.markdown(textwrap.dedent(f"""
                    <div class='stat-box'>
                        <p style='color: #9ca3af; margin-bottom: 2px;'>CORNERS ATTENDUS</p>
                        <p style='font-size: 15px; font-weight: bold;'>{match['stats']['corners_exp']}</p>
                    </div>
                """), unsafe_allow_html=True)
            with c3:
                st.markdown(textwrap.dedent(f"""
                    <div class='stat-box'>
                        <p style='color: #9ca3af; margin-bottom: 2px;'>TIRS CADRÉS ATTENDUS</p>
                        <p style='font-size: 15px; font-weight: bold;'>{match['stats']['shots_on_target_exp']}</p>
                    </div>
                """), unsafe_allow_html=True)
            with c4:
                st.markdown(textwrap.dedent(f"""
                    <div class='stat-box'>
                        <p style='color: #9ca3af; margin-bottom: 2px;'>2 SCORES EXACTS</p>
                        <p style='font-size: 13px; font-weight: bold; color: #38bdf8;'>{match['stats']['scores'][0]} / {match['stats']['scores'][1]}</p>
                    </div>
                """), unsafe_allow_html=True)

            st.markdown(textwrap.dedent(f"""
                <div style="background-color: #070a0f; border-left: 3px solid #10b981; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                    💡 <b>Prédiction Recommandée :</b> <span style="color: #10b981;">{match['stats']['rec']}</span>
                </div>
            """), unsafe_allow_html=True)

render_matches_dashboard(sport_filter)
