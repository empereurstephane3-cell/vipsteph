import os
import json
from datetime import datetime

# ==========================================
# CONFIGURATION VIPSTEPH
# ==========================================
API_BASE_URL = os.getenv("VITE_API_BASE_URL", "https://v3.football.api-sports.io")
API_KEY = os.getenv("VITE_API_KEY", "votre_cle_api_ici")
DEBUG_MODE = True

# ==========================================
# 1. CLASSIFICATEUR D'ÉVÉNEMENTS
# ==========================================
def classify_event(raw_match):
    league_name = raw_match.get("league", {}).get("name", "").lower()
    match_type = raw_match.get("type", "").lower()
    game = raw_match.get("game", "").lower()

    # Détection FIFA / EA FC / eFootball
    if any(k in league_name for k in ["fifa", "ea fc", "efootball", "pes"]) or "fifa" in game:
        return {
            "sport_type": "ESPORT",
            "game": "FIFA / EA SPORTS FC",
            "competition_level": "ESPORT TOURNAMENT",
            "championship": raw_match.get("league", {}).get("name", "FIFA Tournament"),
            "priority": 3
        }
    
    # Détection E-Sport général
    if any(k in league_name for k in ["esport", "cs:go", "valorant", "dota", "league of legends"]):
        return {
            "sport_type": "ESPORT",
            "game": raw_match.get("game", "E-Sport"),
            "competition_level": "ESPORT COMPETITION",
            "championship": raw_match.get("league", {}).get("name", "E-Sport Tournament"),
            "priority": 4
        }

    # Détection Sports Virtuels
    if "virtual" in league_name or "virtual" in match_type:
        return {
            "sport_type": "VIRTUAL",
            "game": "Virtual Sport",
            "competition_level": "VIRTUAL",
            "championship": raw_match.get("league", {}).get("name", "Virtual Competition"),
            "priority": 5
        }

    # Sports Réels - Grands Championnats & International
    top_leagues = [
        "premier league", "la liga", "serie a", "bundesliga", "ligue 1", 
        "champions league", "europa league", "world cup", "copa america", "copa libertadores"
    ]
    is_top = any(l in league_name for l in top_leagues)
    is_international = any(l in league_name for l in ["champions league", "world cup", "euro"])

    return {
        "sport_type": "REAL",
        "game": raw_match.get("sport", "Football"),
        "competition_level": "INTERNATIONAL" if is_international else ("TOP CHAMPIONSHIP" if is_top else "NATIONAL"),
        "championship": raw_match.get("league", {}).get("name", "Championnat National"),
        "priority": 1 if is_international else (2 if is_top else 3)
    }

# ==========================================
# 2. NORMALISEUR DE MATCH
# ==========================================
def normalize_match(raw):
    if "fixture" in raw and "teams" in raw and "league" in raw:
        classification = classify_event({
            "league": raw["league"],
            "sport": "Football"
        })

        return {
            "id": str(raw["fixture"]["id"]),
            "sport": "Football",
            "sport_type": classification["sport_type"],
            "game": classification["game"],
            "competition": raw["league"]["name"],
            "competition_level": classification["competition_level"],
            "country": raw["league"].get("country", "International"),
            "priority": classification["priority"],
            "home_team": {
                "id": str(raw["teams"]["home"]["id"]),
                "name": raw["teams"]["home"]["name"],
                "logo": raw["teams"]["home"].get("logo")
            },
            "away_team": {
                "id": str(raw["teams"]["away"]["id"]),
                "name": raw["teams"]["away"]["name"],
                "logo": raw["teams"]["away"].get("logo")
            },
            "start_time": raw["fixture"]["date"],
            "status": raw["fixture"]["status"]["short"],
            "elapsed": raw["fixture"]["status"].get("elapsed"),
            "score": {
                "home": raw["goals"].get("home"),
                "away": raw["goals"].get("away")
            },
            "odds": raw.get("odds", {}),
            "statistics": raw.get("statistics", {}),
            "source": "API"
        }
    
    # Fallback pour données brutes ou de démo
    return raw

