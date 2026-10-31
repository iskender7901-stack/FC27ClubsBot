"""Create a styled FC 27 Pro Clubs match report with player and team statistics."""
import sys
import os
import io
import urllib.request
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fc_clubs_api import FC27API

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

CLUB_ID = 87430
OUT = Path(__file__).resolve().parent / "reports"
OUT.mkdir(parents=True, exist_ok=True)
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

def fetch_image(url: str, size=(100, 100)) -> Image.Image:
    if not url:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            img = Image.open(io.BytesIO(response.read())).convert("RGBA")
            return img.resize(size, Image.Resampling.LANCZOS)
    except Exception:
        return Image.new("RGBA", size, (0, 0, 0, 0))

def panel(draw, xy, radius=16, fill="#0b111c", outline="#263247", width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def match_rows(players, match):
    match_id = str(val(match, "matchId", default=""))
    return [p for p in players if str(val(p, "matchId", default="")) == match_id]

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

def team_stats(rows):
    shots = sum(number(p, "shots") for p in rows)
    passes = sum(number(p, "passesmade", "passesCompleted") for p in rows)
    attempts = sum(number(p, "passattempts") for p in rows)
    tackles = sum(number(p, "tacklesmade", "cleanTackles", "tacklesWon") for p in rows)
    dribbles = sum(number(p, "dribblesBeat") + number(p, "dribblesCompleted") + number(p, "dribblesSkillMoveBeat") for p in rows)
    interceptions = sum(number(p, "interceptions") + number(p, "opponentsDispossessed") for p in rows)
    assists = sum(number(p, "assists") for p in rows)
    second_assists = sum(number(p, "secondAssists") for p in rows)
    accuracy = round(passes / attempts * 100) if attempts else 0
    return {
        "ŞUTLAR": int(shots),
        "PASLAR": int(passes),
        "PAS İSABETİ": f"{accuracy}%",
        "MÜDAHALE": int(tackles),
        "ÇALIM": int(dribbles),
        "ARAYA GİRME": int(interceptions),
        "ASİST": int(assists),
        "2. ASİST": int(second_assists),
    }

def build_pro_match_card(match: dict, players: list):
    os.makedirs("reports", exist_ok=True)
    match_id = str(val(match, "matchId", default="sonmac"))
    output_path = os.path.join("reports", f"match_{match_id}.png")

    # Kendi kulübümüzün oyuncularını filtrele
    my_club_id = str(val(match, "clubId", default="")) or (str(CLUB_ID) if 'CLUB_ID' in globals() else "")
    if my_club_id:
        filtered = [p for p in players if str(p.get("clubId") or p.get("teamId") or "") in [my_club_id, ""]]
        if filtered:
            players = filtered

    rows = match_rows(players, match) if 'match_rows' in globals() else players
    if not rows and players:
        rows = players

    W, H = 1200, 950
    img = Image.new("RGBA", (W, H), "#070b12")
    draw = ImageDraw.Draw(img)

    # Ana Çerçeve ve Üst Header
    panel(draw, [20, 20, W - 20, H - 20], radius=18, fill="#0b111c", outline="#1c2738", width=2)
    panel(draw, [20, 20, W - 20, 130], radius=18, fill="#101826", outline="#1c2738", width=1)

    f_title = get_font(30, bold=True)
    f_sub = get_font(18, bold=True)
    f_head = get_font(13, bold=True)
    f_row = get_font(14, bold=False)
    f_row_b = get_font(14, bold=True)
    f_stat_lbl = get_font(11, bold=True)
    f_stat_val = get_font(18, bold=True)

    draw.text((45, 36), "FC27 PRO CLUBS", font=f_title, fill="#ffffff")
    draw.text((290, 36), "MATCH REPORT", font=f_title, fill="#00ff8c")

    # Kulüp İsimleri, Skor ve Sonuç
    c_name = str(match.get("clubName") or "Takımımız")
    opp_name = str(match.get("opponentName") or "Rakip Takım")
    goals = match.get("goals", 0)
    goals_against = match.get("goalsAgainst", 0)
    res_raw = str(match.get("result", "")).lower()
    res_tr = "GALİBİYET" if "win" in res_raw else ("MAĞLUBİYET" if "loss" in res_raw else "BERABERLİK")

    score_txt = f"{c_name}  {goals} - {goals_against}  {opp_name}   |   {res_tr}"
    draw.text((45, 82), score_txt, font=f_sub, fill="#ffffff")

    # Tablo Başlıkları
    headers = [("POZ", 50), ("OYUNCU", 130), ("REY", 330), ("GOL", 410), ("AST", 480), ("ŞUT", 550), ("PAS % (B/T)", 620), ("MÜD", 820), ("KURT", 960)]
    panel(draw, [35, 142, W - 35, 178], radius=6, fill="#0f1623", outline="#1c2738", width=1)
    for t, x in headers:
        draw.text((x, 150), t, font=f_head, fill="#00ff8c")

    # Maçın Adamını Belirle (En yüksek reyting)
    def get_rating(r):
        try:
            return float(r.get("rating") or r.get("score") or 0.0)
        except:
            return 0.0

    max_rating = max([get_rating(r) for r in rows]) if rows else 0.0
    motm_found = False

    # Pozisyon Sıralaması: KL -> DF -> OS -> FV
    pos_order = {"KL": 0, "GK": 0, "DF": 1, "OS": 2, "FV": 3}
    def get_rank(r):
        p_norm = normalize_position(r.get("pos") or r.get("position") or "") if 'normalize_position' in globals() else ""
        return pos_order.get(p_norm, 9)

    sorted_rows = sorted(rows, key=get_rank)

    # İstatistik toplamları
    tot_shots = 0
    tot_passes_made = 0
    tot_passes_att = 0
    tot_tackles_made = 0
    tot_tackles_att = 0
    tot_assists = 0
    tot_saves = 0

    # Oyuncu Satırları
    y = 192
    for idx, r in enumerate(sorted_rows[:11]):
        if idx % 2 == 1:
            panel(draw, [35, y - 4, W - 35, y + 36], radius=6, fill="#0e1420", outline="#131b28", width=1)

        raw_name = str(r.get("playername") or r.get("name") or "Oyuncu")[:15]
        pos = normalize_position(r.get("pos") or r.get("position") or "-") if 'normalize_position' in globals() else "-"
        curr_r = get_rating(r)
        rating_str = f"{curr_r:.1f}"

        # Maçın Oyuncusu Yıldızı
        if curr_r == max_rating and max_rating > 6.0 and not motm_found:
            name = f"★ {raw_name}"
            motm_found = True
            name_color = "#facc15"
        else:
            name = raw_name
            name_color = "#f1f5f9"

        g = int(r.get("goals") or 0)
        a = int(r.get("assists") or 0)
        s = int(r.get("shots") or 0)
        pm = int(r.get("passesMade") or r.get("passesmade") or 0)
        pa = int(r.get("passAttempts") or r.get("passattempts") or 0)
        tm = int(r.get("tacklesMade") or r.get("tacklesmade") or 0)
        ta = int(r.get("tackleAttempts") or r.get("tackleattempts") or 0)
        sv = int(r.get("saves") or 0)

        tot_shots += s
        tot_assists += a
        tot_passes_made += pm
        tot_passes_att += pa
        tot_tackles_made += tm
        tot_tackles_att += ta
        tot_saves += sv

        # Seçenek 1: %78 (44/59)
        pct_num = int(round((pm / pa) * 100)) if pa > 0 else 0
        if pa > 0:
            pass_str = f"%{pct_num} ({pm}/{pa})"
        else:
            pass_str = "--"

        pos_color = "#38bdf8" if pos == "KL" else ("#facc15" if pos == "OS" else ("#4ade80" if pos == "DF" else "#f87171"))
        draw.text((50, y), pos, font=f_row_b, fill=pos_color)
        draw.text((130, y), name, font=f_row_b, fill=name_color)

        r_col = "#00ff8c" if curr_r >= 8.0 else ("#facc15" if curr_r >= 7.0 else "#94a3b8")
        draw.text((330, y), rating_str, font=f_row_b, fill=r_col)

        draw.text((410, y), str(g), font=f_row_b if g > 0 else f_row, fill="#ffffff" if g > 0 else "#64748b")
        draw.text((480, y), str(a), font=f_row_b if a > 0 else f_row, fill="#ffffff" if a > 0 else "#64748b")
        draw.text((550, y), str(s), font=f_row, fill="#cbd5e1")
        draw.text((620, y), pass_str, font=f_row, fill="#cbd5e1")
        draw.text((820, y), str(tm), font=f_row, fill="#cbd5e1")
        draw.text((960, y), str(sv), font=f_row_b if pos == "KL" else f_row, fill="#00ff8c" if pos == "KL" and sv > 0 else "#475569")

        y += 42

    # --- 8'Lİ TAKIM İSTATİSTİKLERİ PANELİ ---
    stats_y = 690
    panel(draw, [35, stats_y, W - 35, stats_y + 195], radius=12, fill="#0c121d", outline="#1c2738", width=1)

    team_pass_acc = f"%{int(round((tot_passes_made / tot_passes_att) * 100))}" if tot_passes_att > 0 else "--"

    display_stats = [
        ("TOPLAM ŞUT", str(tot_shots)),
        ("BAŞARILI PAS", str(tot_passes_made)),
        ("TOPLAM PAS", str(tot_passes_att)),
        ("PAS İSABETİ", team_pass_acc),
        ("BAŞARILI MÜD.", str(tot_tackles_made)),
        ("TOPLAM MÜD.", str(tot_tackles_att)),
        ("ASİST", str(tot_assists)),
        ("KURTARIŞ", str(tot_saves)),
    ]

    col_w = (W - 70 - 3 * 15) // 4
    row_h = 75

    for i, (lbl, val_str) in enumerate(display_stats):
        col_idx = i % 4
        row_idx = i // 4
        cx = 45 + col_idx * (col_w + 12)
        cy = stats_y + 16 + row_idx * (row_h + 12)

        panel(draw, [cx, cy, cx + col_w, cy + row_h], radius=8, fill="#111927", outline="#1a2436", width=1)
        draw.text((cx + 14, cy + 12), lbl, font=f_stat_lbl, fill="#00ff8c")
        draw.text((cx + 14, cy + 36), val_str, font=f_stat_val, fill="#ffffff")

    draw.text((45, H - 38), f"MATCH ID: {match_id}  |  FC27 ANALİZ", font=get_font(12, bold=True), fill="#475569")

    img.save(output_path, "PNG")
    return str(output_path)