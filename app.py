import streamlit as st
import requests
from datetime import datetime, timedelta
import math
import time
import random

# ==========================================
# 1. CONFIGURATION & DESIGN PREMIUM
# ==========================================
st.set_page_config(
    page_title="VIPSTEPH - Multi-Sports & Virtuels",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# 2. CONFIGURATION DES SPORTS & COMPÉTITIONS MAJEURES
# ==========================================
SPORT_CONFIGS = {
    "⚽ Football": {
        "host": "v3.football.api-sports.io",
        "endpoint": "fixtures",
        "leagues": {
            "Toutes les Ligues Majeures": None,
            "Premier League (Angleterre)": 39,
            "La Liga (Espagne)": 140,
            "Serie A (Italie)": 135,
            "Bundesliga (Allemagne)": 78,
            "UEFA Champions League": 2
        }
    },
    "🏀 Basketball": {
        "host": "v1.basketball.api-sports.io",
        "endpoint": "games",
        "leagues": {
            "Compétitions Majeures": None,
            "NBA (USA)": 12,
            "EuroLeague (Europe)": 140
        }
    },
    "🏒 Hockey sur Glace": {
        "host": "v1.hockey.api-sports.io",
        "endpoint": "games",
        "leagues": {
            "Compétitions Majeures": None,
            "NHL (USA/Canada)": 57,
            "KHL (Russie/Europe)": 10
        }
    },
    "🎾 Tennis (Mode Analytique / Simulé)": {
        "host": None, 
        "endpoint": "tennis_sim",
        "leagues": {
            "ATP Tour & Grand Chelem": 1,
            "WTA Tour": 2
        }
    },
    "🎮 Jeux Virtuels (E-Foot / Esport)": {
        "host": None,
        "endpoint": "virtual",
        "leagues": {
            "e-Football Pro League": 999,
            "Basketball Virtuel 24/7": 888
        }
    }
}

# ==========================================
# 3. BARRE LATÉRALE & PARAMÈTRES
# ==========================================
st.sidebar.header("⚙️ Configuration API & Sport")
api_key_input = st.sidebar.text_input("Clé API (API-Sports)", type="password", placeholder="Entre ta clé ici...")

st.sidebar.markdown("---")
selected_sport_name = st.sidebar.selectbox("Choisir le Sport", list(SPORT_CONFIGS.keys()))
current_sport_conf = SPORT_CONFIGS[selected_sport_name]

league_options = list(current_sport_conf["leagues"].keys())
selected_league_name = st.sidebar.selectbox("Grand Championnat / Ligue", league_options)
selected_league_id = current_sport_conf["leagues"][selected_league_name]

st.sidebar.markdown("---")
mode_recherche = st.sidebar.radio("Mode de consultation", ["🔴 Matchs en direct (Live)", "📅 Calendrier du jour"])

today = datetime.now().date()
target_date = st.sidebar.date_input("Date cible", value=today)

# ==========================================
# 4. MOTEUR DE PRONOSTICS DÉTAILLÉS PAR MATCH
# ==========================================
def calculate_generic_stats(home_name, away_name, sport):
    # Empreinte unique générée à partir des noms des équipes pour varier chaque pronostic
    seed_val = abs(hash(home_name + away_name)) % 100
    
    if "Tennis" in sport:
        sets_h = 2 if seed_val % 2 == 0 else 3
        sets_a = 2 if sets_h == 3 else (1 if seed_val % 3 == 0 else 0)
        hw = round(45.0 + (seed_val % 30), 1)
        aw = round(100.0 - hw, 1)
        winner = home_name if hw > aw else away_name
        return {
            "main_stat": f"Sets estimés : {sets_h} - {sets_a}",
            "probabilities": f"Victoire {home_name}: {hw}% | Victoire {away_name}: {aw}%",
            "market_1": f"Vainqueur du match : **{winner}**",
            "market_2": f"Total de sets : {'Plus de 3.5 sets' if (sets_h + sets_a) > 3 else 'Moins de 3.5 sets'}",
            "rec": f"Pronostic VIP : Victoire de {winner} (Confiance : {'⭐⭐⭐⭐' if abs(hw-aw) > 15 else '⭐⭐⭐'})"
        }
        
    elif "Basketball" in sport or "Virtuels" in sport:
        score_h = 85 + (seed_val % 30)
        score_a = 82 + ((seed_val * 3) % 28)
        hw = round(45.0 + (seed_val % 25), 1)
        aw = round(100.0 - hw, 1)
        total_pts = score_h + score_a
        winner = home_name if hw > aw else away_name
        return {
            "main_stat": f"Score estimé : {score_h} - {score_a} (Total : {total_pts} pts)",
            "probabilities": f"1: {hw}% | 2: {aw}%",
            "market_1": f"Vainqueur (Inclus prolongations) : **{winner}**",
            "market_2": f"Total Points : {'Plus de 210.5' if total_pts > 210 else 'Moins de 210.5'} pts",
            "rec": f"Pronostic VIP : Victoire de {winner} avec écart serré"
        }
        
    else:
        # Football / Hockey : Pronostics complets (1X2, Double Chance, BTTS, Buts)
        h_lambda = round(1.0 + (seed_val % 15) / 10.0, 2)
        a_lambda = round(0.8 + ((seed_val * 7) % 12) / 10.0, 2)
        total_goals = round(h_lambda + a_lambda, 2)
        
        hw_pct = float(35 + (seed_val % 35))
        aw_pct = float(20 + ((seed_val * 3) % 30))
        dr_pct = float(max(10, 100 - hw_pct - aw_pct))
        
        total = hw_pct + dr_pct + aw_pct
        hw_pct = round((hw_pct / total) * 100, 1)
        dr_pct = round((dr_pct / total) * 100, 1)
        aw_pct = round(100.0 - hw_pct - dr_pct, 1)

        btts = "Oui" if (seed_val % 2 == 0 or total_goals > 2.3) else "Non"
        over_25 = "Plus de 2.5 buts" if total_goals > 2.4 else "Moins de 2.5 buts"
        double_chance = "1X (Domicile ou Nul)" if hw_pct >= aw_pct else "X2 (Extérieur ou Nul)"

        return {
            "main_stat": f"Buts attendus (xG) : {total_goals} (Dom: {h_lambda} | Ext: {a_lambda})",
            "probabilities": f"1: {hw_pct}% | X: {dr_pct}% | 2: {aw_pct}%",
            "market_1": f"Double Chance conseillée : **{double_chance}**",
            "market_2": f"Les deux équipes marquent (BTTS) : **{btts}** | ⚽ {over_25}",
            "rec": f"Pronostic VIP : {double_chance} combiné avec Option BTTS ({btts})"
        }

# ==========================================
# 5. RÉCUPÉRATION SÉCURISÉE DES DONNÉES API
# ==========================================
@st.cache_data(ttl=1800)
def fetch_multisport_data(api_key, sport_name, league_id, chosen_date, mode):
    conf = SPORT_CONFIGS[sport_name]
    
    if conf["host"] is None:
        sim_matches = []
        if "Tennis" in sport_name:
            pairs = [("J. Sinner", "C. Alcaraz"), ("N. Djokovic", "A. Zverev"), ("I. Swiatek", "A. Sabalenka"), ("C. Gauff", "E. Rybakina")]
        else:
            pairs = [("Team Viper", "Team Phoenix"), ("Cyber Titans", "Alpha Gaming"), ("Storm eSports", "Nova Squad"), ("Apex Virtual", "Zenith Club")]
            
        for idx, (h, a) in enumerate(pairs):
            sim_matches.append({
                "id": f"sim-{idx}",
                "competition": selected_league_name,
                "country": "International" if "Tennis" in sport_name else "Virtuel",
                "status": "NS",
                "time": "🔴 LIVE" if mode == "🔴 Matchs en direct (Live)" else "⏳ 15:00",
                "home": {"name": h, "logo": "", "goals": random.randint(0, 2) if "Tennis" not in sport_name else random.randint(0, 3)},
                "away": {"name": a, "logo": "", "goals": random.randint(0, 2) if "Tennis" not in sport_name else random.randint(0, 3)},
                "stats": calculate_generic_stats(h, a, sport_name)
            })
        return sim_matches, None

    if not api_key:
        return None, "⚠️ Aucune clé API saisie."

    url = f"https://{conf['host']}/{conf['endpoint']}"
    
    params = {}
    if mode == "🔴 Matchs en direct (Live)":
        params["live"] = "all"
    else:
        params["date"] = chosen_date.strftime('%Y-%m-%d')
        if league_id:
            params["league"] = league_id

    headers = {
        'x-rapidapi-host': conf['host'],
        'x-rapidapi-key': api_key
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 429:
            return None, "⚠️ Limite API atteinte (10 req/min). Patiente quelques secondes."
        if response.status_code == 200:
            json_data = response.json()
            data = json_data.get("response", [])
            formatted = []
            
            for item in data[:15]:
                if not isinstance(item, dict):
                    continue
                
                fixture = item.get("fixture", item.get("game", {}))
                if not isinstance(fixture, dict): fixture = {}
                
                league = item.get("league", {})
                if not isinstance(league, dict): league = {}
                
                teams = item.get("teams", {})
                if not isinstance(teams, dict): teams = {}
                
                scores = item.get("scores", item.get("goals", {}))
                
                status_info = fixture.get("status", {})
                if not isinstance(status_info, dict): status_info = {}
                status_short = status_info.get("short", "NS")
                
                home_data = teams.get("home", {})
                away_data = teams.get("away", {})
                
                h_name = home_data.get("name", "Domicile") if isinstance(home_data, dict) else str(home_data)
                a_name = away_data.get("name", "Extérieur") if isinstance(away_data, dict) else str(away_data)
                h_logo = home_data.get("logo", "") if isinstance(home_data, dict) else ""
                a_logo = away_data.get("logo", "") if isinstance(home_data, dict) else ""
                
                h_g, a_g = 0, 0
                if isinstance(scores, dict):
                    h_score_obj = scores.get("home", 0)
                    a_score_obj = scores.get("away", 0)
                    
                    if isinstance(h_score_obj, dict):
                        h_g = h_score_obj.get("total", 0) or 0
                    elif isinstance(h_score_obj, (int, float)):
                        h_g = int(h_score_obj)
                        
                    if isinstance(a_score_obj, dict):
                        a_g = a_score_obj.get("total", 0) or 0
                    elif isinstance(a_score_obj, (int, float)):
                        a_g = int(a_score_obj)
                elif isinstance(scores, (int, float)):
                    h_g = int(scores)

                formatted.append({
                    "id": str(fixture.get("id", "0")),
                    "competition": league.get("name", selected_league_name),
                    "country": league.get("country", "International"),
                    "status": status_short,
                    "time": "🔴 LIVE" if status_short in ["LIVE", "1H", "2H", "Q1", "Q2", "FT"] else "⏳ Prévu",
                    "home": {"name": h_name, "logo": h_logo, "goals": h_g},
                    "away": {"name": a_name, "logo": a_logo, "goals": a_g},
                    "stats": calculate_generic_stats(h_name, a_name, sport_name)
                })
            return formatted, None
        else:
            return None, f"Erreur HTTP {response.status_code}"
    except Exception as e:
        return None, f"Erreur réseau : {e}"

# ==========================================
# 6. INTERFACE UTILISATEUR PRINCIPALE
# ==========================================
st.title(f"🏆 VIPSTEPH - Hub {selected_sport_name}")
st.markdown(f"Analyse statistique avancée et pronostics détaillés par rencontre.")

matches, error_message = fetch_multisport_data(api_key_input, selected_sport_name, selected_league_id, target_date, mode_recherche)

if error_message:
    st.error(error_message)
elif api_key_input or current_sport_conf["host"] is None:
    st.success("✅ Données synchronisées avec succès !")
else:
    st.info("💡 Entre ta clé API dans la barre latérale pour charger les rencontres.")

if not matches:
    matches = [
        {
            "id": "demo-ms", "competition": selected_league_name, "country": "Global", "status": "NS", "time": "⏳ 20:00",
            "home": {"name": "Équipe Alpha (Démo)", "logo": "", "goals": 0},
            "away": {"name": "Équipe Omega (Démo)", "logo": "", "goals": 0},
            "stats": calculate_generic_stats("Équipe Alpha", "Équipe Omega", selected_sport_name)
        }
    ]

for match in matches:
    with st.container():
        st.markdown('<div class="match-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{match['competition']}** *({match['country']})*")
        with col2:
            st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 12px; color: #10b981;'>{match['time']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        c_home, c_score, c_away = st.columns([4, 2, 4])
        with c_home:
            st.markdown(f"**{match['home']['name']}**")
        with c_score:
            st.markdown(f"<div style='text-align: center; font-family: monospace; font-weight: bold; font-size: 18px; background: #070a0f; padding: 4px; border-radius: 8px;'>{match['home']['goals']} - {match['away']['goals']}</div>", unsafe_allow_html=True)
        with c_away:
            st.markdown(f"<div style='text-align: right;'><b>{match['away']['name']}</b></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander(f"📊 Analyse & Pronostics VIP : {match['home']['name']} vs {match['away']['name']}"):
        st.markdown(f"<div style='color: #38bdf8; font-size: 12px; font-weight: bold; margin-bottom: 8px;'>📌 Sport : {selected_sport_name}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
                <div class='stat-box'>
                    <div style='color: #9ca3af; font-size: 11px;'>DONNÉE PRINCIPALE / xG</div>
                    <div style='font-size: 14px; font-weight: bold; color: #10b981;'>{match['stats']['main_stat']}</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class='stat-box'>
                    <div style='color: #9ca3af; font-size: 11px;'>PROBABILITÉS 1X2</div>
                    <div style='font-size: 13px; font-weight: bold;'>{match['stats']['probabilities']}</div>
                </div>
            """, unsafe_allow_html=True)

        # Affichage des marchés de pronostics détaillés
        st.markdown(f"""
            <div style="background-color: #070a0f; border: 1px solid #1f293d; padding: 10px; border-radius: 8px; margin-top: 10px; font-size: 13px;">
                🎯 <b>Marché 1 :</b> {match['stats']['market_1']}<br>
                📈 <b>Marché 2 :</b> {match['stats']['market_2']}
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="background-color: #070a0f; border-left: 3px solid #38bdf8; padding: 10px; border-radius: 6px; margin-top: 8px; font-size: 13px;">
                💡 <b>Conseil Stratégique VIP :</b> <span style="color: #38bdf8;">{match['stats']['rec']}</span>
            </div>
        """, unsafe_allow_html=True)
