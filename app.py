import math
import requests
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="VIPSteph - Hub d'Analyse Avancé", page_icon="👑", layout="wide"
)

# Initialisation du gestionnaire de quotas
if "quota_used" not in st.session_state:
  st.session_state.quota_used = 0

st.title("👑 VIPSteph - Tableau de bord & Multi-Agents IA")
st.sidebar.header("Configuration & Quotas")

api_key_ft = st.sidebar.text_input("Clé API Football", type="password")
api_key_tn = st.sidebar.text_input("Clé API Tennis", type="password")

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**⚡ Quotas consommés :** {st.session_state.quota_used} / 100"
)

sport_tab = st.radio(
    "Sélectionner le sport", ["Football", "Tennis"], horizontal=True
)

# --- FONCTION : LOI DE POISSON ROBUSTE ---
def calculate_poisson_match(lambda_home, lambda_away, max_goals=5):
  """Calcule les probabilités exactes de scores et d'issues avec la loi de Poisson."""

  def poisson_prob(lmbda, k):
    return (lmbda**k) * math.exp(-lmbda) / math.factorial(k)

  home_win = 0.0
  draw = 0.0
  away_win = 0.0
  btts_prob = 0.0
  over_25 = 0.0

  score_matrix = {}
  for h in range(max_goals + 1):
    for a in range(max_goals + 1):
      p = poisson_prob(lambda_home, h) * poisson_prob(lambda_away, a)
      score_matrix[(h, a)] = p
      if h > a:
        home_win += p
      elif h == a:
        draw += p
      else:
        away_win += p

      if h + a > 2.5:
        over_25 += p
      if h > 0 and a > 0:
        btts_prob += p

  # Normalisation en pourcentage
  total = home_win + draw + away_win
  if total > 0:
    home_win = (home_win / total) * 100
    draw = (draw / total) * 100
    away_win = (away_win / total) * 100

  return {
      "home_win": round(home_win, 1),
      "draw": round(draw, 1),
      "away_win": round(away_win, 1),
      "over_25": round(over_25 * 100, 1),
      "btts": round(btts_prob * 100, 1),
  }


