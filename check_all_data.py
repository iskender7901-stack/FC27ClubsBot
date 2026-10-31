from collections import Counter
from fc_clubs_api import FC27API

CLUB_ID = 87430
api = FC27API()

for kind in ("leagueMatch", "friendlyMatch", "playoffMatch"):
    print("\n" + "=" * 65)
    print("MAÇ TÜRÜ:", kind)

    try:
        matches = api.get_club_matches(CLUB_ID, match_type=kind, count=10)
        if not isinstance(matches, list):
            print("Dönen veri:", repr(matches)[:500])
            matches = []

        print("Maç sayısı:", len(matches))
        for m in matches:
            print(
                m.get("matchId"),
                m.get("timestamp"),
                m.get("clubName"),
                m.get("goals"), "-", m.get("goalsAgainst"),
                m.get("opponentName")
            )

        players = api.get_match_players(
            CLUB_ID,
            match_type=kind,
            count=10,
            both_teams=True,
            all_columns=True,
            include_events=True
        )

        if not isinstance(players, list):
            print("Oyuncu verisi:", repr(players)[:500])
            players = []

        print("Oyuncu kayıt sayısı:", len(players))
        print("Maç başına oyuncu kaydı:", Counter(
            str(p.get("matchId")) for p in players
        ))
        print("Kulüp dağılımı:", Counter(
            str(p.get("clubId")) for p in players
        ))

        if players:
            print("Örnek oyuncu alanları:")
            print(", ".join(players[0].keys()))

    except Exception as e:
        print("HATA:", type(e).__name__, str(e))

print("\nTEST TAMAMLANDI")
