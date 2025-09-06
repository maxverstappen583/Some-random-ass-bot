# bot.py
# Single-file Discord bot with:
# - Prefix command: !plans
# - Slash command: /plans
# - Flask keep-alive (for uptime pings)
# - Loads token from .env
#
# Requirements: discord.py>=2.x, python-dotenv, flask

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# -------------------------
# Load configuration
# -------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")            # REQUIRED
GUILD_ID = os.getenv("DISCORD_GUILD_ID")      # optional (use for instant slash-command registration)
PORT = int(os.getenv("PORT", 8080))           # optional, default 8080 for Flask

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env — please add DISCORD_TOKEN=your_token_here")

# Convert GUILD_ID to int if present
if GUILD_ID:
    try:
        GUILD_ID = int(GUILD_ID)
    except ValueError:
        print("WARN: DISCORD_GUILD_ID is set but not an integer. Ignoring (will register global commands).")
        GUILD_ID = None

# -------------------------
# Flask keep-alive (for uptime monitors)
# -------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    # When hosting platforms use $PORT, Flask will bind to it
    app.run(host="0.0.0.0", port=PORT)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# -------------------------
# Discord bot setup
# -------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def create_plans_embed():
    embed = discord.Embed(
        title="⚖️ Free vs Premium Bots",
        description="Choose the perfect plan for your custom bot.\nBoth are hosted by me and fully private to you. 🌟",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🌟 Free Bot",
        value=(
            "✅ 100% Free\n"
            "🔟 Up to 10 commands only\n"
            "🖥 Free hosting included\n"
            "🔒 Private & unique bot\n"
            "📩 Basic support\n"
            "⚙️ Standard features"
        ),
        inline=True
    )

    embed.add_field(
        name="🚀 Premium Bot",
        value=(
            "💎 Paid (one-time or custom deal)\n"
            "♾️ Unlimited commands\n"
            "⚡ Priority hosting included\n"
            "👑 Private & unique bot\n"
            "🤝 Priority support\n"
            "🔥 Advanced systems & features"
        ),
        inline=True
    )

    embed.set_footer(text="Contact me on Discord → [your username here]")
    return embed

# -------------------------
# Prefix command (!plans)
# -------------------------
@bot.command(name="plans")
@commands.cooldown(1, 3, commands.BucketType.user)  # small safety cooldown
async def plans_cmd(ctx: commands.Context):
    """Send the Free vs Premium embed (prefix command)."""
    await ctx.send(embed=create_plans_embed())

# -------------------------
# Slash command (/plans)
# -------------------------
@bot.tree.command(name="plans", description="Show Free vs Premium plans")
async def plans_slash(interaction: discord.Interaction):
    """Send the Free vs Premium embed (slash command)."""
    await interaction.response.send_message(embed=create_plans_embed())

# -------------------------
# Events & command sync
# -------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id}) — ready!")
    try:
        if GUILD_ID:
            # Sync commands to a single guild for near-instant availability
            guild = discord.Object(id=GUILD_ID)
            await bot.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {GUILD_ID} (instant).")
        else:
            # Global sync (can take up to an hour to appear)
            await bot.tree.sync()
            print("Global slash commands synced (may take up to 1 hour to appear).")
    except Exception as e:
        print("Failed to sync slash commands:", e)

@bot.event
async def on_command_error(ctx, error):
    # Basic error handling for prefix commands
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"Command on cooldown. Try again in {round(error.retry_after,1)}s.", mention_author=False)
    else:
        # Log other errors to console and optionally notify user
        print(f"Error in command `{ctx.command}`: {error}")
        # Keep user messages friendly but not too verbose
        await ctx.reply("An error occurred while running that command.", mention_author=False)

# -------------------------
# Start everything
# -------------------------
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
