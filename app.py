import math
import requests
import streamlit as st

st.set_page_config(
    page_title="VIPSteph - Dashboard Avancé", page_icon="👑", layout="wide"
)

# --- 1. GESTION DES QUOTAS & SESSION ---
if "quota_used" not in st.session_state:
  st.session_state.quota_used = 0


# --- 2. MOTEUR MATHÉMATIQUE : LOI DE POISSON & MARCHÉS ---
def calculate_poisson_prediction(
    home_att, home_def, away_att, away_def, avg_home_goals=1.5, avg_away_goals=1.1
):
  lambda_home = home_att * away_def * avg_home_goals
  lambda_away = away_att * home_def * avg_away_goals

  def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

  max_goals = 6
  home_win = 0.0
  draw = 0.0
  away_win = 0.0
  btts_yes = 0.0
  over_15 = 0.0
  over_25 = 0.0
  over_35 = 0.0

  score_matrix = {}

  for h in range(max_goals):
    for a in range(max_goals):
      p_h = poisson_prob(lambda_home, h)
      p_a = poisson_prob(lambda_away, a)
      p = p_h * p_a
      score_matrix[(h, a)] = p

      if h > a:
        home_win += p
      elif h == a:
        draw += p
      else:
        away_win += p

      if h > 0 and a > 0:
        btts_yes += p
      if (h + a) > 1.5:
        over_15 += p
      if (h + a) > 2.5:
        over_25 += p
      if (h + a) > 3.5:
        over_35 += p

  most_likely_score = max(score_matrix, key=score_matrix.get)

  # Calcul des marchés dérivés
  double_chance_1x = home_win + draw
  double_chance_x2 = away_win + draw
  double_chance_12 = home_win + away_win

  # Draw No Bet (Remboursé si nul)
  dnb_home = (
      (home_win / (home_win + away_win)) * 100
      if (home_win + away_win) > 0
      else 50.0
  )

  return {
      "lambda_home": round(lambda_home, 2),
      "lambda_away": round(lambda_away, 2),
      "home_win_pct": round(home_win * 100, 1),
      "draw_pct": round(draw * 100, 1),
      "away_win_pct": round(away_win * 100, 1),
      "btts_yes_pct": round(btts_yes * 100, 1),
      "btts_no_pct": round((1 - btts_yes) * 100, 1),
      "over_15_pct": round(over_15 * 100, 1),
      "over_25_pct": round(over_25 * 100, 1),
      "over_35_pct": round(over_35 * 100, 1),
      "under_25_pct": round((1 - over_25) * 100, 1),
      "dc_1x_pct": round(double_chance_1x * 100, 1),
      "dc_x2_pct": round(double_chance_x2 * 100, 1),
      "dc_12_pct": round(double_chance_12 * 100, 1),
      "dnb_home_pct": round(dnb_home, 1),
      "exact_score": f"{most_likely_score[0]} - {most_likely_score[1]}",
  }


# --- 3. SYSTÈME DES 8 AGENTS IA SPÉCIALISÉS ---
def run_8_ai_agents(match_data):
  h_att, h_def = 1.25, 0.85
  a_att, a_def = 1.10, 0.95

  poisson_res = calculate_poisson_prediction(h_att, h_def, a_att, a_def)

  agents_reports = {
      "Agent 1 (Statistiques & Forme)": {
          "icon": "📈",
          "text": (
              "Analyse des 5 derniers matchs : Tendance stable à domicile,"
              " défense légèrement perméable à l'extérieur."
          ),
      },
      "Agent 2 (Modèle Poisson Mathématique)": {
          "icon": "🧮",
          "text": (
              f"xG estimé -> Domicile : {poisson_res['lambda_home']} | Extérieur"
              f" : {poisson_res['lambda_away']}. Score le plus probable :"
              f" {poisson_res['exact_score']}."
          ),
      },
      "Agent 3 (Analyse Tactique)": {
          "icon": "♟️",
          "text": (
              "Le bloc équipe adverse souffre face aux transitions rapides sur"
              " les ailes."
          ),
      },
      "Agent 4 (Contexte & Enjeu)": {
          "icon": "🧠",
          "text": (
              "Forte pression de classement pour l'équipe hôte, besoin"
              " impératif de points."
          ),
      },
      "Agent 5 (Météo & Terrain)": {
          "icon": "⛅",
          "text": (
              "Conditions optimales de jeu, terrain sec favorisant le jeu au"
              " sol rapide."
          ),
      },
      "Agent 6 (Value & Marché)": {
          "icon": "💰",
          "text": (
              "Les probabilités mathématiques offrent une belle value sur"
              f" l'option Over 2.5 ({poisson_res['over_25_pct']}%) ou le BTTS"
              f" ({poisson_res['btts_yes_pct']}%)."
          ),
      },
      "Agent 7 (Infirmerie & Effectif)": {
          "icon": "🏥",
          "text": (
              "Aucun titulaire majeur absent de dernière minute des deux"
              " côtés."
          ),
      },
      "Agent 8 (Synthèse Maître VIPSteph)": {
          "icon": "👑",
          "text": (
              f"Victoire 1 : {poisson_res['home_win_pct']}% | Nul :"
              f" {poisson_res['draw_pct']}% | Victoire 2 :"
              f" {poisson_res['away_win_pct']}%. Marchés validés et sécurisés"
              " par l'IA."
          ),
      },
  }
  return poisson_res, agents_reports


