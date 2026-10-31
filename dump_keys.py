from fc_clubs_api import FC27API
import json

api = FC27API()
CLUB_ID = 87430

players = api.get_match_players(CLUB_ID, match_type="friendlyMatch", count=1, both_teams=True, include_events=True, all_columns=True) or []
if not players:
    players = api.get_match_players(CLUB_ID, match_type="leagueMatch", count=1, both_teams=True, include_events=True, all_columns=True) or []

if players:
    p = players[0]
    print("\n--- OYUNCU HAM VERİ ALANLARI (KEYS) ---")
    keys = sorted(p.keys())
    for k in keys:
        print(f"{k}: {p[k]}")
else:
    print("Oyuncu verisi bulunamadı.")