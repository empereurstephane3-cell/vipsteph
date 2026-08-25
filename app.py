import streamlit as st
import time

# ==========================================
# 1. CONFIGURATION & DESIGN PREMIUM
# ==========================================
st.set_page_config(
    page_title="VIPSTEPH - Premium Match Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style global pour un design sombre épuré
st.markdown("""
    <style>
        .stApp { background-color: #090d12; color: #f3f4f6; }
        .match-container {
            background-color: #111822;
            border: 1px solid #1f293d;
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        }
        .stat-box {
            background-color: #0d121b;
            border: 1px solid #1f293d;
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DONNÉES API (SIMULÉES)
# ==========================================
@st.cache_data(ttl=60)
def fetch_api_matches(sport_category):
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
# 3. INTERFACE UTILISATEUR
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
            status_text = f"🔴 LIVE {match['time']}"
        elif status == "FT":
            status_text = "🏁 TERMINÉ"
        else:
            status_text = f"⏳ {match['time']}"

        # Utilisation d'un conteneur stylisé natif
        with st.container():
            st.markdown('<div class="match-container">', unsafe_allow_html=True)
            
            # En-tête du match (Compétition & Statut)
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
                st.markdown(f"**{match['competition']}** *({match['country']})*")
            with col_info2:
                st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 12px;'>{status_text}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Affichage des équipes et du score au centre
            col_home, col_score, col_away = st.columns([4, 2, 4])
            
            with col_home:
                c_img, c_name = st.columns([1, 4])
                with c_img:
                    st.image(match['home']['logo'], width=28)
                with c_name:
                    st.markdown(f"**{match['home']['name']}**")
                    
            with col_score:
                st.markdown(f"<div style='text-align: center; font-family: monospace; font-weight: bold; font-size: 20px; background: #070a0f; padding: 4px; border-radius: 8px; border: 1px solid #1f293d;'>{match['home']['goals']} - {match['away']['goals']}</div>", unsafe_allow_html=True)
                
            with col_away:
                c_name, c_img = st.columns([4, 1])
                with c_name:
                    st.markdown(f"<div style='text-align: right;'><b>{match['away']['name']}</b></div>", unsafe_allow_html=True)
                with c_img:
                    st.image(match['away']['logo'], width=28)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Volet d'analyses et marchés ciblés
        with st.expander(f"📊 Analyses & Marchés ciblés : {match['home']['name']} vs {match['away']['name']}"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>BUTS ATTENDUS (xG)</div>
                        <div style='font-size: 15px; font-weight: bold; color: #10b981;'>{match['stats']['goals_exp']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>CORNERS ATTENDUS</div>
                        <div style='font-size: 15px; font-weight: bold;'>{match['stats']['corners_exp']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>TIRS CADRÉS</div>
                        <div style='font-size: 15px; font-weight: bold;'>{match['stats']['shots_on_target_exp']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>2 SCORES EXACTS</div>
                        <div style='font-size: 13px; font-weight: bold; color: #38bdf8;'>{match['stats']['scores'][0]} / {match['stats']['scores'][1]}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="background-color: #070a0f; border-left: 3px solid #10b981; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                    💡 <b>Prédiction Recommandée :</b> <span style="color: #10b981;">{match['stats']['rec']}</span>
                </div>
            """, unsafe_allow_html=True)

render_matches_dashboard(sport_filter)
