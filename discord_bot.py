from datetime import datetime
import sys
import os
from pathlib import Path
import discord
from discord.ext import commands, tasks
import test_advanced_card
import generate_monthly_report

CHANNEL_ID = 1566022618115604580

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

LAST_SEEN_MATCH_ID = None

def get_match_time(match_row):
    ts = match_row.get("timestamp")
    if isinstance(ts, datetime):
        return int(ts.timestamp())
    if isinstance(ts, (int, float)):
        return int(ts)
    if isinstance(ts, str) and ts.isdigit():
        return int(ts)
    mid = match_row.get("matchId")
    if isinstance(mid, (int, float)):
        return int(mid)
    if isinstance(mid, str) and mid.isdigit():
        return int(mid)
    return 0


@bot.event
async def on_ready():
    print(f"[BOT AKTIF] {bot.user} basariyla Discord'a baglandi!")
    if not check_new_matches.is_running():
        check_new_matches.start()
        print("[TAKIP] Otomatik mac takip dongusu baslatildi.")

@bot.command(name="sonmac")
async def cmd_sonmac(ctx):
    try:
        candidates = []
        for kind in ["leagueMatch", "playoffMatch", "friendlyMatch"]:
            try:
                rows = test_advanced_card.api.get_club_matches(test_advanced_card.CLUB_ID, match_type=kind, count=3) or []
                for row in rows:
                    candidates.append((row, kind))
            except Exception:
                pass

        if not candidates:
            await ctx.send("❌ Son oynanan mac bulunamadi.")
            return

        candidates.sort(key=lambda x: get_match_time(x[0]), reverse=True)
        match, match_type_used = candidates[0]

        players = test_advanced_card.api.get_match_players(
            test_advanced_card.CLUB_ID, match_type=match_type_used, count=3,
            both_teams=False, include_events=True, all_columns=True
        ) or []

        img_path = test_advanced_card.build_pro_match_card(match, players)

        import glob
        if not img_path or not os.path.exists(str(img_path)):
            all_pngs = glob.glob('reports/*.png') + glob.glob('*.png')
            if all_pngs:
                img_path = max(all_pngs, key=os.path.getmtime)
        with open(img_path, "rb") as f:
            picture = discord.File(f)
            await ctx.send(content=f"📊 **Son Mac Raporu** (ID: {match.get('matchId')})", file=picture)

    except Exception as e:
        await ctx.send(f"⚠️ Hata olustu: {e}")

@bot.command(name="aylik")
async def cmd_aylik(ctx, tur: str = "lig"):
    try:
        await ctx.send(f"⏳ Aylik rapor ({tur}) hazirlaniyor...")
    except Exception as e:
        await ctx.send(f"⚠️ Hata: {e}")

@tasks.loop(minutes=2)
async def check_new_matches():
    global LAST_SEEN_MATCH_ID
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            return

        candidates = []
        for kind in ["leagueMatch", "playoffMatch", "friendlyMatch"]:
            try:
                rows = test_advanced_card.api.get_club_matches(test_advanced_card.CLUB_ID, match_type=kind, count=2) or []
                for row in rows:
                    candidates.append((row, kind))
            except Exception:
                pass

        if not candidates:
            return

        candidates.sort(key=lambda x: get_match_time(x[0]), reverse=True)
        latest_match, match_type_used = candidates[0]
        latest_id = str(latest_match.get("matchId"))

        if LAST_SEEN_MATCH_ID is None:
            LAST_SEEN_MATCH_ID = latest_id
            print(f"[TAKIP] Ilk baslatma: Son mac ID ({latest_id}) kaydedildi. Yeni mac bekleniyor...")
            return

        if latest_id != LAST_SEEN_MATCH_ID:
            print(f"[YENI MAC] Yeni mac tespit edildi! ID: {latest_id}")
            LAST_SEEN_MATCH_ID = latest_id

            players = test_advanced_card.api.get_match_players(
                test_advanced_card.CLUB_ID, match_type=match_type_used, count=3,
                both_teams=False, include_events=True, all_columns=True
            ) or []

            img_path = test_advanced_card.build_pro_match_card(latest_match, players)
            if not img_path or not os.path.exists(str(img_path)):
                all_pngs = glob.glob('reports/*.png')
                if all_pngs:
                    img_path = max(all_pngs, key=os.path.getmtime)

            import glob
        if not img_path or not os.path.exists(str(img_path)):
            all_pngs = glob.glob('reports/*.png') + glob.glob('*.png')
            if all_pngs:
                img_path = max(all_pngs, key=os.path.getmtime)
        with open(img_path, "rb") as f:
            picture = discord.File(f)
            await channel.send(content=f"🔔 **Yeni Mac Tamamlandi!** (ID: {latest_id})", file=picture)
            print("[TAKIP] Yeni mac gorseli basariyla kanala yuklendi.")

    except Exception as e:
        print(f"[HATA - Otomatik Takip]: {e}")

@check_new_matches.before_loop
async def before_check_new_matches():
    await bot.wait_until_ready()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    token_file = Path("token.txt")
    if token_file.exists():
        TOKEN = token_file.read_text(encoding="utf-8").strip()

if not TOKEN:
    print("HATA: Bot tokeni bulunamadi. token.txt dosyasini veya DISCORD_BOT_TOKEN ortam degiskenini kontrol edin.")
    sys.exit(1)

bot.run(TOKEN)

