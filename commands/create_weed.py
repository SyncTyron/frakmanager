import discord
from discord import app_commands
import json
import os
from logs import debug

def load_config(guild_id):
    config_path = f"configs/config_{guild_id}.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def extract_youtube_id(url):
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

class WeedDropdown(discord.ui.Select):
    def __init__(self, config_data):
        self.config_data = config_data
        options = [
            discord.SelectOption(label="Sammler", value="sammler", description="Sammle frisches Weed."),
            discord.SelectOption(label="Verarbeiter", value="verarbeiter", description="Verarbeite das gesammelte Weed."),
            discord.SelectOption(label="Verkäufer", value="verkaeufer", description="Verkaufe das fertige Produkt.")
        ]
        super().__init__(placeholder="Wähle deine Weed-Rolle...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        data = self.config_data.get("weed_roles", {}).get(selected)

        if not data:
            await interaction.response.send_message("❌ Konfiguration für diese Rolle fehlt.", ephemeral=True)
            return

        description = data.get("description", "Keine Beschreibung verfügbar.")
        video_url = data.get("video_url", "")
        color = int(data.get("color", "6a0606"), 16)

        embed = discord.Embed(
            title=data.get("title", "Kein Titel gesetzt"),
            description=description,
            color=color
        )

        embed.set_footer(text="Weed System")

        # Embed senden
        await interaction.channel.send(embed=embed)

        # Sichtbarer YouTube-Link für eingebetteten Player
        if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
            await interaction.channel.send(video_url)

        await interaction.response.defer()

class WeedView(discord.ui.View):
    def __init__(self, config_data):
        super().__init__(timeout=None)
        self.add_item(WeedDropdown(config_data))

def register_create_weed_command(bot):
    async def create_weed(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = load_config(guild_id)

        if not config.get("weed_roles"):
            debug(f"⚠️ Weed-Konfiguration fehlt für {guild_id}")
            await interaction.response.send_message("❌ Weed-Konfiguration nicht gefunden.", ephemeral=True)
            return

        # Dropdown öffentlich posten
        await interaction.channel.send(
            content="🌿 Wähle deine Rolle im Weed-System:",
            view=WeedView(config)
        )
        await interaction.response.defer(ephemeral=True)
        debug(f"✅ Weed-Dropdown gesendet in {guild_id} von {interaction.user}")

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_weed",
                description="Zeigt eine Dropdown-Auswahl für Weed-Rollen.",
                callback=create_weed
            ),
            guild=discord.Object(id=guild.id)
        )
