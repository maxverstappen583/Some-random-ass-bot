"""
main.py — MDickie QOTD Bot (single-file)

Features:
- Single file (embedded 250-question bank)
- Flask keep-alive (useful on Render/Replit)
- Posts a daily QOTD at a server-configured time (Asia/Kolkata)
- Slash commands to configure channel/time, schedule one-off posts, force post now, preview, shuffle, list/cancel schedules, status
- Persistent JSON storage (qotd_data.json)
- Creates a thread for answers when possible
- DOS-era QOTDs excluded (none included)

Requirements:
- Python 3.9+ recommended (zoneinfo used when available)
- pip install -U discord.py flask
"""

import os
import json
import random
import asyncio
from datetime import datetime, timedelta, time as dtime, timezone
from threading import Thread

import discord
from discord.ext import commands, tasks
from discord import app_commands
from flask import Flask

# timezone: prefer zoneinfo if available
try:
    from zoneinfo import ZoneInfo
    KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    # fallback fixed offset IST
    KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30))

# ---------- Embedded question bank (250 MDickie QOTDs) ----------
QUESTIONS = [
    "What was the first MDickie game you ever played?",
    "Which MDickie game do you consider a masterpiece, and why?",
    "What’s the most iconic MDickie mechanic to you (e.g., ragdolls, dynamic dialog, sandbox chaos)?",
    "Which MDickie soundtrack track lives rent-free in your head?",
    "If you could ask Matt Dickie one dev question, what would it be?",
    "Which MDickie game has the best replay value?",
    "What’s your favorite MDickie character creator moment/feature?",
    "Which MDickie game has the funniest emergent chaos?",
    "What’s the most unexpected interaction you discovered in an MDickie game?",
    "Which MDickie game has the most memorable tutorial (or lack thereof!)?",
    "Which MDickie game do you recommend to total beginners?",
    "Mouse/keyboard, controller, or mobile—how do you play MDickie best?",
    "What small MDickie detail made you smile recently?",
    "What makes an ‘MDickie moment’ feel unique compared to other indie games?",
    "Which old MDickie title deserves a modern remaster the most?",
    "What difficulty/settings do you use for the most fun chaos?",
    "Which game’s story events surprised you the most?",
    "If MDickie made a totally new genre, what should it be?",
    "How would you describe MDickie games to someone who’s never played one?",
    "What was the biggest skill you learned from MDickie games (timing, positioning, reading AI)?",
    "Which MDickie game aged the best?",
    "Which feature do you wish appeared across *all* MDickie titles?",
    "What’s the most clutch save you’ve ever pulled off?",
    "What’s your favorite MDickie fan mod or idea?",
    "Which MDickie game’s menus/UI are the most memorable?",
    "Wrestling Empire: Which promotion do you start in and why?",
    "Wrestling Empire: Finisher you’re most proud of creating?",
    "Wrestling Empire: Most outrageous contract clause you’ve accepted?",
    "Wrestling Empire: Do you chase titles or build storylines?",
    "Wrestling Empire: Best arena you’ve fought in?",
    "Wrestling Empire: Favorite weapon spot?",
    "Wrestling Empire: Tag partner you always rely on?",
    "Wrestling Empire: Heel or face—what’s more fun?",
    "Wrestling Empire: Most chaotic backstage brawl?",
    "Wrestling Empire: Entrance theme vibe you like most?",
    "Wrestling Empire: How do you train stats efficiently?",
    "Wrestling Empire: What camera setting feels best?",
    "Wrestling Empire: Most controversial match ending you’ve seen?",
    "Wrestling Empire: Gimmick you wish existed?",
    "Wrestling Empire: Best rivalry you built from scratch?",
    "Wrestling Empire: Which move feels overpowered?",
    "Wrestling Empire: Ironman vs. Deathmatch—what’s peak fun?",
    "Wrestling Empire: Most hilarious botch that became canon in your save?",
    "Wrestling Empire: What’s your entrance pose/taunt of choice?",
    "Wrestling Empire: Best title run you’ve booked?",
    "Wrestling Empire: What’s your dream crossover match?",
    "Wrestling Empire: What slider or rule set makes matches perfect?",
    "Wrestling Empire: Favorite ref and why?",
    "Wrestling Empire: Custom arena idea you want to see?",
    "Wrestling Empire: Which real-life wrestler did you recreate the best?",
    "Hard Time: What crime did you ‘totally not’ commit?",
    "Hard Time: Best way to survive day one?",
    "Hard Time: Officer you fear/respect the most?",
    "Hard Time: Funniest cafeteria incident?",
    "Hard Time: Most broken weapon you’ve used?",
    "Hard Time: How do you deal with random fights?",
    "Hard Time: Best cellmate story?",
    "Hard Time: Do you read, train, or hustle for stats?",
    "Hard Time: What’s your go-to strategy for early freedom?",
    "Hard Time: Craziest courtroom scene outcome?",
    "Hard Time: Most valuable contraband?",
    "Hard Time: Favorite job or area in the prison?",
    "Hard Time: Have you ever run the whole prison?",
    "Hard Time: Saddest moment that hit harder than expected?",
    "Hard Time: How do you handle injury and fatigue?",
    "Hard Time: Most chaotic riot you survived?",
    "Hard Time: Role-playing a villain vs. reformed hero—what’s better?",
    "Hard Time: What rule do you actually follow?",
    "Hard Time: Favorite judge quote?",
    "Hard Time: Best improvised weapon combo?",
    "Hard Time: How often do you reset a run?",
    "Hard Time: Most dramatic escape story?",
    "Hard Time: NPC you secretly protect?",
    "Hard Time: Most unfair punishment you ate calmly?",
    "Hard Time: What mod/idea would refresh it most?",
    "School Days: Best class to slack in?",
    "School Days: Teacher who scares you straight?",
    "School Days: Funniest cafeteria throwdown?",
    "School Days: Club you always join?",
    "School Days: Best way to ace exams?",
    "School Days: Most outrageous detention reason?",
    "School Days: Favorite prank that escalated?",
    "School Days: Best way to make money in-game?",
    "School Days: Which subject do you actually role-play studying?",
    "School Days: How do you handle bullies?",
    "School Days: Coolest outfit you’ve made?",
    "School Days: Friend group archetype you run with?",
    "School Days: Most iconic classroom item?",
    "School Days: Principal meeting horror story?",
    "School Days: Best way to win fights you didn’t start?",
    "School Days: Romantic subplot chaos—yay or nay?",
    "School Days: Which teacher deserves a raise?",
    "School Days: Favorite field trip event?",
    "School Days: What gets you suspended the fastest?",
    "School Days: Most clutch exam save with low stats?",
    "School Days: Best after-school routine?",
    "School Days: Funniest line of dialog you’ve seen?",
    "School Days: Any pacifist playthroughs?",
    "School Days: Your signature class entrance?",
    "School Days: Dream spin-off feature?",
    "Extra Lives: Favorite class (human, zombie, mutant, android, etc.)?",
    "Extra Lives: Best base location?",
    "Extra Lives: What’s your apocalypse day one plan?",
    "Extra Lives: Favorite melee vs. ranged combo?",
    "Extra Lives: Which faction has the best vibes?",
    "Extra Lives: Craziest boss encounter?",
    "Extra Lives: Permadeath—on or off?",
    "Extra Lives: Most tragic companion loss?",
    "Extra Lives: Best food you found at 1 HP?",
    "Extra Lives: Nighttime strategy to survive hordes?",
    "Extra Lives: Weapon you always craft first?",
    "Extra Lives: Favorite quest chain?",
    "Extra Lives: Funniest zombie interaction?",
    "Extra Lives: Story twist that got you?",
    "Extra Lives: Ideal 3-member squad?",
    "Extra Lives: Best safe route between zones?",
    "Extra Lives: Which area creeps you out the most?",
    "Extra Lives: Which mutation perk is underrated?",
    "Extra Lives: Most cinematic moment you created?",
    "Extra Lives: What’s your endgame goal?",
    "Extra Lives: How do you ration meds and food?",
    "Extra Lives: Base defense layout tips?",
    "Extra Lives: Favorite survivor backstory?",
    "Extra Lives: NPC you always rescue?",
    "Extra Lives: Custom challenge idea?",
    "Weekend Warriors: Favorite martial art style to master?",
    "Weekend Warriors: Best training drill?",
    "Weekend Warriors: Your signature combo?",
    "Weekend Warriors: Tournament story you’re proud of?",
    "Weekend Warriors: Most intense sparring session?",
    "Weekend Warriors: What stats matter most?",
    "Super City: Favorite hero power set?",
    "Super City: Best villain arc you role-played?",
    "Super City: Coolest city location for fights?",
    "Super City: Flight vs. teleport—what’s more fun?",
    "Super City: Best costume you designed?",
    "Super City: Most chaotic civilian rescue?",
    "Super City: Rival you always keep around?",
    "Popscene: Stage you love performing on?",
    "Popscene: Best lyric you came up with?",
    "Popscene: Band drama story?",
    "Popscene: What instrument do you main?",
    "Popscene: How do you handle critics in-game?",
    "Popscene: Your album concept idea?",
    "Popscene: Best way to grow fans?",
    "Popscene: Most disastrous gig that became legendary?",
    "Popscene: Favorite producer NPC?",
    "Popscene: What genre fits Popscene best?",
    "Popscene: Merch idea that would slap?",
    "Popscene: Dream crossover with other MDickie worlds?",
    "If you were MDickie’s booking agent, what project would you pitch next?",
    "What’s your favorite emergent storyline you didn’t plan?",
    "Which NPC voice line became a meme for you?",
    "What’s a house rule you always use in MDickie games?",
    "What’s your favorite stat distribution and why?",
    "What’s a build you refuse to use because it’s too strong?",
    "What limits (injuries, rules, time) make the game better?",
    "What’s your ‘ironman’ rule set?",
    "What’s a self-imposed challenge you recommend?",
    "What’s your comfort game session length for MDickie titles?",
    "What’s the funniest bug you *want* to stay forever?",
    "What’s a QoL tweak you wish for without changing the soul?",
    "Which physics moment made you laugh out loud?",
    "What’s your favorite MDickie ‘quote’ or line delivery?",
    "What’s one mechanic you’d teach a new player first?",
    "What’s your favorite ‘zero-HUD’ or cinematic setting?",
    "What’s a crossover event you staged across games?",
    "What’s a community challenge we should try this week?",
    "What’s your go-to ‘hardcore’ save setup?",
    "What’s your soft spot MDickie character archetype?",
    "Which game handles injuries the best?",
    "Which game handles fame/reputation the best?",
    "What’s your favorite way to role-play morality swings?",
    "What’s an item you hoard for no reason?",
    "What’s your ultimate end-of-save goal across titles?",
    "Mobile or PC—where do MDickie games feel better and why?",
    "What controller layout feels most natural for you?",
    "What’s the first MDickie title you showed a friend?",
    "Which game do you revisit every year?",
    "What setting do you immediately change on a fresh save?",
    "What’s the most emotional moment you’ve had in an MDickie game?",
    "What fan theory actually makes sense?",
    "Which soundtrack deserves a live cover?",
    "What’s the best visual mod or reshade you’ve tried?",
    "What UI font/theme screams ‘MDickie’ to you?",
    "What’s your ideal save file naming scheme?",
    "What’s a perfect 20-minute MDickie session for you?",
    "What’s the longest single session you’ve done?",
    "What would a ‘photo mode’ add to your playstyle?",
    "What’s a city/setting you want MDickie to explore?",
    "Which historical era would fit an MDickie sandbox?",
    "What feature would help content creators the most?",
    "What’s the coolest community creation you’ve seen?",
    "What’s a *tiny* tweak that would make you cheer?",
    "What’s an accessibility feature you’d love added?",
    "What’s your favorite easter egg across the games?",
    "Which UI sound effect is peak nostalgia?",
    "What’s an item you wish returned across titles?",
    "Which NPC archetype needs a buff?",
    "What’s the most cinematic fight you staged?",
    "If you balanced one stat globally, which would it be?",
    "Which AI behavior feels the most human?",
    "What’s a bug that became a beloved feature?",
    "What core pillar defines MDickie design for you?",
    "What’s a risk MDickie took that paid off?",
    "What would a co-op focused MDickie title look like?",
    "What would a roguelike MDickie game change?",
    "What’s a UI/UX pattern MDickie nails?",
    "What’s a UI/UX pain you forgive because the game rules?",
    "How should tutorials be handled in MDickie style?",
    "What’s the best fail-state lesson you learned?",
    "How important are physics to the fun?",
    "What’s your stance on realism vs. fun in MDickie worlds?",
    "If you removed one mechanic from a game, which and why?",
    "What’s a resource economy idea you want to test?",
    "How would you rework injuries/fatigue across titles?",
    "What’s your dream dynamic soundtrack behavior?",
    "How do you feel about permadeath in MDickie games?",
    "What’s the ideal save scumming rule for you?",
    "Which MDickie UI needs a 2025 glow-up most?",
    "What pacing trick keeps you hooked?",
    "What’s your ideal difficulty curve?",
    "What’s one meta that new players sleep on?",
    "If MDickie did DLC, what would be perfect?",
    "What would a photojournalist MDickie game be like?",
    "Which MDickie meme always cracks you up?",
    "What’s your proudest clip you’ve recorded?",
    "Share a tip that helped you ‘get it’. What was it?",
    "What’s your favorite community challenge we’ve done?",
    "What’s a weekly theme we should run next month?",
    "Who’s your MDickie doubles partner (another player)?",
    "What’s your best ‘I can’t believe that worked’ story?",
    "Which NPC name makes you grin every time?",
    "What’s the most ridiculous outfit you’ve seen?",
    "What’s a wholesome moment you witnessed?",
    "What’s an MDickie hill you’ll die on?",
    "What’s your favorite control remap?",
    "What’s your go-to celebration/emote after a win?",
    "What’s your favorite MDickie quote to spam?",
    "What’s the best clip you’ve seen from someone else?",
    "What in-game day felt like a movie?",
    "What’s the best use of props you’ve pulled off?",
    "What’s your favorite low-stat underdog story?",
    "What’s one habit you had to unlearn to get better?",
    "What’s a challenge you want the server to try tomorrow?",
    "What’s your ‘perfect match’ setup?",
    "What song would you assign to your main character?",
    "What’s your favorite menu you’d print on a T-shirt?",
    "What crossover mod idea would break the internet?",
    "If you could cameo in one MDickie game, which and doing what?"
]

