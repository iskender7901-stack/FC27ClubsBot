import os
import glob
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_names = ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
    if bold:
        font_names = ["segouib.ttf", "arialbd.ttf", "calibrib.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def create_match_card(match: dict, players: list) -> str:
    os.makedirs("reports", exist_ok=True)
    match_id = str(match.get("matchId") or match.get("id") or "sonmac")
    output_path = os.path.join("reports", f"match_{match_id}.png")

    W, H = 1000, 650
    img = Image.new("RGBA", (W, H), (15, 18, 26, 255))
    draw = ImageDraw.Draw(img)

    # Arka plan gradyanı / panel efekti
    draw.rounded_rectangle([20, 20, W - 20, H - 20], radius=16, fill=(24, 28, 40, 240), outline=(0, 255, 150, 180), width=2)
    
    font_title = get_font(26, bold=True)
    font_sub = get_font(16, bold=False)
    font_header = get_font(14, bold=True)
    font_row = get_font(13, bold=False)

    # Başlık Alanı
    draw.text((40, 40), "PRO CLUBS MATCH REPORT", font=font_title, fill=(0, 255, 150))
    clubs_info = match.get("clubs", {})
    club_names = list(clubs_info.keys()) if isinstance(clubs_info, dict) else []
    
    score_text = "SKOR BİLGİSİ ALINAMADI"
    if len(club_names) >= 2:
        c1 = clubs_info.get(club_names[0], {})
        c2 = clubs_info.get(club_names[1], {})
        score_text = f"{c1.get('details', {}).get('name', 'Ev Sahibi')}  {c1.get('goals', 0)} - {c2.get('goals', 0)}  {c2.get('details', {}).get('name', 'Deplasman')}"
    elif match.get("result"):
        score_text = f"Sonuç: {match.get('result')}"

    draw.text((40, 75), score_text, font=font_sub, fill=(220, 225, 235))
    draw.line([(40, 110), (W - 40, 110)], fill=(45, 55, 75), width=2)

    # Tablo Başlıkları
    headers = [("OYUNCU", 50), ("POZ", 240), ("REY", 300), ("GOL", 360), ("AST", 420), ("ŞUT", 480), ("PAS %", 550), ("MÜD", 630), ("KURT", 710)]
    for text, x in headers:
        draw.text((x, 125), text, font=font_header, fill=(0, 255, 150))

    draw.line([(40, 150), (W - 40, 150)], fill=(45, 55, 75), width=1)

    # Oyuncu Satırları
    y = 165
    for p in players[:10]:
        name = str(p.get("playername") or p.get("name") or "Oyuncu")[:16]
        pos = str(p.get("pos") or p.get("position") or "-").upper()
        rating = str(p.get("rating") or p.get("score") or "6.0")
        goals = str(p.get("goals") or "0")
        assists = str(p.get("assists") or "0")
        shots = str(p.get("shots") or "0")
        passes = f"{p.get('passsuccesspct') or p.get('pass_accuracy') or '0'}%"
        tackles = str(p.get("tacklesmade") or p.get("tackles") or "0")
        saves = str(p.get("saves") or "0")

        # Pozisyona göre renklendirme
        pos_color = (0, 200, 255) if pos in ["GK", "KALECI"] else (220, 225, 235)

        draw.text((50, y), name, font=font_row, fill=(255, 255, 255))
        draw.text((240, y), pos, font=font_row, fill=pos_color)
        draw.text((300, y), rating, font=font_row, fill=(255, 215, 0))
        draw.text((360, y), goals, font=font_row, fill=(220, 225, 235))
        draw.text((420, y), assists, font=font_row, fill=(220, 225, 235))
        draw.text((480, y), shots, font=font_row, fill=(220, 225, 235))
        draw.text((550, y), passes, font=font_row, fill=(220, 225, 235))
        draw.text((630, y), tackles, font=font_row, fill=(220, 225, 235))
        draw.text((710, y), saves, font=font_row, fill=(0, 255, 150) if pos in ["GK", "KALECI"] else (120, 130, 145))

        y += 35
        if y > H - 80:
            break

    # Alt Bilgi
    draw.line([(40, H - 60), (W - 40, H - 60)], fill=(45, 55, 75), width=1)
    draw.text((40, H - 45), f"Match ID: {match_id} | FC27 ANALİZ", font=get_font(12), fill=(130, 140, 160))

    img.save(output_path, "PNG")
    print("Maç görseli:", output_path)
    return str(output_path)
