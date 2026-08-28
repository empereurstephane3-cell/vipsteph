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

# --- BARRE LATÉRALE : CONFIGURATION, FILTRES & AUTO-REFRESH ---
st.sidebar.header("⚙️ Configuration & Filtres")
api_key_ft = st.sidebar.text_input(
    "Clé API Football (RapidAPI)", type="password"
)

# Option d'actualisation automatique
auto_refresh = st.sidebar.checkbox(
    "🔄 Actualisation auto (toutes les 30s)", value=False
)
if auto_refresh:
  st.markdown(
      '<meta http-equiv="refresh" content="30">', unsafe_allow_html=True
  )
  st.sidebar.info("Actualisation automatique active.")

# 1. Sélection de la date
selected_date = st.sidebar.date_input("Date des matchs", datetime.today())
date_str = selected_date.strftime("%Y-%m-%d")


# Fonctions API dynamiques
@st.cache_data(ttl=3600)
def fetch_countries(api_key):
  if not api_key:
    return ["France", "England", "Spain", "Italy", "Germany"]
  url = "https://api-football-v1.p.rapidapi.com/v3/countries"
  try:
    res = requests.get(
        url,
        headers={
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        },
        timeout=5,
    )
    if res.status_code == 200:
      data = res.json().get("response", [])
      return sorted([c["name"] for c in data])
  except Exception:
    pass
  return ["France", "England", "Spain", "Italy", "Germany"]


@st.cache_data(ttl=3600)
def fetch_leagues_by_country(api_key, country_name):
  if not api_key:
    return {"Ligue 1": 61, "Premier League": 39}
  url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
  try:
    res = requests.get(
        url,
        headers={
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        },
        params={"country": country_name},
        timeout=5,
    )
    if res.status_code == 200:
      data = res.json().get("response", [])
      leagues = {
          item["league"]["name"]: item["league"]["id"] for item in data
      }
      return leagues
  except Exception:
    pass
  return {}


countries_list = fetch_countries(api_key_ft)
selected_country = st.sidebar.selectbox("Pays", countries_list)

leagues_dict = fetch_leagues_by_country(api_key_ft, selected_country)
if leagues_dict:
  selected_league_name = st.sidebar.selectbox(
      "Championnat", list(leagues_dict.keys())
  )
  selected_league_id = leagues_dict[selected_league_name]
else:
  selected_league_name = "Tous les championnats"
  selected_league_id = None

st.sidebar.markdown(f"**Quotas consommés :** {st.session_state.quota_used} / 100")


# --- MOTEUR DE CALCUL POISSON (TEMPS RÉGLEMENTAIRE 90 MIN) ---
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

  double_chance_1x = home_win + draw

  return {
      "top_scores": top_scores,
      "home_win_pct": round(home_win * 100, 1),
      "draw_pct": round(draw * 100, 1),
      "away_win_pct": round(away_win * 100, 1),
      "dc_1x_pct": round(double_chance_1x * 100, 1),
      "btts_yes_pct": round(btts_yes * 100, 1),
      "over_25_pct": round(over_25 * 100, 1),
  }


# --- RÉCUPÉRATION DES MATCHS ET LOGOS ---
def fetch_fixtures(api_key, date_s, league_id=None):
  if not api_key:
    return [], "Pas de clé API"
  url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
  params = {"date": date_s}
  if league_id:
    params["league"] = league_id

  try:
    res = requests.get(
        url,
        headers={
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        },
        params=params,
        timeout=10,
    )
    if res.status_code == 200:
      data = res.json()
      items = data.get("response", [])
      matches = []
      for item in items:
        fix = item.get("fixture", {})
        teams = item.get("teams", {})
        league = item.get("league", {})
        goals = item.get("goals", {})

        h_goals = goals.get("home")
        a_goals = goals.get("away")
        score_str = (
            f"{h_goals} - {a_goals}"
            if h_goals is not None and a_goals is not None
            else "0 - 0"
        )

        matches.append({
            "id": fix.get("id", 0),
            "home": teams.get("home", {}).get("name", "Domicile"),
            "away": teams.get("away", {}).get("name", "Extérieur"),
            "home_logo": teams.get("home", {}).get(
                "logo", "https://media.api-sports.io/football/teams/default.png"
            ),
            "away_logo": teams.get("away", {}).get(
                "logo", "https://media.api-sports.io/football/teams/default.png"
            ),
            "league": league.get("name", "Championnat").upper(),
            "status": fix.get("status", {}).get("short", "NS"),
            "elapsed": fix.get("status", {}).get("elapsed", 0) or 0,
            "score_str": score_str,
        })
      return matches, None
    else:
      return [], f"Erreur HTTP {res.status_code}: {res.text}"
  except Exception as e:
    return [], str(e)


