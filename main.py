import os
import asyncio
from datetime import date, datetime, time, timedelta
from discord.ext import commands
from discord import app_commands, Game
from dotenv import load_dotenv
import pytz
import math
import random

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
START_DATE_FILE = "start_date.txt"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Singapore")

bot = commands.Bot(command_prefix="!", intents=None)
tz = pytz.timezone(TIMEZONE)

# A list of cute kaomoji to randomly use each update
KAOMOJIS = [
    "(⁄⁄>⁄▽⁄<⁄⁄)", "(˶ˆ꒳ˆ˵)", "(≧◡≦)", "(♡˙︶˙♡)", "(๑˃̵ᴗ˂̵)ﻭ", "(⁄ ⁄•⁄ω⁄•⁄ ⁄)", "(≧ω≦)", "(づ￣ ³￣)づ"
]


# --- Helper functions ---
def load_start_date():
    if os.path.exists(START_DATE_FILE):
        with open(START_DATE_FILE, "r") as f:
            return datetime.strptime(f.read().strip(), "%Y-%m-%d").date()
    else:
        default_date = datetime.strptime(os.getenv("START_DATE"), "%Y-%m-%d").date()
        return default_date


def save_start_date(new_date: date):
    with open(START_DATE_FILE, "w") as f:
        f.write(new_date.strftime("%Y-%m-%d"))


def get_days_and_months():
    start_date = load_start_date()
    today = date.today()
    days_passed = (today - start_date).days
    months_passed = math.floor(days_passed / 30.4375)  # average days per month
    return days_passed, months_passed


async def update_nickname(mode="days"):
    guild = bot.get_guild(GUILD_ID)
    if guild:
        days, months = get_days_and_months()
        kaomoji = random.choice(KAOMOJIS)

        if mode == "days":
            new_nick = f"💞 {days} Days in love {kaomoji}"
        else:
            new_nick = f"💞 {months} Months in love {kaomoji}"

        try:
            await guild.me.edit(nick=new_nick[:32])  # Discord nickname limit = 32 chars
            print(f"✅ Updated nickname to: {new_nick}")
        except Exception as e:
            print(f"⚠️ Failed to update nickname: {e}")


async def schedule_nickname_switch():
    """Switch nickname every 1 minute between days/months display."""
    await bot.wait_until_ready()
    mode = "days"
    while not bot.is_closed():
        await update_nickname(mode)
        # Alternate mode
        mode = "months" if mode == "days" else "days"
        await asyncio.sleep(60)  # every 1 minute


async def schedule_midnight_reset():
    """Ensure nickname refreshes at midnight local time for correct day count."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now(tz)
        next_midnight = tz.localize(datetime.combine(now.date() + timedelta(days=1), time(0, 0)))
        wait_seconds = (next_midnight - now).total_seconds()
        print(f"🕛 Next midnight recalculation in {wait_seconds/3600:.2f} hours")

        await asyncio.sleep(wait_seconds)
        await update_nickname("days")  # Refresh after midnight


# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} commands.")
    except Exception as e:
        print(f"⚠️ Error syncing commands: {e}")

    await bot.change_presence(activity=Game("💞 counting our love days"))
    await update_nickname("days")  # update immediately
    bot.loop.create_task(schedule_nickname_switch())  # alternate every minute
    bot.loop.create_task(schedule_midnight_reset())  # correct daily roll


# --- Slash Commands ---
@bot.tree.command(name="setstartdate", description="Set a new start date (YYYY-MM-DD)")
async def setstartdate(interaction, new_date: str):
    try:
        parsed_date = datetime.strptime(new_date, "%Y-%m-%d").date()
        save_start_date(parsed_date)
        await interaction.response.send_message(f"✅ Start date set to {new_date}")
        await asyncio.sleep(2)
        await update_nickname("days")
    except ValueError:
        await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD")


@bot.tree.command(name="ping", description="Check if the bot is alive 💕")
async def ping(interaction):
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    await interaction.response.send_message(f"🏓 Pong! I'm alive and in love 💞 (Local time: {now})")


bot.run(TOKEN)
