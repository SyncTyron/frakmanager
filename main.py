# main.py
import discord
from discord.ext import commands
import os
import shutil
import json
import logging
from dotenv import load_dotenv
import asyncio

from whitelist import is_guild_whitelisted
from commands.generate_config import register_generate_config_command
from commands.status import register_status_command
from commands.create_verify import register_create_verify_command
from commands.create_rules import register_create_rules_command
from commands.create_frakrules import register_create_frakrules_command
from commands.create_sanction import register_create_sanction_command
from commands.create_weed import register_create_weed_command
from commands.create_vehicle import register_create_vehicle_command
from commands.create_clothing import register_create_clothing_command
from commands.create_ranking import register_create_ranking_command
from commands.create_report import register_create_report_command
from commands.create_lineup import register_create_lineup_command
from commands.create_tax import register_create_tax_command
from commands.blacklist import register_blacklist_commands
from commands.create_order import register_create_order_command
import name_change
from logs import debug

# === Initial Setup ===
for folder in ["logs", "configs", "data"]:
    os.makedirs(folder, exist_ok=True)
    debug(f"📁 Ordner sichergestellt: {folder}/")

# === Environment ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    debug("❌ DISCORD_TOKEN nicht gefunden. Bitte prüfe deine .env Datei.")
    exit(1)
else:
    debug(f"🔑 DISCORD_TOKEN geladen: {TOKEN[:5]}...")

# === Bot Setup ===
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

# === Events ===
@bot.event
async def on_ready():
    debug("✅ Bot ist bereit (on_ready)")

    for guild in bot.guilds:
        guild_id = str(guild.id)
        config_path = f"configs/config_{guild_id}.json"

        if is_guild_whitelisted(guild_id):
            if not os.path.exists(config_path):
                debug(f"📄 Kopiere Template für Guild {guild_id}")
                shutil.copyfile("templates/config_guild_id.json", config_path)

            # Konfigurationsdatei initialisieren
            with open(config_path, 'r+', encoding='utf-8') as f:
                config_data = json.load(f)

                config_data.setdefault("verify_embed", {
                    "verify_message_id": "",
                    "title": "Willkommen auf {guild_name}!",
                    "description": "Klicke auf den Button um dich zu verifizieren.",
                    "thumbnail_url": "",
                    "color": "6a0606",
                    "roles": []
                })
                config_data.setdefault("rules_embed", {
                    "title": "{guild_name} Discord Regeln!",
                    "description": "",
                    "thumbnail_url": "",
                    "color": "6a0606"
                })
                config_data.setdefault("frakrules_embed", {
                    "title": "{guild_name} Fraktionsregeln!",
                    "description": "",
                    "thumbnail_url": "",
                    "color": "6a0606"
                })
                config_data.setdefault("sanction_embed", {
                    "title": "{guild_name} Sanktionen!",
                    "description": "",
                    "thumbnail_url": "",
                    "color": "6a0606"
                })



                config_data['guild_id'] = guild_id
                f.seek(0)
                json.dump(config_data, f, indent=4)
                f.truncate()
        else:
            debug(f"🚫 Guild {guild_id} ist nicht in der Whitelist.")

    # === Commands registrieren ===
    register_status_command(bot)
    register_create_verify_command(bot)
    register_generate_config_command(bot)
    register_create_rules_command(bot)
    register_create_frakrules_command(bot)
    register_create_sanction_command(bot)
    register_create_weed_command(bot)
    register_create_vehicle_command(bot)
    register_create_clothing_command(bot)
    register_create_ranking_command(bot)
    register_create_report_command(bot)
    register_create_lineup_command(bot)
    register_create_tax_command(bot)
    register_blacklist_commands(bot)
    register_create_order_command(bot)
    debug("✅ Alle Commands registriert.")
    # === Name Change Setup ===
    debug("🔄 Name Change Setup wird initialisiert...")
    name_change.setup(bot)

    # === Slash-Commands synchronisieren ===
    try:
        for guild in bot.guilds:
            await bot.tree.sync(guild=guild)
            debug(f"📡 Slash-Commands mit Guild {guild.id} synchronisiert.")
    except Exception as e:
        debug(f"❌ Fehler beim Synchronisieren der Slash-Commands: {e}")

# === Start Bot ===
if __name__ == "__main__":
    bot.run(TOKEN)