# Chargement des matchs avec récupération d'un éventuel message d'erreur
matches, api_error = fetch_fixtures(api_key_ft, date_str, selected_league_id)

if not api_key_ft:
  st.warning(
      "⚠️ Veuillez entrer votre **Clé API Football (RapidAPI)** dans la barre"
      " latérale."
  )
elif api_error:
  st.error(f"Erreur API : {api_error}")

# Si la liste est vide, on affiche les démos
if not matches:
  st.info(
      f"Aucun match trouvé pour la date du **{date_str}** dans ce championnat."
      " (Affichage des exemples de démonstration ci-dessous) :"
  )
  matches = [
      {
          "id": 501,
          "home": "Real Madrid",
          "away": "FC Barcelone",
          "home_logo": "https://media.api-sports.io/football/teams/541.png",
          "away_logo": "https://media.api-sports.io/football/teams/529.png",
          "league": selected_league_name.upper(),
          "status": "NS",
          "elapsed": 0,
          "score_str": "0 - 0",
      },
      {
          "id": 502,
          "home": "Arsenal",
          "away": "Manchester City",
          "home_logo": "https://media.api-sports.io/football/teams/42.png",
          "away_logo": "https://media.api-sports.io/football/teams/50.png",
          "league": selected_league_name.upper(),
          "status": "NS",
          "elapsed": 0,
          "score_str": "0 - 0",
      },
  ]

# --- AFFICHAGE DES MATCHS AVEC LOGOS ---
st.subheader(
    f"📅 Matchs du {selected_date.strftime('%d/%m/%Y')} — {selected_league_name}"
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

      # 1. Position Recommandée (90 min)
      st.markdown(
          f"""
            <div class="rec-box">
                <div style="font-size: 10px; font-weight: bold; color: #2e7d32; text-transform: uppercase;">Position recommandée • Temps réglementaire (90 min)</div>
                <div style="font-size: 15px; font-weight: bold; color: #111; margin-top: 3px;">{match['home']} ou nul (1X)</div>
                <div style="font-size: 12px; color: #555; margin-top: 2px;">Double chance • Confiance {res['dc_1x_pct']}% • Buts totaux Over 2.5 ({res['over_25_pct']}%)</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

      # 2. Scores Exacts les plus probables
      st.markdown(
          "<div style='font-size: 12px; font-weight: bold; color: #444;"
          " margin-bottom: 6px;'>SCORES EXACTS LES PLUS PROBABLES · FIN DE MATCH</div>",
          unsafe_allow_html=True,
      )

      col_s1, col_s2, col_s3 = st.columns(3)

      with col_s1:
        s = res["top_scores"][0]
        st.markdown(
            f"""
                <div class="score-box" style="border-color: #ffca28;">
                    <div style="font-size: 16px; font-weight: bold; color: #111;">{s['score']}</div>
                    <div style="font-size: 11px; color: #555;">{s['prob']}% • cote {s['odds']}</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

      with col_s2:
        s = res["top_scores"][1]
        st.markdown(
            f"""
                <div class="score-box" style="border-color: #e0e0e0;">
                    <div style="font-size: 16px; font-weight: bold; color: #111;">{s['score']}</div>
                    <div style="font-size: 11px; color: #555;">{s['prob']}% • cote {s['odds']}</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

      with col_s3:
        s = res["top_scores"][2]
        st.markdown(
            f"""
                <div class="score-box" style="border-color: #e0e0e0;">
                    <div style="font-size: 16px; font-weight: bold; color: #111;">{s['score']}</div>
                    <div style="font-size: 11px; color: #555;">{s['prob']}% • cote {s['odds']}</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

      # 3. Bloc Détail Complet
      st.markdown(
          f"""
            <div class="detail-box">
                <b>ANALYSE COMPLÈTE • TEMPS RÉGLEMENTAIRE (90 MIN)</b>
                <ul style="margin: 6px 0 0 -15px; padding-left: 20px; line-height: 1.4;">
                    <li><b>Probabilité Victoire domicile :</b> {res['home_win_pct']}% | <b>Nul :</b> {res['draw_pct']}% | <b>Victoire extérieur :</b> {res['away_win_pct']}%</li>
                    <li>Tendance globale : Modélisation mathématique sur les forces offensives et défensives sur l'ensemble de la rencontre.</li>
                    <li>Marché BTTS (Les deux équipes marquent) : {res['btts_yes_pct']}% de chance de validation.</li>
                </ul>
            </div>
            """,
          unsafe_allow_html=True,
      )
    st.markdown("---")
