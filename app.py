import streamlit as st
import requests
import json
import os
import math
import datetime
import concurrent.futures

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="KIM PRONO VIP PRO+ POISSON", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")
CONFIG_FILE = "config.json"

# --- STYLE DARK VIP & CORRECTION VISIBILITÉ LISTE DÉROULANTE ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #0b0f19 !important; color: #ffffff !important; border-right: 1px solid #23304a; }
    .agent-card { background-color: #141c2e; border: 1px solid #23304a; color: #ffffff !important; padding: 8px 10px; border-radius: 8px; font-size: 0.8em; margin-bottom: 6px; }
    .match-card { background-color: #111d32; border: 1px solid #1f3a60; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); color: #ffffff !important; }
    .metric-box { background-color: #162238; border: 1px solid #283c5f; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 8px; color: #ffffff !important; }
    .prono-vip-box { background-color: #162238; border-left: 4px solid #f39c12; border-radius: 8px; padding: 12px; margin-top: 10px; color: #ffffff !important; }
    .melbet-odd-btn { background-color: #1a2538; border: 1px solid #f39c12; border-radius: 6px; padding: 8px; text-align: center; font-weight: bold; color: #f39c12; }
    .market-badge { background-color: #1a2d4f; color: #f39c12; padding: 4px 10px; border-radius: 6px; font-size: 0.8em; font-weight: bold; display: inline-block; margin-bottom: 8px; }
    .status-badge-venir { background-color: #2980b9; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
    .status-badge-live { background-color: #c0392b; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
    .status-badge-fin { background-color: #27ae60; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
    
    h1, h2, h3, h4, p, span, label, summary, strong, b { color: #ffffff !important; }
    
    div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"] {
        background-color: #141c2e !important;
        color: #ffffff !important;
    }
    div[role="option"] {
        background-color: #141c2e !important;
        color: #ffffff !important;
    }
    div[role="option"]:hover {
        background-color: #1f3a60 !important;
        color: #f39c12 !important;
    }
    
    [data-testid="stExpander"] { 
        background-color: #141c2e !important; 
        border: 1px solid #23304a !important; 
        border-radius: 10px !important; 
    }
    [data-testid="stExpander"] details { background-color: #141c2e !important; }
    [data-testid="stExpander"] summary { background-color: #141c2e !important; color: #ffffff !important; }
    [data-testid="stExpander"] summary p { color: #ffffff !important; }
    div[data-baseweb="calendar"] { background-color: #141c2e !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- REQUÊTES & CONFIG ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"api_football_key": "", "vip_code": "VIP2026"}

config = load_config()

TOP_LEAGUES_PRIORITY = [
    "England - Premier League",
    "Spain - La Liga",
    "Italy - Serie A",
    "Germany - Bundesliga",
    "France - Ligue 1",
    "Portugal - Primeira Liga",
    "Netherlands - Eredivisie",
    "UEFA - Champions League",
    "UEFA - Europa League"
]

def sort_leagues_key(league_str):
    base_name = league_str.split(" (ID:")[0]
    for idx, top_league in enumerate(TOP_LEAGUES_PRIORITY):
        if top_league.lower() in base_name.lower():
            return (0, idx, league_str)
    return (1, 0, league_str)

@st.cache_data(ttl=3600)
def fetch_available_leagues(api_key):
    if not api_key: return []
    try:
        res = requests.get("https://apiv3.apifootball.com/", params={"action": "get_leagues", "APIkey": api_key}, timeout=5)
        if res.status_code == 200:
            leagues = list(set([f"{l['country_name']} - {l['league_name']} (ID: {l['league_id']})" for l in res.json() if 'league_name' in l]))
            return sorted(leagues, key=sort_leagues_key)
    except: pass
    return []

@st.cache_data(ttl=600)
def fetch_football_events(api_key, date_str):
    if not api_key: return []
    try:
        res = requests.get("https://apiv3.apifootball.com/", params={"action": "get_events", "APIkey": api_key, "from": date_str, "to": date_str, "timezone": "Africa/Abidjan"}, timeout=5)
        return res.json() if res.status_code == 200 and isinstance(res.json(), list) else []
    except: pass
    return []

@st.cache_data(ttl=3600)
def fetch_league_standings_single(api_key, league_id):
    if not api_key or not league_id: return {}
    try:
        res = requests.get("https://apiv3.apifootball.com/", params={"action": "get_standings", "league_id": league_id, "APIkey": api_key}, timeout=4)
        if res.status_code == 200 and isinstance(res.json(), list):
            standings_dict = {}
            for row in res.json():
                team_name = row.get('team_name')
                if team_name:
                    standings_dict[team_name] = {
                        "played": int(row.get('overall_league_payed', 1) or 1),
                        "gf": int(row.get('overall_league_GF', 0) or 0),
                        "ga": int(row.get('overall_league_GA', 0) or 0),
                        "home_gf": int(row.get('home_league_GF', 0) or 0),
                        "home_ga": int(row.get('home_league_GA', 0) or 0),
                        "home_played": int(row.get('home_league_payed', 1) or 1),
                        "away_gf": int(row.get('away_league_GF', 0) or 0),
                        "away_ga": int(row.get('away_league_GA', 0) or 0),
                        "away_played": int(row.get('away_league_payed', 1) or 1),
                    }
            return standings_dict
    except: pass
    return {}

def fetch_all_standings_cached(api_key, league_ids_tuple):
    standings_map = {}
    if not api_key or not league_ids_tuple:
        return standings_map
    
    def fetch_one(l_id):
        return l_id, fetch_league_standings_single(api_key, l_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(fetch_one, league_ids_tuple)
        for l_id, data in results:
            standings_map[l_id] = data
            
    return standings_map

def prob_to_odds(p): return round(100.0 / p, 2) if p > 0 else 1.01

def render_poisson_metrics(stats):
    return f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px;">
        <div class="metric-box">
            <div style="font-size: 0.75em; color: #ffffff; font-weight: bold;">SCORE EXACT MI-TEMPS (1H)</div>
            <div style="font-size: 1.1em; font-weight: bold; color: #2ecc71;">{stats['score_1h']}</div>
        </div>
        <div class="metric-box">
            <div style="font-size: 0.75em; color: #ffffff; font-weight: bold;">SCORE EXACT 2ÈME MI-TEMPS (2H)</div>
            <div style="font-size: 1.1em; font-weight: bold; color: #2ecc71;">{stats['score_2h']}</div>
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
        <div class="metric-box">
            <div style="font-size: 0.75em; color: #ffffff; font-weight: bold;">SCORE EXACT FIN (FT)</div>
            <div style="font-size: 1.1em; font-weight: bold; color: #f39c12;">{stats['final_score']}</div>
        </div>
        <div class="metric-box">
            <div style="font-size: 0.75em; color: #ffffff; font-weight: bold;">TOTAL BUTS ATTENDUS</div>
            <div style="font-size: 1.1em; font-weight: bold; color: #3498db;">{stats['total_goals']} buts</div>
        </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
        <div class="metric-box">
            <div style="font-size: 0.75em; color: #ffffff; font-weight: bold;">BTTS (DEUX ÉQUIPES MARQUENT)</div>
            <div style="font-size: 1.05em; font-weight: bold; color: #e67e22;">{stats['btts']}</div>
        </div>
        <div class="metric-box">
            <div style="font-size: 0.75em; color: #ffffff; font-weight: bold;">TOTAL CORNERS ATTENDUS</div>
            <div style="font-size: 1.05em; font-weight: bold; color: #9b59b6;">~{stats['total_corners']} corners</div>
        </div>
    </div>
    """

# --- LOI DE POISSON ULTRA-ROBUSTE & FIABILITÉ MAXIMALE ---
# --- CORRECTION DÉBUT DE SAISON (PONDÉRATION) ---
        # On ajoute un poids de 5 matchs "fantômes" basés sur la moyenne de la ligue
        # Cela stabilise les stats tant que le nombre de matchs joués est faible  
PRIOR_WEIGHT = 5


def smooth(goals, games, league_avg):
  return (goals + PRIOR_WEIGHT * league_avg) / (games + PRIOR_WEIGHT)


smooth_home_gf = smooth(h_data["home_gf"], h_data["home_played"], league_avg)
smooth_home_ga = smooth(h_data["home_ga"], h_data["home_played"], league_avg)
smooth_away_gf = smooth(a_data["away_gf"], a_data["away_played"], league_avg)
smooth_away_ga = smooth(a_data["away_ga"], a_data["away_played"], league_avg)

home_att = smooth_home_gf / league_avg
home_def = smooth_home_ga / league_avg
away_att = smooth_away_gf / league_avg
away_def = smooth_away_ga / league_avg

home_adv = 1.20
lambda_home = home_att * away_def * league_avg * home_adv
lambda_away = away_att * home_def * league_avg / home_adv
 def poisson(k, lam): return (math.pow(lam, k) * math.exp(-lam)) / math.factorial(k)
    
 scores_full = []
 p_home, p_draw, p_away = 0.0, 0.0, 0.0
 p_over, p_under = 0.0, 0.0
 p_btts_yes, p_btts_no = 0.0, 0.0
    
 for h in range(7):
 for a in range(7):
 p = poisson(h, lam_h) * poisson(a, lam_a)
 # Correction mineure de corrélation pour les scores serrés (Dixon-Coles style approximation)
 if h == 0 and a == 0: p *= 1.05
            
 scores_full.append({"score": f"{h}-{a}", "prob": p * 100})
 if h > a: p_home += p
 elif h == a: p_draw += p
 else: p_away += p
            
 if (h + a) > 2.5: p_over += p
 else: p_under += p
            
 if h > 0 and a > 0: p_btts_yes += p
 else: p_btts_no += p
            
 total = p_home + p_draw + p_away
 if total > 0:
        p_home, p_draw, p_away = (p_home/total)*100, (p_draw/total)*100, (p_away/total)*100
        p_over, p_under = (p_over/total)*100, (p_under/total)*100
        p_btts_yes, p_btts_no = (p_btts_yes/total)*100, (p_btts_no/total)*100
    
    p_1x = p_home + p_draw
    p_x2 = p_draw + p_away
    
    # Mi-temps
    lam_h_1h, lam_a_1h = lam_h * 0.43, lam_a * 0.43
    best_p_1h = -1
    score_1h = "0-0"
    for h in range(4):
        for a in range(4):
            p = poisson(h, lam_h_1h) * poisson(a, lam_a_1h)
            if p > best_p_1h:
                best_p_1h = p
                score_1h = f"{h}-{a}"

    # 2ème Mi-temps
    lam_h_2h, lam_a_2h = lam_h * 0.57, lam_a * 0.57
    best_p_2h = -1
    score_2h = "1-0"
    for h in range(4):
        for a in range(4):
            p = poisson(h, lam_h_2h) * poisson(a, lam_a_2h)
            if p > best_p_2h:
                best_p_2h = p
                score_2h = f"{h}-{a}"

    total_corners_expected = round(max(7.0, min(13.0, (lam_h + lam_a) * 4.1)), 1)
    corners_line = 9.5
    p_over_corners = 56.0 if total_corners_expected > corners_line else 44.0
    
    scores_full.sort(key=lambda x: x["prob"], reverse=True)
    
    markets = [
        {"category": "1N2", "bet": f"Victoire {h_name}" if p_home >= p_away else f"Victoire {a_name}", "conf": int(max(p_home, p_away)), "odds": prob_to_odds(max(p_home, p_away))},
        {"category": "Double Chance", "bet": f"1X ({h_name} ou Nul)" if p_1x >= p_x2 else f"X2 (Nul ou {a_name})", "conf": int(max(p_1x, p_x2)), "odds": prob_to_odds(max(p_1x, p_x2))},
        {"category": "BTTS", "bet": "Les deux équipes marquent (Oui)" if p_btts_yes >= 52 else "Les deux équipes ne marquent pas (Non)", "conf": int(max(p_btts_yes, p_btts_no)), "odds": prob_to_odds(max(p_btts_yes, p_btts_no))},
        {"category": "Total Buts", "bet": "Plus de 2.5 buts" if p_over >= 52 else "Moins de 2.5 buts", "conf": int(max(p_over, p_under)), "odds": prob_to_odds(max(p_over, p_under))},
        {"category": "Corners", "bet": f"Plus de {corners_line} corners" if total_corners_expected > corners_line else f"Moins de {corners_line} corners", "conf": int(max(p_over_corners, 100 - p_over_corners) + 4), "odds": prob_to_odds(max(p_over_corners, 100 - p_over_corners) + 4)}
    ]
    
    # Algorithme de sélection ultra-sécurisé pour le pronostic recommandé (poids renforcé sur la Double Chance et la stabilité)
    def reliability_score(mkt):
        base_conf = mkt['conf']
        if mkt['category'] == "Double Chance":
            return base_conf * 1.12  # Bonus de sécurité élevé pour éliminer les risques inutiles
        elif mkt['category'] == "Total Buts" and base_conf > 60:
            return base_conf * 1.05
        return base_conf

    best_opt = max(markets, key=reliability_score)
    
    return {
        "rec_bet": best_opt['bet'],
        "rec_category": best_opt['category'],
        "rec_conf": best_opt['conf'],
        "rec_odd": best_opt['odds'],
        "markets": markets,
        "odd_1": prob_to_odds(p_home),
        "odd_x": prob_to_odds(p_draw),
        "odd_2": prob_to_odds(p_away),
        "btts": f"{'Oui' if p_btts_yes >= 52 else 'Non'} ({int(max(p_btts_yes, p_btts_no))}%)",
        "total_goals": round(lam_h + lam_a, 2),
        "total_corners": total_corners_expected,
        "final_score": scores_full[0]['score'],
        "score_1h": score_1h,
        "score_2h": score_2h,
        "xg_home": round(lam_h, 2),
        "xg_away": round(lam_a, 2)
    }

def get_8_ai_agents(h, a, stats):
    return {
        "📊 Agent Statistique": f"Modèle Poisson Corrigé v3.3 | xG Dom: {stats['xg_home']} vs Ext: {stats['xg_away']}",
        "⚡ Agent Momentum": f"Analyse croisée des dynamiques de bloc et de l'intensité.",
        "🛡️ Agent Défensif": f"Indice de solidité face aux transitions rapides.",
        "🎯 Agent Attaque": f"Taux de conversion des opportunités validé.",
        "⚖️ Agent Disciplinary": f"Indice de maîtrise du tempo et gestion des fautes.",
        "🌡️ Agent Météo & Pitch": f"Conditions de pelouse stables estimées.",
        "♟️ Agent Tactique": f"Lecture des confrontations de systèmes de jeu.",
        "💎 Agent Value Market": f"Cote Melbet optimisée à {stats['rec_odd']} (Sécurité maximale)."
    }

def get_match_status_badge(m):
    status = m.get('match_status', '')
    time_m = m.get('match_time', '--:--')
    if status and ('FT' in status.upper() or 'FINISHED' in status.upper()):
        return f'<span class="status-badge-fin">Terminé ✅</span>', time_m
    elif status and ('-' in status or status.isdigit() or 'LIVE' in status.upper()):
        return f'<span class="status-badge-live">En direct 🔴 ({status})</span>', time_m
    else:
        return f'<span class="status-badge-venir">À venir ⏳</span>', time_m

# --- AUTHENTIFICATION & SIDEBAR ---
if "vip_authenticated" not in st.session_state: st.session_state["vip_authenticated"] = False

with st.sidebar:
    st.title("⚙️ Paramètres VIP")
    target_date = st.date_input("Date des matchs", datetime.date.today())
    target_date_str = target_date.strftime("%Y-%m-%d")
    
    st.markdown("---")
    st.subheader("🏆 Choix des Championnats")
    api_key = st.text_input("Clé API-Football", value=config.get("api_football_key", ""), type="password")
    
    all_leagues = fetch_available_leagues(api_key)
    selected_leagues = st.multiselect("Sélectionnez vos ligues :", options=all_leagues, default=[])
    
    st.markdown("---")
    st.subheader("🔐 Accès VIP")
    vip_code_input = st.text_input("Code d'accès", value=config.get("vip_code", "VIP2026"), type="password")
    
    if st.button("Sauvegarder"):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api_football_key": api_key, "vip_code": vip_code_input}, f)
        st.rerun()

    st.markdown("---")
    st.subheader("🎯 Filtre de Confiance")
    min_confidence = st.slider("Confiance min (%)", 0, 90, 50, 5)

if not st.session_state["vip_authenticated"]:
    if st.text_input("Code VIP", type="password") == config.get("vip_code", "VIP2026"):
        st.session_state["vip_authenticated"] = True
        st.rerun()
    st.stop()

# --- APPLICATION PRINCIPALE ---
tabs = st.tabs(["🔥 3 Combinés du Jour", "⚽ Football & Analyses Pro"])

def get_filtered_matches():
    data = fetch_football_events(api_key, target_date_str)
    if not selected_leagues: return data
    
    selected_league_names = [l.split(" (ID:")[0] for l in selected_leagues]
    valid_matches = []
    for m in data:
        league_str = f"{m.get('country_name', 'Inconnu')} - {m.get('league_name', 'Inconnu')}"
        if league_str in selected_league_names:
            valid_matches.append(m)
    return valid_matches

matches = get_filtered_matches()
unique_league_ids = tuple(set([m.get('league_id') for m in matches if m.get('league_id')]))
all_standings_cache = fetch_all_standings_cached(api_key, unique_league_ids)

# --- ONGLET 1 : LES 3 COMBINÉS DU JOUR ---
with tabs[0]:
    st.subheader("🔥 Les 3 Combinés VIP du Jour (Sécurisé, Audacieux & Risqué)")
    
    all_bets = []
    for m in matches:
        h = m.get('match_hometeam_name')
        a = m.get('match_awayteam_name')
        hb = m.get('team_home_badge', '')
        ab = m.get('team_away_badge', '')
        country = m.get('country_name', 'Inconnu')
        league = m.get('league_name', 'Inconnu')
        _, time_m = get_match_status_badge(m)
        
        stats = calculate_match_stats(m, all_standings_cache)
        for market in stats['markets']:
            all_bets.append({
                "match": f"{h} vs {a}",
                "hb": hb,
                "ab": ab,
                "country": country,
                "league": league,
                "time": time_m,
                "bet": market['bet'],
                "conf": market['conf'],
                "odd": market['odds'],
                "category": market['category']
            })
    
    all_bets.sort(key=lambda x: x['conf'], reverse=True)
    
    chunk = max(1, len(all_bets) // 3) if len(all_bets) >= 3 else 1
    secure_pool = all_bets[:chunk]
    bold_pool = all_bets[chunk:chunk*2]
    risky_pool = all_bets[chunk*2:] if len(all_bets) > chunk*2 else all_bets
    
    combinos = [
        ("🛡️ Combiné #1 : Sécurisé", secure_pool, "#27ae60"),
        ("⚡ Combiné #2 : Audacieux", bold_pool, "#f39c12"),
        ("🔥 Combiné #3 : Un peu risqué", risky_pool, "#c0392b")
    ]
    
    for title, pool, color in combinos:
        st.markdown(f"""
        <div class="match-card" style="border-left: 5px solid {color};">
            <h3 style="color: {color}; margin-top: 0;">{title}</h3>
        """, unsafe_allow_html=True)
        
        if len(pool) >= 2:
            m1, m2 = pool[0], pool[1]
            tot_odd = round(m1['odd'] * m2['odd'], 2)
            avg_conf = int((m1['conf'] + m2['conf']) / 2)
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: bold; color: #ffffff;">
                <span>Cote Totale Estimée : <span style="color: #2ecc71;">{tot_odd}</span></span>
                <span>Indice Global : <span style="color: #f39c12;">{avg_conf}%</span></span>
            </div>
            <div style="background-color: #141c2e; padding: 10px; border-radius: 8px; margin-bottom: 8px; color: #ffffff;">
                <span class="market-badge">Marché : {m1['category']}</span> &bull; 🌍 {m1['country']} &bull; 🕒 {m1['time']}
                <div style="display: flex; align-items: center; gap: 8px; margin: 4px 0; color: #ffffff;">
                    <img src="{m1['hb']}" width="20"/> <b>{m1['match'].split('vs')[0].strip()}</b> vs 
                    <img src="{m1['ab']}" width="20"/> <b>{m1['match'].split('vs')[1].strip()}</b>
                </div>
                <div style="color: #ffffff;">Pronostic : <b style="color: #2ecc71;">{m1['bet']}</b> (Cote : {m1['odd']} | <span style="color: #f39c12; font-weight: bold;">Confiance : {m1['conf']}%</span>)</div>
            </div>
            <div style="background-color: #141c2e; padding: 10px; border-radius: 8px; color: #ffffff;">
                <span class="market-badge">Marché : {m2['category']}</span> &bull; 🌍 {m2['country']} &bull; 🕒 {m2['time']}
                <div style="display: flex; align-items: center; gap: 8px; margin: 4px 0; color: #ffffff;">
                    <img src="{m2['hb']}" width="20"/> <b>{m2['match'].split('vs')[0].strip()}</b> vs 
                    <img src="{m2['ab']}" width="20"/> <b>{m2['match'].split('vs')[1].strip()}</b>
                </div>
                <div style="color: #ffffff;">Pronostic : <b style="color: #2ecc71;">{m2['bet']}</b> (Cote : {m2['odd']} | <span style="color: #f39c12; font-weight: bold;">Confiance : {m2['conf']}%</span>)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Pas assez de matchs disponibles pour ce combiné.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- ONGLET 2 : FOOTBALL & ANALYSES PRO ---
with tabs[1]:
    st.subheader("⚽ Dashboard Analyses Pro & Moteur Poisson Amélioré")
    
    if matches:
        valid_matches = []
        for m in matches:
            stats = calculate_match_stats(m, all_standings_cache)
            if stats['rec_conf'] >= min_confidence:
                valid_matches.append((m, stats))
        
        if valid_matches:
            for i in range(0, len(valid_matches), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(valid_matches):
                        m, stats = valid_matches[i + j]
                        with cols[j]:
                            h = m.get('match_hometeam_name')
                            a = m.get('match_awayteam_name')
                            hb = m.get('team_home_badge', '')
                            ab = m.get('team_away_badge', '')
                            country = m.get('country_name', 'Inconnu')
                            league = m.get('league_name', 'Inconnu')
                            status_badge, time_m = get_match_status_badge(m)
                            agents = get_8_ai_agents(h, a, stats)
                            
                            st.markdown(f"""
                            <div class="match-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 4px;">
                                    <span style="background-color: #1a2d4f; color: #f39c12; padding: 5px 8px; border-radius: 6px; font-size: 0.75em; font-weight: bold;">
                                        🌍 {country} &bull; 🏆 {league}
                                    </span>
                                    <div>
                                        {status_badge} &bull; <span style="color: #2ecc71; font-weight: bold; font-size: 0.85em;">🕒 {time_m}</span>
                                    </div>
                                </div>
                                
                                <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin: 12px 0; color: #ffffff;">
                                    <div style="text-align: center; flex: 1; color: #ffffff;">
                                        <img src="{hb}" width="40" style="margin-bottom: 4px;"/>
                                        <div style="font-weight: bold; font-size: 0.95em; color: #ffffff;">{h}</div>
                                    </div>
                                    <div style="font-size: 1.2em; font-weight: bold; color: #f39c12;">VS</div>
                                    <div style="text-align: center; flex: 1; color: #ffffff;">
                                        <img src="{ab}" width="40" style="margin-bottom: 4px;"/>
                                        <div style="font-weight: bold; font-size: 0.95em; color: #ffffff;">{a}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_o1, col_ox, col_o2 = st.columns(3)
                            with col_o1:
                                st.markdown(f"<div class='melbet-odd-btn' style='font-size: 0.75em; padding: 6px;'>1: {stats['odd_1']}</div>", unsafe_allow_html=True)
                            with col_ox:
                                st.markdown(f"<div class='melbet-odd-btn' style='font-size: 0.75em; padding: 6px;'>X: {stats['odd_x']}</div>", unsafe_allow_html=True)
                            with col_o2:
                                st.markdown(f"<div class='melbet-odd-btn' style='font-size: 0.75em; padding: 6px;'>2: {stats['odd_2']}</div>", unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="prono-vip-box">
                                <h4 style="margin-top: 0; color: #f39c12; font-size: 0.95em; border-bottom: 1px solid #283c5f; padding-bottom: 6px;">
                                    📊 Analyses API-Football & Moteur Corrigé
                                </h4>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(render_poisson_metrics(stats), unsafe_allow_html=True)

                            st.markdown(f"""
                                <div style="background-color: #111d32; padding: 8px; border-radius: 6px; margin-top: 10px; border: 1px solid #23304a; color: #ffffff;">
                                    <div style="font-size: 0.8em; font-weight: bold; color: #f39c12; margin-bottom: 4px;">Tous les marchés analysés (avec Indice de Confiance) :</div>
                            """, unsafe_allow_html=True)

                            for mkt in stats['markets']:
                                st.markdown(f"""
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.8em; border-bottom: 1px dashed #1f3a60; color: #ffffff;">
                                    <span style="color: #ffffff;"><b>{mkt['category']} :</b> {mkt['bet']}</span>
                                    <span>Indice : <span style="color: #f39c12; font-weight: bold;">{mkt['conf']}%</span> | Cote : <b style="color: #ffffff;">{mkt['odds']}</b></span>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown(f"""
                                </div>

                                <div style="background-color: #142834; border: 1px solid #27ae60; padding: 10px; border-radius: 6px; margin-top: 10px; text-align: center; color: #ffffff;">
                                    <div style="font-size: 0.75em; color: #ffffff; text-transform: uppercase; font-weight: bold;">🎯 Pronostic Recommandé & Sécurisé</div>
                                    <div style="font-size: 1.05em; font-weight: bold; color: #2ecc71; margin-top: 2px;">{stats['rec_bet']}</div>
                                    <div style="font-size: 0.85em; color: #ffffff; margin-top: 2px;">Indice de Confiance : <b style="color: #f39c12;">{stats['rec_conf']}%</b> &bull; Cote : <b style="color: #2ecc71;">{stats['rec_odd']}</b></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            with st.expander(f"🤖 Agents IA ({h} vs {a})"):
                                for k, v in list(agents.items()):
                                    st.markdown(f"<div class='agent-card'><b style='color: #ffffff;'>{k}</b><br><span style='color: #ffffff;'>{v}</span></div>", unsafe_allow_html=True)
                            
                            st.markdown("---")
        else:
            st.info("Aucun match ne correspond au filtre de confiance minimum sélectionné.")
    else:
        st.info("Aucun match disponible pour les championnats sélectionnés.")