# ---------- Data file ----------
DATA_FILE = "qotd_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"guilds": {}}
        save_data(data)
        return data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"guilds": {}}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def ensure_guild(data, gid_str):
    g = data["guilds"].setdefault(gid_str, {
        "channel_id": None,
        "time_hhmm": "21:00",
        "enabled": False,
        "current_index": 0,
        "one_shot_schedules": [],
        "last_post_date": None,
        "order": None
    })
    g.setdefault("one_shot_schedules", [])
    return g

def parse_hhmm(hhmm: str):
    parts = hhmm.split(":")
    if len(parts) != 2:
        raise ValueError("Invalid time format")
    h = int(parts[0]); m = int(parts[1])
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError("Hour/minute out of range")
    return h, m

def next_run_dt(now_k: datetime, hhmm: str) -> datetime:
    h, m = parse_hhmm(hhmm)
    candidate = now_k.replace(hour=h, minute=m, second=0, microsecond=0)
    if candidate <= now_k:
        candidate += timedelta(days=1)
    return candidate

# ---------- Flask keep-alive ----------
app = Flask("qotd_keepalive")

@app.route("/")
def index():
    return "MDickie QOTD Bot — alive!"

def _run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def start_keepalive():
    t = Thread(target=_run_flask, daemon=True)
    t.start()

