import streamlit as st
import requests
from datetime import datetime, timedelta
import math
import time

# ==========================================
# 1. CONFIGURATION & DESIGN PREMIUM
# ==========================================
st.set_page_config(
    page_title="VIPSTEPH - Match Analyzer API",
    page_icon="⚽",
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
# 2. BARRE LATÉRALE & CONFIGURATION
# ==========================================
st.sidebar.header("⚙️ Configuration API")
api_key_input = st.sidebar.text_input("Clé API (API-Sports / API-Football)", type="password", placeholder="Entre ta clé ici...")

st.sidebar.markdown("---")
st.sidebar.header("📅 Sélection du mode & des dates")

mode_recherche = st.sidebar.radio("Mode de consultation", ["🔴 Matchs en direct (Live)", "📅 Choisir une date spécifique"])

today = datetime.now().date()
min_allowed_date = today - timedelta(days=1)
max_allowed_date = today + timedelta(days=1)

target_date = today
if mode_recherche == "📅 Choisir une date spécifique":
    target_date = st.sidebar.date_input(
        "Date des matchs (Plan Gratuit : 3 jours max)", 
        value=today,
        min_value=min_allowed_date,
        max_value=max_allowed_date
    )

league_choice = st.sidebar.selectbox(
    "Sélectionner la Compétition", 
    [
        "Tous les Championnats",
        "Premier League (Angleterre)",
        "La Liga (Espagne)",
        "Serie A (Italie)",
        "Bundesliga (Allemagne)",
        "UEFA Champions League",
        "NBA (Basketball)"
    ]
)

LEAGUE_IDS = {
    "Premier League (Angleterre)": 39,
    "La Liga (Espagne)": 140,
    "Serie A (Italie)": 135,
    "Bundesliga (Allemagne)": 78,
    "UEFA Champions League": 2,
    "NBA (Basketball)": 12
}

# ==========================================
# 3. RÉCUPÉRATION DES PRÉDICTIONS API AVEC GESTION DU RATE LIMIT
# ==========================================
@st.cache_data(ttl=3600)
def fetch_api_predictions(api_key, fixture_id):
    if not api_key or str(fixture_id).startswith("demo"):
        return None
    
    url = "https://v3.football.api-sports.io/predictions"
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': api_key
    }
    params = {"fixture": fixture_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 429:
            return "RATE_LIMIT"
        if response.status_code == 200:
            data = response.json().get("response", [])
            if data:
                return data[0]
    except Exception:
        pass
    return None

# ==========================================
# 4. MOTEUR POISSON TEMPOREL (FALLBACK SOLIDE)
# ==========================================
def poisson_pmf(lmbda, k):
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (lmbda**k) * math.exp(-lmbda) / math.factorial(k)

def calculate_robust_poisson(home_name, away_name, h_goals, a_goals, status_short, elapsed):
    base_home = 1.55
    base_away = 1.15
    
    top_teams = ["Arsenal", "Manchester City", "Real Madrid", "Barcelona", "Bayern Munich", "PSG", "Inter", "Liverpool"]
    if any(t.lower() in home_name.lower() for t in top_teams): base_home += 0.35
    if any(t.lower() in away_name.lower() for t in top_teams): base_away += 0.30

    if status_short in ["1H", "2H", "ET"] and elapsed and elapsed > 0:
        played_fraction = min(max(elapsed / 90.0, 0.05), 0.98)
        remaining_fraction = 1.0 - played_fraction
        lambda_home = h_goals + (base_home * remaining_fraction)
        lambda_away = a_goals + (base_away * remaining_fraction)
    else:
        lambda_home = base_home
        lambda_away = base_away

    home_win_prob, draw_prob, away_win_prob, btts_prob, over_25_prob = 0.0, 0.0, 0.0, 0.0, 0.0
    score_probabilities = []
    
    for h in range(6 + 1):
        for a in range(6 + 1):
            p_score = poisson_pmf(lambda_home, h) * poisson_pmf(lambda_away, a)
            score_probabilities.append(((h, a), p_score))
            if h > a: home_win_prob += p_score
            elif h == a: draw_prob += p_score
            else: away_win_prob += p_score
            if h > 0 and a > 0: btts_prob += p_score
            if (h + a) > 2.5: over_25_prob += p_score

    score_probabilities.sort(key=lambda x: x[1], reverse=True)
    hw_pct, dr_pct, aw_pct = round(home_win_prob * 100, 1), round(draw_prob * 100, 1), round(away_win_prob * 100, 1)

    return {
        "goals_exp": round(lambda_home + lambda_away, 2),
        "scores": [f"{score_probabilities[0][0][0]} - {score_probabilities[0][0][1]}", f"{score_probabilities[1][0][0]} - {score_probabilities[1][0][1]}"],
        "rec": f"Tendance : Victoire 1 ({hw_pct}%) ou Nul ({dr_pct}%)",
        "probabilities": f"1: {hw_pct}% | X: {dr_pct}% | 2: {aw_pct}%"
    }

# ==========================================
# 5. FONCTION API (FIXTURES)
# ==========================================
def fetch_real_api_data(api_key, mode, chosen_date, selected_league):
    if not api_key:
        return None, "⚠️ Aucune clé API saisie."
    
    url = "https://v3.football.api-sports.io/fixtures"
    if mode == "🔴 Matchs en direct (Live)":
        params = {"live": "all"}
    else:
        params = {"date": chosen_date.strftime('%Y-%m-%d')}
        if selected_league != "Tous les Championnats" and selected_league in LEAGUE_IDS:
            params["league"] = LEAGUE_IDS[selected_league]

    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': api_key
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 429:
            return None, "Erreur API-Sports : Limite de requêtes atteinte (10/min max sur le plan gratuit). Patiente quelques secondes."
        if response.status_code == 200:
            json_data = response.json()
            if "errors" in json_data and json_data["errors"]:
                err_msg = json_data["errors"]
                if isinstance(err_msg, dict):
                    err_msg = ", ".join([f"{k}: {v}" for k, v in err_msg.items()])
                return None, f"Erreur API-Sports : {err_msg}"
                
            data = json_data.get("response", [])
            formatted_matches = []
            
            for item in data:
                fixture = item["fixture"]
                league = item["league"]
                teams = item["teams"]
                goals = item["goals"]
                
                status_short = fixture["status"]["short"]
                elapsed = fixture["status"]["elapsed"]
                
                if status_short in ["1H", "2H", "HT", "ET", "P"]:
                    status_text = f"🔴 LIVE {elapsed}'" if elapsed else "🔴 LIVE"
                elif status_short == "FT":
                    status_text = f"🏁 TERMINÉ"
                else:
                    status_text = f"⏳ {fixture['date'][11:16]}"

                h_g = goals["home"] if goals["home"] is not None else 0
                a_g = goals["away"] if goals["away"] is not None else 0
                h_name = teams["home"]["name"]
                a_name = teams["away"]["name"]

                formatted_matches.append({
                    "id": str(fixture["id"]),
                    "competition": league["name"],
                    "country": league["country"],
                    "status": status_short,
                    "time": status_text,
                    "home": {"name": h_name, "logo": teams["home"]["logo"], "goals": h_g},
                    "away": {"name": a_name, "logo": teams["away"]["logo"], "goals": a_g},
                    "stats": calculate_robust_poisson(h_name, a_name, h_g, a_g, status_short, elapsed)
                })
            return formatted_matches, None
        else:
            return None, f"Erreur HTTP {response.status_code} : Vérifie ta clé API."
    except Exception as e:
        return None, f"Erreur réseau : {e}"

# ==========================================
# 6. INTERFACE PRINCIPALE
# ==========================================
st.title("⚽ VIPSTEPH - Match Analyzer API")
st.markdown("Tableau de bord combinant **Données API** et **Modèle de Sécurité (Anti-Rate Limit)**.")

matches, error_message = fetch_real_api_data(api_key_input, mode_recherche, target_date, league_choice)

if api_key_input:
    if error_message:
        st.error(error_message)
    else:
        st.success("✅ Clé API connectée avec succès !")
else:
    st.info("💡 Entre ta clé API dans la barre latérale pour charger les matchs.")

if not matches:
    if api_key_input and not error_message:
        st.warning(f"ℹ️ Aucun match trouvé. Exemple de démonstration :")
    
    matches = [
        {
            "id": "demo-1", "competition": "Premier League", "country": "England", "status": "NS", "time": "⏳ 18:30",
            "home": {"name": "Arsenal", "logo": "https://media.api-sports.io/football/teams/42.png", "goals": 0},
            "away": {"name": "Manchester City", "logo": "https://media.api-sports.io/football/teams/50.png", "goals": 0},
            "stats": calculate_robust_poisson("Arsenal", "Manchester City", 0, 0, "NS", 0)
        }
    ]

for match in matches:
    with st.container():
        st.markdown('<div class="match-container">', unsafe_allow_html=True)
        col_info1, col_info2 = st.columns([3, 1])
        with col_info1:
            st.markdown(f"**{match['competition']}** *({match['country']})*")
        with col_info2:
            st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 12px; color: #10b981;'>{match['time']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        col_home, col_score, col_away = st.columns([4, 2, 4])
        with col_home:
            c_img, c_name = st.columns([1, 4])
            with c_img: st.image(match['home']['logo'], width=28)
            with c_name: st.markdown(f"**{match['home']['name']}**")
        with col_score:
            st.markdown(f"<div style='text-align: center; font-family: monospace; font-weight: bold; font-size: 20px; background: #070a0f; padding: 4px; border-radius: 8px; border: 1px solid #1f293d;'>{match['home']['goals']} - {match['away']['goals']}</div>", unsafe_allow_html=True)
        with col_away:
            c_name, c_img = st.columns([4, 1])
            with c_name: st.markdown(f"<div style='text-align: right;'><b>{match['away']['name']}</b></div>", unsafe_allow_html=True)
            with c_img: st.image(match['away']['logo'], width=28)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander(f"📊 Analyse & Prédictions : {match['home']['name']} vs {match['away']['name']}"):
        
        official_data = None
        if match['status'] == "NS":
            with st.spinner("Récupération des prédictions de l'API..."):
                official_data = fetch_api_predictions(api_key_input, match['id'])
                # Petite pause pour éviter de saturer l'API gratuite si on ouvre plusieurs expanders d'affilée
                time.sleep(0.5)

        if official_data == "RATE_LIMIT":
            st.warning("⚠️ Limite de l'API atteinte (10 req/min). Basculement automatique sur l'analyse statistique locale :")
            official_data = None # Force le passage au bloc de secours ci-dessous

        if official_data:
            pred = official_data.get("predictions", {})
            winner = pred.get("winner", {})
            percent = pred.get("percent", {})
            
            st.markdown(f"<div style='color: #38bdf8; font-size: 12px; font-weight: bold; margin-bottom: 8px;'>📌 Source : Prédictions Officielles API-Sports</div>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px;'>VICTOIRE DOMICILE</div>
                        <div style='font-size: 16px; font-weight: bold; color: #10b981;'>{percent.get('home', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px;'>MATCH NUL</div>
                        <div style='font-size: 16px; font-weight: bold; color: #f59e0b;'>{percent.get('draw', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px;'>VICTOIRE EXTÉRIEUR</div>
                        <div style='font-size: 16px; font-weight: bold; color: #ef4444;'>{percent.get('away', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="background-color: #070a0f; border-left: 3px solid #38bdf8; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                    💡 <b>Conseil Officiel API :</b> <span style="color: #38bdf8;">{pred.get('advice', 'Aucun conseil disponible')}</span><br>
                    🏆 <b>Favori identifié :</b> {winner.get('name', 'Équilibré')} <i>({winner.get('comment', '')})</i>
                </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"<div style='color: #10b981; font-size: 12px; font-weight: bold; margin-bottom: 8px;'>📌 Source : Modèle Statistique / Alternatif</div>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px;'>BUTS ATTENDUS (xG)</div>
                        <div style='font-size: 15px; font-weight: bold; color: #10b981;'>{match['stats']['goals_exp']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px;'>PROBABILITÉS 1X2</div>
                        <div style='font-size: 12px; font-weight: bold;'>{match['stats']['probabilities']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                    <div class='stat-box'>
                        <div style='color: #9ca3af; font-size: 11px;'>SCORES PROBABLES</div>
                        <div style='font-size: 13px; font-weight: bold; color: #38bdf8;'>{match['stats']['scores'][0]} / {match['stats']['scores'][1]}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="background-color: #070a0f; border-left: 3px solid #10b981; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                    💡 <b>Pronostic Recommandé :</b> <span style="color: #10b981;">{match['stats']['rec']}</span>
                </div>
            """, unsafe_allow_html=True)
