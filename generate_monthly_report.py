"""Generate monthly/periodic leaderboard card filtered by match type."""
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
ARCHIVE_FILE = BASE_DIR / "stats_archive.json"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()

def panel(draw, xy, radius=16, fill="#0b111c", outline="#263247", width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def generate_leaderboard(target_type="leagueMatch", days=30):
    """
    target_type: 'leagueMatch', 'playoffMatch', 'friendlyMatch' veya 'all'
    """
    type_labels = {
        "leagueMatch": "LİG MAÇLARI RAPORU",
        "playoffMatch": "PLAYOFF MAÇLARI RAPORU",
        "friendlyMatch": "DOSTLUK MAÇLARI RAPORU",
        "all": "GENEL (TÜM MAÇLAR) RAPORU"
    }
    title_label = type_labels.get(target_type, "KULÜP DÖNEMSEL RAPORU")

    if not ARCHIVE_FILE.exists():
        print("[HATA] Henüz arşiv dosyası (stats_archive.json) bulunamadı. Önce birkaç maç kartı üretmelisin.")
        return None

    with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches", {})
    cutoff = datetime.utcnow() - timedelta(days=days)

    filtered_matches = []
    for mid, m in matches.items():
        m_type = m.get("match_type", "leagueMatch")
        if target_type != "all" and m_type != target_type:
            continue
        try:
            m_time = datetime.fromisoformat(m.get("timestamp", ""))
            # timezone offset'i kaldırıp kıyasla
            if m_time.tzinfo:
                m_time = m_time.replace(tzinfo=None)
            if m_time >= cutoff:
                filtered_matches.append(m)
        except Exception:
            filtered_matches.append(m)

    if not filtered_matches:
        print(f"[BİLGİ] '{title_label}' için son {days} gün içerisinde kayıtlı maç bulunamadı.")
        return None

    # Oyuncu istatistiklerini topla
    player_stats = {}
    for m in filtered_matches:
        for p in m.get("players", []):
            name = p["name"]
            if name not in player_stats:
                player_stats[name] = {
                    "name": name,
                    "pos": p.get("pos", "OS"),
                    "matches": 0,
                    "ratings": [],
                    "goals": 0,
                    "assists": 0,
                    "second_assists": 0,
                    "key_passes": 0,
                    "interceptions": 0,
                    "dribbles": 0,
                    "shots": 0,
                    "passes_made": 0,
                    "pass_attempts": 0,
                    "tackles_won": 0,
                    "moms": 0
                }
            st = player_stats[name]
            st["matches"] += 1
            st["ratings"].append(float(p.get("rating", 0.0)))
            st["goals"] += int(p.get("goals", 0))
            st["assists"] += int(p.get("assists", 0))
            st["second_assists"] += int(p.get("second_assists", 0))
            st["key_passes"] += int(p.get("key_passes", 0))
            st["interceptions"] += int(p.get("interceptions", 0))
            st["dribbles"] += int(p.get("dribbles", 0))
            st["shots"] += int(p.get("shots", 0))
            st["passes_made"] += int(p.get("passes_made", 0))
            st["pass_attempts"] += int(p.get("pass_attempts", 0))
            st["tackles_won"] += int(p.get("tackles_won", 0))
            st["moms"] += int(p.get("mom", 0))

    # Ortalama reyting ve pas isabeti hesapla
    leaderboard = []
    for p in player_stats.values():
        avg_rating = sum(p["ratings"]) / len(p["ratings"]) if p["ratings"] else 0.0
        pass_pct = round(p["passes_made"] / p["pass_attempts"] * 100) if p["pass_attempts"] else 0
        p["avg_rating"] = avg_rating
        p["pass_pct"] = pass_pct
        leaderboard.append(p)

    # Sıralama: Ortalama Reyting ve Gol Katkısına göre
    leaderboard.sort(key=lambda x: (x["avg_rating"], x["goals"] + x["assists"]), reverse=True)

    # Görseli Çiz
    W, H = 1600, 900
    im = Image.new("RGB", (W, H), "#050910")
    d = ImageDraw.Draw(im, "RGBA")

    # Arka plan
    d.ellipse((-200, 100, 600, 900), fill=(0, 255, 145, 18))
    d.ellipse((1000, 100, 1800, 900), fill=(130, 40, 255, 20))

    # Header
    panel(d, (28, 22, 1572, 112), radius=22, fill=(8, 13, 22, 220), outline="#273143", width=2)
    d.text((58, 44), "GS", font=get_font(30, True), fill="#28f4a2")
    d.text((116, 43), "GraveShift Analytics", font=get_font(29, True), fill="#f8fafc")
    d.text((116, 77), f"EA SPORTS FC 27  /  {title_label.upper()}", font=get_font(13, True), fill="#31f0a6")
    d.text((1530, 55), f"SON {days} GÜN  •  {len(filtered_matches)} MAÇ", font=get_font(19, True), fill="#cbd5e1", anchor="ra")

    # Tablo Başlıkları
    columns = [
        ("#", 60), ("OYUNCU", 100), ("MEV", 350), ("MAÇ", 420),
        ("ORT RYT", 500), ("GOL", 620), ("AST", 710), ("2.AST", 800),
        ("K.PAS", 890), ("AR.GİR", 990), ("ÇALIM", 1100),
        ("PAS İSAB.", 1210), ("MÜD.", 1380), ("MVP", 1490)
    ]

    panel(d, (30, 135, 1570, 180), radius=10, fill=(25, 30, 45, 235), outline="#30394c")
    for title, x in columns:
        col_color = "#25f3a2" if title == "OYUNCU" else "#d4dbea"
        d.text((x, 147), title, font=get_font(13, True), fill=col_color)

    # Satırlar
    for i, p in enumerate(leaderboard[:14]):
        y = 195 + i * 47
        bg = (10, 80, 55, 175) if i == 0 else ((13, 17, 29, 210) if i % 2 else (16, 20, 33, 190))
        outline_col = (37, 243, 162, 120) if i == 0 else (60, 70, 90, 70)
        d.rounded_rectangle((30, y, 1570, y + 40), radius=8, fill=bg, outline=outline_col, width=1)

        pass_str = f"{p['passes_made']}/{p['pass_attempts']} ({p['pass_pct']}%)"
        vals = [
            str(i + 1), p["name"][:18], p["pos"], str(p["matches"]),
            f"{p['avg_rating']:.2f}", str(p["goals"]), str(p["assists"]),
            str(p["second_assists"]), str(p["key_passes"]), str(p["interceptions"]),
            str(p["dribbles"]), pass_str, str(p["tackles_won"]), str(p["moms"])
        ]

        for (title, x), val_text in zip(columns, vals):
            color = "#25f3a2" if (title in ("ORT RYT", "OYUNCU") and i == 0) else "#ffffff"
            f_bold = True if title in ("ORT RYT", "OYUNCU", "#") else False
            d.text((x, y + 11), val_text, font=get_font(13, f_bold), fill=color)

    d.text((35, 864), "GS  GraveShift Clubs Bot", font=get_font(15, True), fill="#25f3a2")
    d.text((1560, 864), f"FİLTRE: {target_type}  •  SIRALAMA KRİTERİ: ORTALAMA REYTİNG", font=get_font(11, True), fill="#7f8ca3", anchor="ra")

    out_file = (REPORTS_DIR / f"leaderboard_{target_type}_{datetime.utcnow().strftime('%Y%m%d')}.png").resolve()
    im.save(str(out_file), format="PNG")
    print(f"\n[OK] Liderlik tablosu üretildi -> {out_file.name}")
    os.startfile(str(out_file))
    return out_file

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "leagueMatch"
    generate_leaderboard(target_type=mode, days=30)