# ---------- Discord bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
DATA = load_data()

async def post_qotd(guild_id: int, q_idx_override=None):
    gid = str(guild_id)
    g = DATA["guilds"].get(gid)
    if not g or not g.get("channel_id"):
        return
    channel = bot.get_channel(g["channel_id"])
    if channel is None:
        return

    pool = list(QUESTIONS)  # DOS-era excluded
    if not pool:
        return

    q_text = None
    order = g.get("order")
    if q_idx_override is not None:
        idx = int(q_idx_override) % len(pool)
        q_text = pool[idx]
    else:
        if order and isinstance(order, list) and len(order) == len(pool):
            cur = int(g.get("current_index", 0)) % len(order)
            pool_idx = order[cur]
            q_text = pool[pool_idx]
            g["current_index"] = (cur + 1) % len(order)
        else:
            cur = int(g.get("current_index", 0)) % len(pool)
            q_text = pool[cur]
            g["current_index"] = (cur + 1) % len(pool)

    embed = discord.Embed(title="🗓️ MDickie QOTD", description=q_text, color=discord.Color.blurple())
    embed.set_footer(text="Answer below! A thread will be created for answers when possible.")
    try:
        sent = await channel.send(embed=embed)
        try:
            await sent.create_thread(name="QOTD Answers", auto_archive_duration=60)
        except Exception:
            pass
        DATA["guilds"][gid] = g
        save_data(DATA)
    except Exception as e:
        print(f"[post_qotd] failed for guild {guild_id}: {e}")

