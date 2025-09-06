import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Flask app for uptime pings
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Discord bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.command()
async def plans(ctx):
    embed = discord.Embed(
        title="⚖️ Free vs Premium Bots",
        description="Choose the perfect plan for your custom bot.\nBoth are hosted by me and fully private to you. 🌟",
        color=discord.Color.blue()
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

    await ctx.send(embed=embed)

# Start Flask + Bot
keep_alive()
bot.run(TOKEN)