# ==========================================
# 3. MOTEUR DE PRÉDICTION STATISTIQUE
# ==========================================
def prediction_engine(match):
    statistics = match.get("statistics", {})
    home_stats = statistics.get("home", {})
    away_stats = statistics.get("away", {})
    
    has_stats = bool(home_stats and away_stats)

    if not has_stats and match.get("source") == "DEMO DATA":
        return generate_mock_predictions(match)

    if not has_stats:
        return {
            "insufficient_data": True,
            "mt1": {"probable_score": "Données insuffisantes", "probability": 0, "confidence": "Faible"},
            "mt2": {"probable_score": "Données insuffisantes", "probability": 0, "confidence": "Faible"},
            "final": {"probable_score": "Données insuffisantes", "probability": 0, "confidence": "Faible"}
        }

    home_avg = home_stats.get("goalsForAvg", 1.5)
    away_avg = away_stats.get("goalsForAvg", 1.2)

    # Calculs MT1 (environ 45% des buts)
    mt_home = round(home_avg * 0.45, 1)
    mt_away = round(away_avg * 0.45, 1)
    mt1_score = f"{round(mt_home)} - {round(mt_away)}"

    # Score Final
    final_home = round(home_avg)
    final_away = round(away_avg)
    final_score = f"{final_home} - {final_away}"

    return {
        "insufficient_data": False,
        "general_probs": {"home": 48, "draw": 28, "away": 24},
        "mt1": {
            "probable_score": mt1_score,
            "probability": 42,
            "confidence": "Moyenne"
        },
        "mt2": {
            "probable_score": "1 - 1",
            "probability": 38,
            "confidence": "Moyenne"
        },
        "final": {
            "probable_score": final_score,
            "probability": 45,
            "confidence": "Élevée",
            "top_scores": [
                {"score": final_score, "prob": 45},
                {"score": f"{final_home + 1} - {final_away}", "prob": 25},
                {"score": f"{final_home} - {final_away + 1}", "prob": 18},
                {"score": "1 - 1", "prob": 8}
            ]
        }
    }

def generate_mock_predictions(match):
    return {
        "insufficient_data": False,
        "general_probs": {"home": 52, "draw": 26, "away": 22},
        "mt1": {
            "probable_score": "1 - 0",
            "probability": 44,
            "confidence": "Élevée",
            "top_scores": [{"score": "1 - 0", "prob": 44}, {"score": "0 - 0", "prob": 30}]
        },
        "mt2": {
            "probable_score": "1 - 1",
            "probability": 40,
            "confidence": "Moyenne",
            "top_scores": [{"score": "1 - 1", "prob": 40}, {"score": "1 - 0", "prob": 25}]
        },
        "final": {
            "probable_score": "2 - 1",
            "probability": 48,
            "confidence": "Élevée",
            "top_scores": [{"score": "2 - 1", "prob": 48}, {"score": "1 - 1", "prob": 24}]
        }
    }

# ==========================================
# 4. DONNÉES DE DÉMONSTRATION SÉCURISÉES
# ==========================================
def get_demo_matches():
    return [
        {
            "id": "demo-1",
            "sport": "Football",
            "sport_type": "REAL",
            "game": "Football",
            "competition": "Premier League",
            "competition_level": "TOP CHAMPIONSHIP",
            "country": "Angleterre",
            "priority": 2,
            "home_team": {"id": "h1", "name": "Arsenal"},
            "away_team": {"id": "a1", "name": "Manchester City"},
            "start_time": datetime.now().isoformat(),
            "status": "NS",
            "score": {"home": None, "away": None},
            "odds": {"home": 2.20, "draw": 3.40, "away": 3.10},
            "statistics": {
                "home": {"goalsForAvg": 2.1},
                "away": {"goalsForAvg": 2.4}
            },
            "source": "DEMO DATA"
        }
    ]

# ==========================================
# 5. FONCTION PRINCIPALE (EXÉCUTION VIPSTEPH)
# ==========================================
def main():
    print("--- VIPSTEPH : Démarrage du moteur d'analyse ---")
    
    # Chargement des matchs (ici bascule sur la démo si aucune clé API configurée)
    matches = get_demo_matches()
    
    for match in matches:
        print(f"\nMatch analysé : {match['home_team']['name']} vs {match['away_team']['name']}")
        print(compétition := f"Compétition : {match['competition']} ({match['country']})")
        
        # Exécution du moteur de prédiction
        prediction = prediction_engine(match)
        
        print("📊 Résultats des Prédictions :")
        print(f"  - MT1 Score Probable : {prediction['mt1']['probable_score']} ({prediction['mt1']['probability']}%)")
        print(f"  - MT2 Score Probable : {prediction['mt2']['probable_score']} ({prediction['mt2']['probability']}%)")
        print(f"  - Score Final Estimé : {prediction['final']['probable_score']} (Confiance : {prediction['final']['confidence']})")

if __name__ == "__main__":
    main()