# Scheduler: checks every 15s
@tasks.loop(seconds=15.0)
async def scheduler_loop():
    now_k = datetime.now(KOLKATA_TZ)
    today_iso = now_k.date().isoformat()
    for gid_str, g in list(DATA["guilds"].items()):
        # one-shot schedules
        remaining = []
        for s in g.get("one_shot_schedules", []):
            run_at_iso = s.get("run_at")
            try:
                dt = datetime.fromisoformat(run_at_iso)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=KOLKATA_TZ)
            except Exception:
                # skip malformed
                continue
            if now_k >= dt:
                await post_qotd(int(gid_str), q_idx_override=s.get("q_idx"))
            else:
                remaining.append(s)
        if len(remaining) != len(g.get("one_shot_schedules", [])):
            g["one_shot_schedules"] = remaining
            DATA["guilds"][gid_str] = g
            save_data(DATA)

        # daily posting (avoid duplicates)
        if g.get("enabled") and g.get("time_hhmm") and g.get("channel_id"):
            try:
                h, m = parse_hhmm(g["time_hhmm"])
                if now_k.hour == h and now_k.minute == m:
                    if g.get("last_post_date") != today_iso:
                        await post_qotd(int(gid_str))
                        g["last_post_date"] = today_iso
                        DATA["guilds"][gid_str] = g
                        save_data(DATA)
            except Exception:
                continue

