import datetime
import math
import requests
import streamlit as st

st.set_page_config(
    page_title="VIP Steph - Prévisions Football", page_icon="⚽", layout="centered"
)

st.title("VIP Steph - Prévisions Football en Direct ⚽")

# --- CONFIGURATION API-FOOTBALL ---
# --- CONFIGURATION API-FOOTBALL ---
# --- CONFIGURATION API-FOOTBALL (DIRECT) ---
try:
    API_KEY = st.secrets["65ad65cff78e2148482946179f1a89300f749a0ae3b6d8db848ffbc41901dc4e"]
    st.sidebar.success("🔑 Clé secrète détectée !")
except:
    API_KEY = "65ad65cff78e2148482946179f1a89300f749a0ae3b6d8db848ffbc41901dc4e"
    st.sidebar.warning("⚠️ Clé non trouvée")

# URL et Header officiels d'API-Sports
URL_API = "https://v3.football.api-sports.io/fixtures"
HEADERS = {
    "x-apisports-key": API_KEY,
}

# Date du jour dynamique
today_str = datetime.date.today().strftime("%Y-%m-%d")

st.sidebar.header("📅 Sélection des Matchs")
selected_date = st.sidebar.date_input("Date des matchs", datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")

# Fonction pour récupérer les matchs du jour via l'API
@st.cache_data(ttl=300)
@st.cache_data(ttl=300)
def get_fixtures(date_target):
    url = f"{URL_API}?date={date_target}"
    try:
        response = requests.get(url, headers=HEADERS)
        st.sidebar.write(f"API Status: {response.status_code}")
        if response.status_code == 200:
            return response.json().get("response", [])
        else:
            st.sidebar.error(f"Erreur API : {response.status_code}")
            return []
    except Exception as e:
        st.sidebar.error(f"Erreur : {e}")
        return []


# Simulation ou chargement des matchs
fixtures = get_fixtures(date_str)

if not fixtures and API_KEY == "65ad65cff78e2148482946179f1a89300f749a0ae3b6d8db848ffbc41901dc4e":
    st.warning(
        "⚠️ Pense à insérer ta clé API-Football dans le code pour récupérer"
        " les vrais matchs en direct !"
    )
    # Données fictives de secours pour tester l'affichage si pas de clé
    fixtures = [
        {
            "fixture": {
                "id": 101,
                "date": "2026-06-06T20:00:00+00:00",
                "status": {"short": "LIVE", "elapsed": 64},
            },
            "teams": {
                "home": {
                    "name": "Real Madrid",
                    "logo": "https://media.api-sports.io/football/teams/541.png",
                },
                "away": {
                    "name": "FC Barcelone",
                    "logo": "https://media.api-sports.io/football/teams/529.png",
                },
            },
            "goals": {"home": 2, "away": 1},
        },
        {
            "fixture": {
                "id": 102,
                "date": "2026-06-06T21:00:00+00:00",
                "status": {"short": "NS", "elapsed": None},
            },
            "teams": {
                "home": {
                    "name": "Manchester City",
                    "logo": "https://media.api-sports.io/football/teams/50.png",
                },
                "away": {
                    "name": "Arsenal",
                    "logo": "https://media.api-sports.io/football/teams/42.png",
                },
            },
            "goals": {"home": None, "away": None},
        },
    ]

# --- AFFICHAGE DE LA LISTE DES MATCHS ---
match_options = {}
for f in fixtures:
    h_name = f["teams"]["home"]["name"]
    a_name = f["teams"]["away"]["name"]
    status = f["fixture"]["status"]["short"]
    elapsed = f["fixture"]["status"]["elapsed"]

    # Formatage du statut pour l'affichage
    if status == "LIVE":
        status_label = f"🔴 EN DIRECT ({elapsed}')"
    elif status in ["FT", "AET", "PEN"]:
        status_label = "✅ TERMINÉ"
    else:
        status_label = "⏰ À VENIR"

    label = f"{h_name} vs {a_name} [{status_label}]"
    match_options[label] = f

selected_match_label = st.sidebar.selectbox(
    "Choisis un match à analyser", list(match_options.keys())
)

if selected_match_label:
    match_data = match_options[selected_match_label]

    home_team = match_data["teams"]["home"]["name"]
    away_team = match_data["teams"]["away"]["name"]
    home_logo = match_data["teams"]["home"]["logo"]
    away_logo = match_data["teams"]["away"]["logo"]
    status_short = match_data["fixture"]["status"]["short"]
    elapsed = match_data["fixture"]["status"]["elapsed"]
    live_goals_h = match_data["goals"]["home"]
    live_goals_a = match_data["goals"]["away"]

    # En-tête du match sélectionné
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.image(home_logo, width=60)
        st.markdown(f"**{home_team}**")
        if live_goals_h is not None:
            st.markdown(f"### Score : {live_goals_h}")
    with col2:
        if status_short == "LIVE":
            st.markdown(f"### 🔴 {elapsed}'")
        elif status_short in ["FT", "AET"]:
            st.markdown("### ✅ FT")
        else:
            st.markdown("### ⏰ 21:00")
    with col3:
        st.image(away_logo, width=60)
        st.markdown(f"**{away_team}**")
        if live_goals_a is not None:
            st.markdown(f"### Score : {live_goals_a}")

    st.markdown("---")

    # --- CALCULS STATISTIQUES (Poisson) ---
    league_avg = 1.35
    h_stats = {"home_gf": 16, "home_played": 10, "home_ga": 8}
    a_stats = {"away_gf": 12, "away_played": 10, "away_ga": 11}
    PRIOR_WEIGHT = 5


    def smooth(goals, games, league_avg):
        return (goals + PRIOR_WEIGHT * league_avg) / (games + PRIOR_WEIGHT)


    h_att = smooth(h_stats["home_gf"], h_stats["home_played"], league_avg) / league_avg
    h_def = smooth(h_stats["home_ga"], h_stats["home_played"], league_avg) / league_avg
    a_att = smooth(a_stats["away_gf"], a_stats["away_played"], league_avg) / league_avg
    a_def = smooth(a_stats["away_ga"], a_stats["away_played"], league_avg) / league_avg

    home_adv = 1.20
    lambda_home = h_att * a_def * league_avg * home_adv
    lambda_away = a_att * h_def * league_avg / home_adv


    def poisson(k, lam):
        return (math.pow(lam, k) * math.exp(-lam)) / math.factorial(k)


    # Match complet
    max_goals = 6
    home_win, draw, away_win = 0, 0, 0
    scores_full = []

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson(h, lambda_home) * poisson(a, lambda_away)
            scores_full.append({"score": f"{h}-{a}", "prob": p})
            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p

    scores_full = sorted(scores_full, key=lambda x: x["prob"], reverse=True)

    # Recommandation & Confiance
    max_prob = max(home_win, draw, away_win)
    if max_prob == home_win:
        rec = f"Victoire {home_team} (1)"
    elif max_prob == away_win:
        rec = f"Victoire {away_team} (2)"
    else:
        rec = "Match Nul (X)"

    if max_prob >= 0.60:
        confiance = "🔥 ÉLEVÉE"
    elif max_prob >= 0.45:
        confiance = "⚡ MOYENNE"
    else:
        confiance = "⚠️ FAIBLE / RISQUÉ"

    st.subheader("🎯 Recommandation VIP & Confiance")
    st.success(f"**Pari conseillé :** {rec}")
    st.info(f"**Indice de confiance :** {confiance} ({max_prob * 100:.1f}%)")

    st.subheader("⚽ Probabilités du Match (FT)")
    st.write(f"Victoire {home_team} : {home_win * 100:.1f}%")
    st.write(f"Match nul : {draw * 100:.1f}%")
    st.write(f"Victoire {away_team} : {away_win * 100:.1f}%")

    st.markdown("**Top 3 Scores Exacts :**")
    for item in scores_full[:3]:
        st.write(f"- Score {item['score']} : {item['prob'] * 100:.1f}%")
