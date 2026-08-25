import streamlit as st
import requests
from datetime import datetime
import math

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

target_date = datetime.now()
if mode_recherche == "📅 Choisir une date spécifique":
    target_date = st.sidebar.date_input("Date des matchs", value=datetime.now())

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
# 3. MOTEUR MATHÉMATIQUE DE LA LOI DE POISSON
# ==========================================
def poisson_pmf(lmbda, k):
    """Calcule la probabilité de Poisson pour k buts sachant la moyenne lambda."""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (lmbda**k) * math.exp(-lmbda) / math.factorial(k)

def calculate_poisson_analysis(home_name, away_name, h_goals, a_goals, status_short):
    # Estimation des taux de buts attendus (lambda) ajustés avec les buts réels si le match a commencé
    base_lambda_home = 1.45 + (h_goals * 0.5)
    base_lambda_away = 1.15 + (a_goals * 0.5)

    home_win_prob = 0.0
    draw_prob = 0.0
    away_win_prob = 0.0
    btts_prob = 0.0
    over_25_prob = 0.0

    score_probabilities = []
    max_goals = 5

    # Calcul de la matrice de Poisson (tous les scores de 0-0 à 5-5)
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p_home = poisson_pmf(base_lambda_home, h)
            p_away = poisson_pmf(base_lambda_away, a)
            p_score = p_home * p_away
            
            score_probabilities.append(((h, a), p_score))

            if h > a:
                home_win_prob += p_score
            elif h == a:
                draw_prob += p_score
            else:
                away_win_prob += p_score

            if h > 0 and a > 0:
                btts_prob += p_score
            if (h + a) > 2.5:
                over_25_prob += p_score

    # Tri des scores par probabilité décroissante pour trouver les plus probables
    score_probabilities.sort(key=lambda x: x[1], reverse=True)
    top_score_1 = f"{score_probabilities[0][0][0]} - {score_probabilities[0][0][1]}"
    top_score_2 = f"{score_probabilities[1][0][0]} - {score_probabilities[1][0][1]}"

    # Conversion en pourcentages lisibles
    hw_pct = round(home_win_prob * 100, 1)
    dr_pct = round(draw_prob * 100, 1)
    aw_pct = round(away_win_prob * 100, 1)
    btts_pct = round(btts_prob * 100, 1)
    over_pct = round(over_25_prob * 100, 1)

    # Détermination d'une recommandation robuste basée sur le modèle
    if hw_pct >= 55:
        rec = f"Victoire de {home_name} ({hw_pct}% de probabilité)"
    elif aw_pct >= 50:
        rec = f"Gros potentiel extérieur : {away_name} ({aw_pct}%)"
    elif btts_pct >= 62:
        rec = f"Les deux équipes marquent (BTTS à {btts_pct}%)"
    elif over_pct >= 60:
        rec = f"Match ouvert : Plus de 2.5 buts ({over_pct}%)"
    else:
        rec = f"Rencontre équilibrée (Double chance ou Match Nul)"

    return {
        "goals_exp": round(base_lambda_home + base_lambda_away, 2),
        "corners_exp": 9.8,
        "shots_on_target_exp": round(8.0 + (base_lambda_home + base_lambda_away) * 1.5, 1),
        "scores": [top_score_1, top_score_2],
        "rec": rec,
        "probabilities": f"1: {hw_pct}% | X: {dr_pct}% | 2: {aw_pct}%"
    }

# ==========================================
# 4. FONCTION API
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
                    "home": {
                        "name": h_name,
                        "logo": teams["home"]["logo"],
                        "goals": h_g
                    },
                    "away": {
                        "name": a_name,
                        "logo": teams["away"]["logo"],
                        "goals": a_g
                    },
                    "stats": calculate_poisson_analysis(h_name, a_name, h_g, a_g, status_short)
                })
            return formatted_matches, None
        else:
            return None, f"Erreur HTTP {response.status_code} : Vérifie ta clé API."
    except Exception as e:
        return None, f"Erreur réseau : {e}"

# ==========================================
# 5. INTERFACE PRINCIPALE
# ==========================================
st.title("⚽ VIPSTEPH - Match Analyzer API")
st.markdown("Tableau de bord professionnel avec **Moteur de Probabilités de Poisson**.")

matches, error_message = fetch_real_api_data(api_key_input, mode_recherche, target_date, league_choice)

if api_key_input:
    if error_message:
        st.error(error_message)
    else:
        st.success("✅ Clé API valide et connectée avec succès !")
else:
    st.info("💡 Entre ta clé API dans la barre latérale pour récupérer les données en direct.")

if not matches:
    if api_key_input and not error_message:
        st.warning(f"ℹ️ Aucun match trouvé pour cette sélection/date via l'API. Voici un exemple avec calcul de Poisson :")
    
    matches = [
        {
            "id": "demo-1", "competition": "Premier League", "country": "England", "status": "1H", "time": "🔴 LIVE 42'",
            "home": {"name": "Arsenal", "logo": "https://media.api-sports.io/football/teams/42.png", "goals": 2},
            "away": {"name": "Manchester City", "logo": "https://media.api-sports.io/football/teams/50.png", "goals": 1},
            "stats": calculate_poisson_analysis("Arsenal", "Manchester City", 2, 1, "1H")
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

    with st.expander(f"📊 Analyse Poisson & Pronostics : {match['home']['name']} vs {match['away']['name']}"):
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
                    <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>PROBABILITÉS 1X2</div>
                    <div style='font-size: 12px; font-weight: bold;'>{match['stats']['probabilities']}</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class='stat-box'>
                    <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>SCORES PROBABLES</div>
                    <div style='font-size: 13px; font-weight: bold; color: #38bdf8;'>{match['stats']['scores'][0]} / {match['stats']['scores'][1]}</div>
                </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
                <div class='stat-box'>
                    <div style='color: #9ca3af; font-size: 11px; margin-bottom: 2px;'>TIRS CADRÉS (Est.)</div>
                    <div style='font-size: 15px; font-weight: bold;'>{match['stats']['shots_on_target_exp']}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="background-color: #070a0f; border-left: 3px solid #10b981; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 13px;">
                💡 <b>Pronostic Recommandé (Modèle Poisson) :</b> <span style="color: #10b981;">{match['stats']['rec']}</span>
            </div>
        """, unsafe_allow_html=True)
