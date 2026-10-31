"""Backfill stats_archive.json with past matches from EA API."""
import sys
import json
from datetime import datetime
from pathlib import Path
from fc_clubs_api import FC27API

CLUB_ID = 87430
BASE_DIR = Path(__file__).resolve().parent
ARCHIVE_FILE = BASE_DIR / "stats_archive.json"
api = FC27API()

def val(row, *keys, default=0):
    if not isinstance(row, dict):
        return default
    lookup = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        value = lookup.get(key.lower())
        if value is not None and value != "":
            return value
    return default

def number(row, *keys):
    try:
        return float(val(row, *keys, default=0) or 0)
    except (TypeError, ValueError):
        return 0.0

def normalize_position(pos_raw: str) -> str:
    p = str(pos_raw).upper().strip()
    if p in ("0", "GK", "GOAL", "GOALKEEPER", "KALECI"):
        return "KL"
    if any(k in p for k in ("CB", "LB", "RB", "RWB", "LWB", "DEF", "DEFENDER", "DEFE", "DEFANS")):
        return "DF"
    if any(k in p for k in ("CM", "CDM", "CAM", "LM", "RM", "MID", "MIDFIELDER", "MIDF", "ORTA SAHA")):
        return "OS"
    if any(k in p for k in ("ST", "CF", "RW", "LW", "RF", "LF", "FORW", "ATT", "FORWARD", "FORVET")):
        return "FV"
    return "OS"

data = {"matches": {}}
if ARCHIVE_FILE.exists():
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"matches": {}}

print("EA API'den gecmis maclar toplaniyor...")

for kind in ("leagueMatch", "playoffMatch", "friendlyMatch"):
    try:
        matches = api.get_club_matches(CLUB_ID, match_type=kind, count=10) or []
        players = api.get_match_players(CLUB_ID, match_type=kind, count=10, both_teams=True, include_events=True, all_columns=True) or []
    except Exception as exc:
        print(f"[{kind}] Cekilirken hata: {exc}")
        continue

    for m in matches:
        mid = str(val(m, "matchId", default=""))
        if not mid or mid in data["matches"]:
            continue

        stamp = val(m, "timestamp", default=None)
        iso_date = stamp.isoformat() if isinstance(stamp, datetime) else datetime.utcnow().isoformat()

        all_rows = [p for p in players if str(val(p, "matchId", default="")) == mid]
        own_players = [p for p in all_rows if str(val(p, "clubId", default="")) == str(CLUB_ID)]

        record = {
            "match_id": mid,
            "match_type": kind,
            "timestamp": iso_date,
            "result": str(val(m, "result", default="unknown")),
            "goals_for": int(number(m, "goals")),
            "goals_against": int(number(m, "goalsAgainst")),
            "opponent": str(val(m, "opponentName", default="Rakip")),
            "players": []
        }

        for p in own_players:
            p_name = str(val(p, "playername", "name", default="Unknown"))
            pos = normalize_position(val(p, "pos", default="OS"))
            record["players"].append({
                "name": p_name,
                "pos": pos,
                "rating": number(p, "rating"),
                "mom": int(number(p, "mom")),
                "goals": int(number(p, "goals")),
                "assists": int(number(p, "assists")),
                "second_assists": int(number(p, "secondAssists")),
                "key_passes": int(number(p, "throughPasses") + number(p, "throughBallAssists")),
                "interceptions": int(number(p, "interceptions") + number(p, "opponentsDispossessed")),
                "blocks": int(number(p, "crossesBlocked")),
                "clearances": int(number(p, "slidingTacklesWon") + number(p, "possessionWonDefensiveThird")),
                "dribbles": int(number(p, "dribblesBeat") + number(p, "dribblesCompleted") + number(p, "dribblesSkillMoveBeat")),
                "shots": int(number(p, "shots")),
                "passes_made": int(number(p, "passesmade", "passesCompleted")),
                "pass_attempts": int(number(p, "passattempts")),
                "tackles_won": int(number(p, "tacklesmade", "cleanTackles", "tacklesWon")),
                "tackle_attempts": int(number(p, "tackleattempts"))
            })

        data["matches"][mid] = record
        print(f"  -> Mac eklendi: #{mid} ({kind})")

with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n[BASARILI] Toplam {len(data['matches'])} mac arsive kaydedildi.")