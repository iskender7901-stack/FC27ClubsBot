from fc_clubs_api import FC27API
import traceback

CLUB_ID = 87430

def main():
    api = FC27API()

    print("=" * 50)
    print("FC 27 CLUBS API TESTI")
    print("=" * 50)

    tests = [
        ("Kulüp bilgileri", lambda: api.get_club_details(CLUB_ID)),
        ("Genel istatistikler", lambda: api.get_club_overall_stats(CLUB_ID)),
        ("Oyuncu istatistikleri", lambda: api.get_member_stats(CLUB_ID)),
        ("Son lig maçları", lambda: api.get_club_matches(CLUB_ID)),
    ]

    for name, test in tests:
        print(f"\n--- {name} ---")
        try:
            result = test()

            if result is None or result == [] or result == {}:
                print("İstek başarılı olabilir ancak veri boş döndü.")
            else:
                print("BAŞARILI")
                if isinstance(result, dict):
                    print("Alanlar:", list(result.keys())[:15])
                    print("Veri:", str(result)[:1200])
                elif isinstance(result, list):
                    print("Kayıt sayısı:", len(result))
                    for item in result[:2]:
                        print(str(item)[:1000])
                else:
                    print(str(result)[:1200])

        except Exception as exc:
            print("HATA:", type(exc).__name__, str(exc))
            traceback.print_exc(limit=2)

if __name__ == "__main__":
    main()