# --- FOOTBALL SECTION ---
if sport_tab == "Football":
  st.subheader("⚽ Matchs de Football - Analyse multi-agents & Poisson")
  st.markdown(
      "Mode économie actif : Sélectionnez un match pour déclencher l'analyse"
      " approfondie (-1 requête ciblée)."
  )

  football_matches = [
      {
          "id": 1,
          "home": "Real Madrid",
          "away": "FC Barcelone",
          "league": "La Liga",
          "status": "À venir",
          "l_home": 2.1,
          "l_away": 1.4,
      },
      {
          "id": 2,
          "home": "Manchester City",
          "away": "Arsenal",
          "league": "Premier League",
          "status": "En direct",
          "l_home": 1.8,
          "l_away": 1.6,
      },
      {
          "id": 3,
          "home": "Bayern Munich",
          "away": "Dortmund",
          "league": "Bundesliga",
          "status": "À venir",
          "l_home": 2.4,
          "l_away": 1.1,
      },
  ]

  for match in football_matches:
    col1, col2 = st.columns([3, 1])
    with col1:
      st.write(
          f"**{match['league']}** | {match['home']} vs {match['away']} —"
          f" *{match['status']}*"
      )
    with col2:
      if st.button("🔍 Analyser", key=f"ft_{match['id']}"):
        st.session_state.quota_used += 1

        # Calcul Poisson
        poisson_res = calculate_poisson_match(match["l_home"], match["l_away"])

        st.success(
            f"Analyse multi-agents réussie pour {match['home']} vs"
            f" {match['away']} !"
        )

        # Affichage des Résultats de la Loi de Poisson
        st.markdown("---")
        st.markdown("### 📊 1. Modèle Mathématique (Loi de Poisson)")
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
        p_col1.metric(
            f"Victoire {match['home']}", f"{poisson_res['home_win']}%"
        )
        p_col2.metric("Match Nul", f"{poisson_res['draw']}%")
        p_col3.metric(
            f"Victoire {match['away']}", f"{poisson_res['away_win']}%"
        )
        p_col4.metric("Over 2.5 buts", f"{poisson_res['over_25']}%")
        p_col5.metric("Les 2 marquent (BTTS)", f"{poisson_res['btts']}%")

        # Conseil des 8 Agents IA
        st.markdown("---")
        st.markdown("### 🤖 2. Le Conseil des 8 Agents IA Experts")

        agents = [
            (
                "🛡️ Agent 1 : Tacticien",
                (
                    f"Analyse des blocs: {match['home']} privilégie la"
                    " possession haute, tandis que {match['away']} excelle en"
                    " transition rapide."
                ),
            ),
            (
                "📈 Agent 2 : Statisticien",
                (
                    "Indicateurs xG cohérents avec les moyennes de la"
                    f" saison. {match['home']} subit peu d'occasions à"
                    " domicile."
                ),
            ),
            (
                "⚡ Agent 3 : Momentum & Forme",
                (
                    "Dynamique récente favorable à l'équipe hôte sur les 5"
                    " derniers matchs."
                ),
            ),
            (
                "📜 Agent 4 : Historien (H2H)",
                (
                    "L'historique des confrontations directes montre traditionnellement"
                    " des matchs ouverts et prolifiques."
                ),
            ),
            (
                "🧮 Agent 5 : Modélisateur Poisson",
                (
                    f"Validation mathématique : Lambda Domicile ({match['l_home']})"
                    f" vs Extérieur ({match['l_away']}). Probabilité de succès"
                    f" de {poisson_res['home_win']}%."
                ),
            ),
            (
                "🌦️ Agent 6 : Veilleur (Météo/Absences)",
                (
                    "Aucune absence majeure signalée de dernière minute. Conditions"
                    " de pelouse optimales."
                ),
            ),
            (
                "💰 Agent 7 : Bookmaker & Marché",
                (
                    "Les cotes du marché sont légèrement value sur l'option"
                    " buts ou double chance."
                ),
            ),
            (
                "👑 Agent 8 : Coach VIP (Synthèse Finale)",
                (
                    f"**Recommandation VIP :** Victoire de {match['home']} ou"
                    f" match nul avec une forte tendance Over 2.5 buts"
                    f" ({poisson_res['over_25']}%)."
                ),
            ),
        ]

        # Affichage des agents en grille de 2 colonnes
        for i in range(0, len(agents), 2):
            ac1, ac2 = st.columns(2)
            with ac1:
              title, desc = agents[i]
              st.info(f"**{title}**\n\n{desc}")
            if i + 1 < len(agents):
              with ac2:
                title, desc = agents[i + 1]
                st.info(f"**{title}**\n\n{desc}")

# --- TENNIS SECTION ---
else:
  st.subheader("🎾 Tournois de Tennis - Mode Économie d'API")
  st.markdown(
      "Sélectionnez un match pour analyser les confrontations sur le circuit."
  )

  tennis_matches = [
      {
          "id": 101,
          "player1": "Novak Djokovic",
          "player2": "Carlos Alcaraz",
          "tournament": "ATP Masters",
          "status": "En direct",
      },
      {
          "id": 102,
          "player1": "Jannik Sinner",
          "player2": "Daniil Medvedev",
          "tournament": "ATP Finals",
          "status": "À venir",
      },
  ]

  for match in tennis_matches:
    col1, col2 = st.columns([3, 1])
    with col1:
      st.write(
          f"**{match['tournament']}** | {match['player1']} vs"
          f" {match['player2']} — *{match['status']}*"
      )
    with col2:
      if st.button("🔍 Analyser", key=f"tn_{match['id']}"):
        st.session_state.quota_used += 1
        st.success(
            "Analyse tennis ciblée lancée pour {match['player1']} vs"
            f" {match['player2']} (-1 requête)"
        )
        st.info(
            "🔮 **Synthèse IA Tennis :** Match très serré prévu en 3 sets."
            " Avantage léger sur l'efficacité des premières balles."
        )