@scheduler_loop.before_loop
async def before_scheduler():
    await bot.wait_until_ready()

# ---------- Slash command group ----------
@app_commands.default_permissions(manage_guild=True)
class QOTDGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="qotd", description="Configure MDickie QOTD (Manage Server required)")

    @app_commands.command(name="set_channel", description="Set the channel for QOTD posts")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        gid = str(interaction.guild_id)
        ensure_guild(DATA, gid)
        DATA["guilds"][gid]["channel_id"] = channel.id
        save_data(DATA)
        await interaction.response.send_message(f"✅ QOTD channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="set_time", description="Set daily QOTD time (Asia/Kolkata) in HH:MM (24h)")
    async def set_time(self, interaction: discord.Interaction, hhmm: str):
        try:
            parse_hhmm(hhmm)
        except Exception:
            await interaction.response.send_message("❌ Invalid time. Use HH:MM (24-hour), e.g. 21:00.", ephemeral=True)
            return
        gid = str(interaction.guild_id)
        ensure_guild(DATA, gid)
        DATA["guilds"][gid]["time_hhmm"] = hhmm
        DATA["guilds"][gid]["last_post_date"] = None
        save_data(DATA)
        await interaction.response.send_message(f"✅ Daily QOTD time set to **{hhmm} (Asia/Kolkata)**", ephemeral=True)

    @app_commands.command(name="start", description="Enable daily QOTD posting")
    async def start(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        ensure_guild(DATA, gid)
        if not DATA["guilds"][gid].get("channel_id"):
            await interaction.response.send_message("❌ Set a QOTD channel first with `/qotd set_channel`.", ephemeral=True)
            return
        DATA["guilds"][gid]["enabled"] = True
        save_data(DATA)
        await interaction.response.send_message("✅ Daily QOTD enabled.", ephemeral=True)

    @app_commands.command(name="stop", description="Disable daily QOTD posting")
    async def stop(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        ensure_guild(DATA, gid)
        DATA["guilds"][gid]["enabled"] = False
        save_data(DATA)
        await interaction.response.send_message("⏸️ Daily QOTD disabled.", ephemeral=True)

    @app_commands.command(name="schedule_once", description="Schedule a one-time QOTD at HH:MM (Asia/Kolkata). Optional question index (1..250).")
    async def schedule_once(self, interaction: discord.Interaction, hhmm: str, q_index: int = None):
        gid = str(interaction.guild_id)
        g = ensure_guild(DATA, gid)
        if not g.get("channel_id"):
            await interaction.response.send_message("❌ Set a QOTD channel first with `/qotd set_channel`.", ephemeral=True)
            return
        try:
            target = next_run_dt(datetime.now(KOLKATA_TZ), hhmm)
        except Exception:
            await interaction.response.send_message("❌ Invalid time format. Use HH:MM.", ephemeral=True)
            return
        entry = {"run_at": target.isoformat(), "q_idx": None}
        if q_index is not None:
            entry["q_idx"] = max(0, min(len(QUESTIONS) - 1, int(q_index) - 1))
        g.setdefault("one_shot_schedules", []).append(entry)
        DATA["guilds"][gid] = g
        save_data(DATA)
        await interaction.response.send_message(f"🗓️ One-time QOTD scheduled for **{target.strftime('%Y-%m-%d %H:%M %Z')}**", ephemeral=True)

    @app_commands.command(name="list_schedules", description="List upcoming one-time QOTD schedules")
    async def list_schedules(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        g = DATA["guilds"].get(gid, {})
        schedules = g.get("one_shot_schedules", [])
        if not schedules:
            await interaction.response.send_message("No one-time QOTD schedules.", ephemeral=True)
            return
        lines = []
        for i, s in enumerate(schedules, start=1):
            run_at = s.get("run_at")
            qidx = s.get("q_idx")
            try:
                dt = datetime.fromisoformat(run_at)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=KOLKATA_TZ)
                when = dt.strftime("%Y-%m-%d %H:%M %Z")
            except Exception:
                when = str(run_at)
            if qidx is not None:
                lines.append(f"**{i}.** {when} — question #{qidx+1}")
            else:
                lines.append(f"**{i}.** {when} — next in order")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="cancel_schedule", description="Cancel a one-time schedule by its number from /qotd list_schedules")
    async def cancel_schedule(self, interaction: discord.Interaction, index: int):
        gid = str(interaction.guild_id)
        g = DATA["guilds"].get(gid, {})
        schedules = g.get("one_shot_schedules", [])
        if not schedules or index < 1 or index > len(schedules):
            await interaction.response.send_message("❌ Invalid schedule index.", ephemeral=True)
            return
        schedules.pop(index - 1)
        g["one_shot_schedules"] = schedules
        DATA["guilds"][gid] = g
        save_data(DATA)
        await interaction.response.send_message("✅ Schedule removed.", ephemeral=True)

    @app_commands.command(name="next_now", description="Post the next QOTD immediately")
    async def next_now(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        g = DATA["guilds"].get(gid)
        if not g or not g.get("channel_id"):
            await interaction.response.send_message("❌ Set a QOTD channel first with `/qotd set_channel`.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=False)
        await post_qotd(int(gid))
        await interaction.followup.send("✅ QOTD posted.", ephemeral=True)

    @app_commands.command(name="preview", description="Preview the next QOTD without posting")
    async def preview(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        g = ensure_guild(DATA, gid)
        pool = list(QUESTIONS)
        if not pool:
            await interaction.response.send_message("No questions available.", ephemeral=True)
            return
        order = g.get("order")
        if order and isinstance(order, list) and len(order) == len(pool):
            idx = int(g.get("current_index", 0)) % len(order)
            q = pool[order[idx]]
        else:
            idx = int(g.get("current_index", 0)) % len(pool)
            q = pool[idx]
        await interaction.response.send_message(embed=discord.Embed(title="Preview MDickie QOTD", description=q), ephemeral=True)

    @app_commands.command(name="shuffle", description="Shuffle the order of upcoming questions")
    async def shuffle(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        g = ensure_guild(DATA, gid)
        pool_len = len(QUESTIONS)
        order = list(range(pool_len))
        random.shuffle(order)
        g["order"] = order
        g["current_index"] = 0
        DATA["guilds"][gid] = g
        save_data(DATA)
        await interaction.response.send_message("🔀 Shuffled question order.", ephemeral=True)

    @app_commands.command(name="status", description="Show QOTD configuration for this server")
    async def status(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        g = DATA["guilds"].get(gid, {})
        ch = f"<#{g.get('channel_id')}>" if g.get("channel_id") else "Not set"
        time_str = g.get("time_hhmm", "Not set")
        enabled = "On" if g.get("enabled") else "Off"
        idx = int(g.get("current_index", 0)) + 1
        total = len(QUESTIONS)
        pending = len(g.get("one_shot_schedules", []))
        await interaction.response.send_message(
            f"**MDickie QOTD Status**\n• Channel: {ch}\n• Time (Asia/Kolkata): **{time_str}**\n• Enabled: **{enabled}**\n• Next index: **{idx}/{total}**\n• One-time schedules: **{pending}**",
            ephemeral=True
        )

# register group
bot.tree.add_command(QOTDGroup())

# ---------- Events ----------
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception:
        pass
    if not scheduler_loop.is_running():
        scheduler_loop.start()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# ---------- Entrypoint ----------
def main():
    start_keepalive()
    token = os.getenv("DISCORD_BOT_TOKEN", None)
    if not token:
        print("ERROR: set DISCORD_BOT_TOKEN environment variable (or edit main.py to include it).")
        return
    bot.run(token)

if __name__ == "__main__":
    main()
