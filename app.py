from datetime import datetime
import math
import requests
import streamlit as st

st.set_page_config(
    page_title="VIPSteph - Kim Prono Pro", page_icon="👑", layout="centered"
)

# --- STYLE CSS PERSONNALISÉ ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f6f5;
    }
    .match-card {
        background-color: white;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .rec-box {
        background-color: #f1f8f5;
        border: 1px solid #c8e6c9;
        padding: 14px;
        border-radius: 10px;
        margin: 12px 0;
    }
    .score-box {
        background-color: #ffffff;
        border: 2px solid #ffca28;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .detail-box {
        background-color: #ffffff;
        border-left: 4px solid #2e7d32;
        padding: 12px 15px;
        border-radius: 6px;
        font-size: 13px;
        color: #333;
        margin-top: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "quota_used" not in st.session_state:
  st.session_state.quota_used = 0

st.title("👑 VIPSteph - Pronos Avancés")

# --- BARRE LATÉRALE : CONFIGURATION & FILTRES GRATUITS ---
st.sidebar.header("⚙️ Configuration & Filtres")
api_key_ft = st.sidebar.text_input(
    "Clé API (apiv3.apifootball.com)", type="password"
)

# Restriction volontaire aux championnats du plan gratuit pour éviter l'Erreur 400
free_leagues = {
    "Angleterre (Premier League / Général)": None,
    "Ligue 2 Française": "100",  # ID indicatif ou filtrage par texte
}

selected_league_choice = st.sidebar.selectbox(
    "Championnat (Plan Gratuit)",
    [
        "Angleterre (Premier League)",
        "France (Ligue 2)",
        "Mode Démo (Matchs types)",
    ],
)

selected_date = st.sidebar.date_input("Date des matchs", datetime.today())
date_str = selected_date.strftime("%Y-%m-%d")

st.sidebar.markdown(f"**Appels effectués :** {st.session_state.quota_used}")


# --- MOTEUR DE CALCUL POISSON ---
def calculate_poisson_prediction(
    home_att, home_def, away_att, away_def, avg_home_goals=1.65, avg_away_goals=1.25
):
  lambda_home = home_att * away_def * avg_home_goals
  lambda_away = away_att * home_def * avg_away_goals

  def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

  max_goals = 6
  home_win, draw, away_win, btts_yes, over_25 = 0.0, 0.0, 0.0, 0.0, 0.0
  score_matrix = {}

  for h in range(max_goals):
    for a in range(max_goals):
      p = poisson_prob(lambda_home, h) * poisson_prob(lambda_away, a)
      score_matrix[(h, a)] = p
      if h > a:
        home_win += p
      elif h == a:
        draw += p
      else:
        away_win += p
      if h > 0 and a > 0:
        btts_yes += p
      if (h + a) > 2.5:
        over_25 += p

  sorted_scores = sorted(score_matrix.items(), key=lambda x: x[1], reverse=True)
  top_scores = []
  for score_tuple, prob in sorted_scores[:3]:
    estimated_odds = round(1 / prob, 2) if prob > 0 else 99.0
    top_scores.append({
        "score": f"{score_tuple[0]} - {score_tuple[1]}",
        "prob": round(prob * 100, 1),
        "odds": estimated_odds,
    })

  return {
      "top_scores": top_scores,
      "home_win_pct": round(home_win * 100, 1),
      "draw_pct": round(draw * 100, 1),
      "away_win_pct": round(away_win * 100, 1),
      "dc_1x_pct": round((home_win + draw) * 100, 1),
      "btts_yes_pct": round(btts_yes * 100, 1),
      "over_25_pct": round(over_25 * 100, 1),
  }


# --- RÉCUPÉRATION SÉCURISÉE DES MATCHS ---
def fetch_fixtures(api_key, date_s):
  if not api_key:
    return [], "Veuillez entrer votre clé API."

  url = f"https://apiv3.apifootball.com/?action=get_fixtures&from={date_s}&to={date_s}&APIkey={api_key}"
  try:
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
      data = res.json()
      if isinstance(data, dict) and "error" in data:
        return [], data["error"]
      if isinstance(data, list):
        matches = []
        for item in data:
          # Filtrage textuel simple pour s'assurer de ne garder que l'Angleterre ou la Ligue 2 si besoin
          league_name = item.get("league_name", "").lower()
          if (
              selected_league_choice.startswith("Angleterre")
              and "england" not in league_name
              and "premier league" not in league_name
          ):
            continue
          if (
              selected_league_choice.startswith("France")
              and "ligue 2" not in league_name
          ):
            continue

          h_goals = item.get("match_hometeam_score")
          a_goals = item.get("match_awayteam_score")
          score_str = (
              f"{h_goals} - {a_goals}"
              if h_goals is not None
              and a_goals is not None
              and h_goals != ""
              and a_goals != ""
              else "0 - 0"
          )

          matches.append({
              "id": item.get("match_id", 0),
              "home": item.get("match_hometeam_name", "Domicile"),
              "away": item.get("match_awayteam_name", "Extérieur"),
              "home_logo": item.get(
                  "team_home_badge",
                  "https://apiv3.apifootball.com/badges/logo_country/default.png",
              ),
              "away_logo": item.get(
                  "team_away_badge",
                  "https://apiv3.apifootball.com/badges/logo_country/default.png",
              ),
              "league": item.get("league_name", "Championnat").upper(),
              "status": item.get("match_status", "NS"),
              "score_str": score_str,
          })
        return matches, None
    return [], f"Erreur HTTP {res.status_code}"
  except Exception as e:
    return [], str(e)


matches = []
api_error = None

if selected_league_choice != "Mode Démo (Matchs types)":
  matches, api_error = fetch_fixtures(api_key_ft, date_str)

if api_error:
  st.warning(f"Note API : {api_error}")

# Fallback si aucun match trouvé ou mode démo activé
if not matches:
  st.info(
      "Affichage des exemples de démonstration compatibles (Angleterre /"
      " Espagne) :"
  )
  matches = [
      {
          "id": 501,
          "home": "Arsenal",
          "away": "Manchester City",
          "home_logo": "https://apiv3.apifootball.com/badges/8643_arsenal.png",
          "away_logo": (
              "https://apiv3.apifootball.com/badges/8645_manchester-city.png"
          ),
          "league": "PREMIER LEAGUE",
          "status": "NS",
          "score_str": "0 - 0",
      }
  ]

# --- AFFICHAGE ---
st.subheader(
    f"📅 Matchs du {selected_date.strftime('%d/%m/%Y')} —"
    f" {selected_league_choice}"
)

for match in matches:
  with st.container():
    st.markdown(
        f"""
        <div class="match-card">
            <div style="font-size: 11px; font-weight: bold; color: #555; margin-bottom: 8px;">
                {match['league']} &nbsp;•&nbsp; <span style="color: #2e7d32;">✓ {match['status']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 12px 0;">
                <div style="text-align: center; flex: 1;">
                    <img src="{match['home_logo']}" width="38" style="vertical-align: middle; margin-bottom: 4px;"><br>
                    <b style="font-size: 14px; color: #111;">{match['home']}</b>
                </div>
                <div style="text-align: center; padding: 0 10px;">
                    <span style="color: #d32f2f; background: #ffebee; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 16px;">{match['score_str']}</span>
                </div>
                <div style="text-align: center; flex: 1;">
                    <img src="{match['away_logo']}" width="38" style="vertical-align: middle; margin-bottom: 4px;"><br>
                    <b style="font-size: 14px; color: #111;">{match['away']}</b>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        f"🌿 ANALYSER CE MATCH ({match['home']} vs {match['away']})",
        key=f"btn_{match['id']}",
    ):
      st.session_state.quota_used += 1
      res = calculate_poisson_prediction(1.3, 0.85, 1.15, 0.90)

      st.markdown(
          f"""
            <div class="rec-box">
                <div style="font-size: 10px; font-weight: bold; color: #2e7d32; text-transform: uppercase;">Position recommandée • 90 min</div>
                <div style="font-size: 15px; font-weight: bold; color: #111; margin-top: 3px;">{match['home']} ou nul (1X)</div>
                <div style="font-size: 12px; color: #555; margin-top: 2px;">Double chance • Confiance {res['dc_1x_pct']}% • Over 2.5 ({res['over_25_pct']}%)</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

      col_s1, col_s2, col_s3 = st.columns(3)
      for idx, col in enumerate([col_s1, col_s2, col_s3]):
        s = res["top_scores"][idx]
        with col:
          st.markdown(
              f"""
                    <div class="score-box">
                        <div style="font-size: 16px; font-weight: bold; color: #111;">{s['score']}</div>
                        <div style="font-size: 11px; color: #555;">{s['prob']}% • cote {s['odds']}</div>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

      st.markdown(
          f"""
            <div class="detail-box">
                <b>ANALYSE COMPLÈTE</b>
                <ul style="margin: 6px 0 0 -15px; padding-left: 20px; line-height: 1.4;">
                    <li><b>Domicile :</b> {res['home_win_pct']}% | <b>Nul :</b> {res['draw_pct']}% | <b>Extérieur :</b> {res['away_win_pct']}%</li>
                    <li>Marché BTTS (Les deux marquent) : {res['btts_yes_pct']}%</li>
                </ul>
            </div>
            """,
          unsafe_allow_html=True,
      )
    st.markdown("---")