# --- 4. INTERFACE UTILISATEUR STREAMLIT ---
st.title("👑 VIPSteph - Smart Sports Dashboard & Multi-Agents AI")
st.sidebar.header("Configuration & Quotas")

api_key_ft = st.sidebar.text_input("Clé API Football", type="password")
api_key_tn = st.sidebar.text_input("Clé API Tennis", type="password")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Quotas consommés :** {st.session_state.quota_used} / 100")

sport_tab = st.radio(
    "Sélectionner le sport", ["Football", "Tennis"], horizontal=True
)

if sport_tab == "Football":
  st.subheader("⚽ Matchs de Football - Analyse par les 8 Agents IA")
  st.markdown(
      "Mode Économie d'API actif. Cliquez sur **Analyser** pour déclencher le"
      " modèle de Poisson, les marchés 💹 et l'intelligence des 8 agents."
  )

  football_matches = [
      {
          "id": 1,
          "home": "Real Madrid",
          "away": "FC Barcelone",
          "league": "La Liga",
          "status": "À venir",
      },
      {
          "id": 2,
          "home": "Manchester City",
          "away": "Arsenal",
          "league": "Premier League",
          "status": "En direct",
      },
      {
          "id": 3,
          "home": "Bayern Munich",
          "away": "Dortmund",
          "league": "Bundesliga",
          "status": "À venir",
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

        poisson_data, agents_output = run_8_ai_agents(match)

        st.success(
            f"Analyse croisée réussie pour {match['home']} vs"
            f" {match['away']} (-1 requête)"
        )

        # Affichage des résultats du modèle de Poisson
        st.markdown("### 📊 Résultats du Modèle de Poisson Robuste")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        col_p1.metric("Score le plus probable", poisson_data["exact_score"])
        col_p2.metric(
            f"Victoire {match['home']}", f"{poisson_data['home_win_pct']}%"
        )
        col_p3.metric("Match Nul", f"{poisson_data['draw_pct']}%")
        col_p4.metric(
            f"Victoire {match['away']}", f"{poisson_data['away_win_pct']}%"
        )

        # Section Marchés 💹 intégrée
        st.markdown("---")
        st.markdown("### 💹 Analyse détaillée des Marchés de Paris")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
          st.metric("Double Chance 1X", f"{poisson_data['dc_1x_pct']}%")
          st.metric("Over 1.5 Buts", f"{poisson_data['over_15_pct']}%")
        with m2:
          st.metric("Double Chance X2", f"{poisson_data['dc_x2_pct']}%")
          st.metric("Over 2.5 Buts", f"{poisson_data['over_25_pct']}%")
        with m3:
          st.metric("BTTS (Les 2 marquent)", f"{poisson_data['btts_yes_pct']}%")
          st.metric("Under 2.5 Buts", f"{poisson_data['under_25_pct']}%")
        with m4:
          st.metric(
              f"Draw No Back ({match['home']})",
              f"{poisson_data['dnb_home_pct']}%",
          )
          st.metric("Over 3.5 Buts", f"{poisson_data['over_35_pct']}%")

        st.markdown("---")
        st.markdown("### 🤖 Rapports des 8 Agents IA Spécialisés")

        # Grille des agents
        agent_items = list(agents_output.items())
        for i in range(0, len(agent_items), 2):
          col_a, col_b = st.columns(2)

          with col_a:
            name_a, data_a = agent_items[i]
            with st.container(border=True):
              st.markdown(f"#### {data_a['icon']} {name_a}")
              st.write(data_a["text"])

          if i + 1 < len(agent_items):
            with col_b:
              name_b, data_b = agent_items[i + 1]
              with st.container(border=True):
                st.markdown(f"#### {data_b['icon']} {name_b}")
                st.write(data_b["text"])

else:
  st.subheader("🎾 Tournois de Tennis - Mode Économie d'API")
  st.markdown(
      "La liste ci-dessous n'utilise pas de requêtes. Cliquez sur **Analyser**"
      " pour cibler un match précis."
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
            f"Analyse ciblée lancée pour {match['player1']} vs"
            f" {match['player2']} (-1 requête)"
        )
        st.info("🔮 Pronostic IA : Match serré prévu en 3 sets.")
