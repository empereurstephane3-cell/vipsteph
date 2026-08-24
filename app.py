import streamlit as st
from datetime import datetime

# Configuration de la page Streamlit
st.set_page_config(page_title="VIPSTEPH - Match Analyzer", layout="wide")

st.title("⚽ VIPSTEPH - Analyseur & Prédictions")
st.write("Tableau de bord des statistiques et des scores probables.")

# ==========================================
# MOTEUR DE PRÉDICTION & LOGIQUE
# ==========================================
def prediction_engine(match):
    statistics = match.get("statistics", {})
    home_stats = statistics.get("home", {})
    away_stats = statistics.get("away", {})
    
    home_avg = home_stats.get("goalsForAvg", 1.5)
    away_avg = away_stats.get("goalsForAvg", 1.2)

    mt_home = round(home_avg * 0.45, 1)
    mt_away = round(away_avg * 0.45, 1)
    mt1_score = f"{round(mt_home)} - {round(mt_away)}"

    final_home = round(home_avg)
    final_away = round(away_avg)
    final_score = f"{final_home} - {final_away}"

    return {
        "mt1": {"probable_score": mt1_score, "probability": "42%"},
        "mt2": {"probable_score": "1 - 1", "probability": "38%"},
        "final": {"probable_score": final_score, "confidence": "Élevée"}
    }

def get_demo_matches():
    return [
        {
            "id": "demo-1",
            "competition": "Premier League (Angleterre)",
            "home_team": {"name": "Arsenal"},
            "away_team": {"name": "Manchester City"},
            "statistics": {"home": {"goalsForAvg": 2.1}, "away": {"goalsForAvg": 2.4}}
        }
    ]

# ==========================================
# AFFICHAGE VISUEL DANS L'APPLICATION
# ==========================================
matches = get_demo_matches()

for match in matches:
    with st.container():
        st.subheader(f"📍 {match['competition']}")
        
        # Affichage du nom des équipes
        col_teams, col_btn = st.columns([3, 1])
        with col_teams:
            st.markdown(f"### **{match['home_team']['name']}** vs **{match['away_team']['name']}**")
        
        # Récupération des prédictions
        pred = prediction_engine(match)
        
        # Affichage visuel sous forme de colonnes (métriques Streamlit)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="⏱️ 1ère Mi-Temps (MT1)", value=pred["mt1"]["probable_score"], delta=pred["mt1"]["probability"])
        with c2:
            st.metric(label="⏱️ 2ème Mi-Temps (MT2)", value=pred["mt2"]["probable_score"], delta=pred["mt2"]["probability"])
        with c3:
            st.metric(label="🏆 Score Final Estimé", value=pred["final"]["probable_score"], delta=pred["final"]["confidence"])
        
        st.divider()
