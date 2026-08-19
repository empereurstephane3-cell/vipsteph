import concurrent.futures
import datetime
import json
import math
import os
import requests
import streamlit as st

st.set_page_config(
    page_title="VIP Steph - Prévisions Football", page_icon="⚽", layout="centered"
)

st.title("VIP Steph - Prévisions Football Avancées")

# --- PARAMÈTRES DU MATCH (Heure, Logos, Équipes) ---
match_time = "21:00"
home_team = "Équipe Domicile"
away_team = "Équipe Extérieur"
home_logo = "https://img.icons8.com/color/96/football--v1.png"
away_logo = "https://img.icons8.com/color/96/football--v1.png"

# Affichage de l'en-tête
col1, col2, col3 = st.columns([2, 1, 2])
with col1:
    st.image(home_logo, width=60)
    st.markdown(f"**{home_team}**")
with col2:
    st.markdown(f"### ⏰ {match_time}")
with col3:
    st.image(away_logo, width=60)
    st.markdown(f"**{away_team}**")

st.markdown("---")

# --- DONNÉES & PARAMÈTRES STATISTIQUES ---
# (Tu pourras ici utiliser 'os' pour récupérer ta clé API via os.getenv ou 'json' pour charger tes fichiers locaux)
league_avg = 1.35
h_data = {"home_gf": 15, "home_played": 10, "home_ga": 8}
a_data = {"away_gf": 10, "away_played": 10, "away_ga": 12}
PRIOR_WEIGHT = 5


def smooth(goals, games, league_avg):
    return (goals + PRIOR_WEIGHT * league_avg) / (games + PRIOR_WEIGHT)


smooth_home_gf = smooth(
    h_data["home_gf"], h_data["home_played"], league_avg
)
smooth_home_ga = smooth(
    h_data["home_ga"], h_data["home_played"], league_avg
)
smooth_away_gf = smooth(
    a_data["away_gf"], a_data["away_played"], league_avg
)
smooth_away_ga = smooth(
    a_data["away_ga"], a_data["away_played"], league_avg
)

home_att = smooth_home_gf / league_avg
home_def = smooth_home_ga / league_avg
away_att = smooth_away_gf / league_avg
away_def = smooth_away_ga / league_avg

home_adv = 1.20
lambda_home = home_att * away_def * league_avg * home_adv
lambda_away = away_att * home_def * league_avg / home_adv


def poisson(k, lam):
    return (math.pow(lam, k) * math.exp(-lam)) / math.factorial(k)


# --- 1. MATCH COMPLET (FT) ---
max_goals = 6
home_win = 0
draw = 0
away_win = 0
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

# --- RECOMMANDATION & INDICE DE CONFIANCE ---
max_prob = max(home_win, draw, away_win)
if max_prob == home_win:
    rec = "Victoire Domicile (1)"
elif max_prob == away_win:
    rec = "Victoire Extérieur (2)"
else:
    rec = "Match Nul (X)"

if max_prob >= 0.60:
    confiance = "🔥 ÉLEVÉE (Très favorable)"
elif max_prob >= 0.45:
    confiance = "⚡ MOYENNE (À surveiller)"
else:
    confiance = "⚠️ FAIBLE (Match très ouvert / Risqué)"

st.subheader("🎯 Recommandation VIP & Confiance")
st.success(f"**Pari conseillé :** {rec}")
st.info(f"**Indice de confiance :** {confiance} ({max_prob * 100:.1f}%)")

st.subheader("⚽ Match Complet (FT)")
st.write(f"Victoire domicile : {home_win * 100:.1f}%")
st.write(f"Match nul : {draw * 100:.1f}%")
st.write(f"Victoire extérieur : {away_win * 100:.1f}%")

st.markdown("**Top 5 Scores Exacts :**")
for item in scores_full[:5]:
    st.write(f"- Score {item['score']} : {item['prob'] * 100:.1f}%")


# --- 2. 1ÈRE MI-TEMPS (1H) ---
lam_h_1h = lambda_home / 2
lam_a_1h = lambda_away / 2
h1_win = 0
h1_draw = 0
h1_away_win = 0

for h in range(4):
    for a in range(4):
        p = poisson(h, lam_h_1h) * poisson(a, lam_a_1h)
        if h > a:
            h1_win += p
        elif h == a:
            h1_draw += p
        else:
            h1_away_win += p

st.subheader("⏱️ 1ère Mi-temps (1H)")
st.write(f"1H - Victoire domicile : {h1_win * 100:.1f}%")
st.write(f"1H - Match nul : {h1_draw * 100:.1f}%")
st.write(f"1H - Victoire extérieur : {h1_away_win * 100:.1f}%")


# --- 3. 2ÈME MI-TEMPS (2H) ---
lam_h_2h = lambda_home / 2
lam_a_2h = lambda_away / 2
h2_win = 0
h2_draw = 0
h2_away_win = 0

for h in range(4):
    for a in range(4):
        p = poisson(h, lam_h_2h) * poisson(a, lam_a_2h)
        if h > a:
            h2_win += p
        elif h == a:
            h2_draw += p
        else:
            h2_away_win += p

st.subheader("⏱️ 2ème Mi-temps (2H)")
st.write(f"2H - Victoire domicile : {h2_win * 100:.1f}%")
st.write(f"2H - Match nul : {h2_draw * 100:.1f}%")
st.write(f"2H - Victoire extérieur : {h2_away_win * 100:.1f}%")


# --- 4. STATISTIQUES & TENDANCES (xG & Corners) ---
total_expected_goals = lambda_home + lambda_away
league_avg_corners = 9.5
corners_home = (home_att * away_def) * (league_avg_corners / 2)
corners_away = (away_att * home_def) * (league_avg_corners / 2)
total_corners = corners_home + corners_away

st.subheader("📊 Statistiques & Tendances Attendues")
st.write(f"Buts attendus Domicile (xG) : {lambda_home:.2f}")
st.write(f"Buts attendus Extérieur (xG) : {lambda_away:.2f}")
st.write(f"Total buts attendus : {total_expected_goals:.2f}")
st.write(f"Corners attendus (Domicile) : {corners_home:.1f}")
st.write(f"Corners attendus (Extérieur) : {corners_away:.1f}")
st.write(f"Total corners attendus : {total_corners:.1f}")
