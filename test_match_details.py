from fc_clubs_api import FC27API
from datetime import datetime

CLUB_ID = 87430
api = FC27API()

def show_data(label, data, limit=3):
    print(f"\n--- {label} ---")
    if data is None:
        print("Veri yok")
    elif isinstance(data, list):
        print("Kayıt sayısı:", len(data))
        for item in data[:limit]:
            print(item)
    elif isinstance(data, dict):
        print("Alanlar:", list(data.keys()))
        print(data)
    else:
        print(type(data).__name__, data)

# Son maçlar ve tarih kapsamı
try:
    matches = api.get_club_matches(CLUB_ID, count=100)
    show_data("MAÇLAR", matches, 2)

    if isinstance(matches, list):
        dates = [
            m.get("timestamp") for m in matches
            if isinstance(m, dict) and m.get("timestamp")
        ]
        if dates:
            print("\nEn eski dönen maç:", min(dates))
            print("En yeni dönen maç:", max(dates))
except Exception as e:
    print("MAÇ HATASI:", repr(e))

# Maç başına oyuncular ve olaylar
try:
    details = api.get_match_players(
        CLUB_ID,
        count=3,
        both_teams=True,
        include_events=True
    )
    show_data("MAÇ OYUNCULARI VE OLAYLARI", details, 4)
except Exception as e:
    print("OYUNCU DETAY HATASI:", repr(e))

