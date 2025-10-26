import os
import asyncio
from datetime import date, datetime
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
START_DATE_FILE = "start_date.txt"

bot = commands.Bot(command_prefix="!", intents=None)

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

# --- Main Logic ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    update_nickname.start()

@tasks.loop(hours=24)
async def update_nickname():
    guild = bot.get_guild(GUILD_ID)
    if guild:
        start_date = load_start_date()
        days_passed = (date.today() - start_date).days
        new_nick = f"Day {days_passed}"
        try:
            await guild.me.edit(nick=new_nick)
            print(f"✅ Updated nickname to {new_nick}")
        except Exception as e:
            print(f"⚠️ Failed to update nickname: {e}")

# --- Slash Command ---
@bot.tree.command(name="setstartdate", description="Set a new start date (YYYY-MM-DD)")
async def setstartdate(interaction, new_date: str):
    try:
        parsed_date = datetime.strptime(new_date, "%Y-%m-%d").date()
        save_start_date(parsed_date)
        await interaction.response.send_message(f"✅ Start date set to {new_date}")
        # Update immediately
        await asyncio.sleep(2)
        await update_nickname()
    except ValueError:
        await interaction.response.send_message("❌ Invalid date format. Use YYYY-MM-DD")

bot.run(TOKEN)
