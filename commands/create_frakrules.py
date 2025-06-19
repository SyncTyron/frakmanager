# commands/create_frakrules.py
import discord
from discord import app_commands
import json
import os
from logs import debug

def register_create_frakrules_command(bot):
    async def create_frakrules(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"

        if not os.path.exists(config_path):
            debug(f"Keine Config gefunden für {guild_id}")
            await interaction.response.send_message("Keine Konfigurationsdatei gefunden.", ephemeral=True)
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        channel_id = config.get("frakrules_embed", {}).get("frakrules_channel_id")
        if not channel_id:
            debug(f"frakrules_channel_id fehlt in der Config von {guild_id}")
            await interaction.response.send_message("frakrules_channel_id ist nicht konfiguriert.", ephemeral=True)
            return

        channel = bot.get_channel(int(channel_id))
        if not channel:
            debug(f"Channel mit ID {channel_id} nicht gefunden in Guild {guild_id}")
            await interaction.response.send_message("Der konfigurierte Channel wurde nicht gefunden.", ephemeral=True)
            return

        frakrules_embed = config.get("frakrules_embed", {})
        title = frakrules_embed.get("title", f"Fraktionsregeln auf {interaction.guild.name}")
        description = frakrules_embed.get("description", "Keine Fraktionsregeln konfiguriert.")
        thumbnail_url = frakrules_embed.get("thumbnail_url", "")
        color_hex = frakrules_embed.get("color", "e67e22")
        color = int(color_hex, 16)

        embed = discord.Embed(
            title=title.replace("{guild_name}", interaction.guild.name),
            description=description,
            color=color
        )
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        await channel.send(embed=embed)
        debug(f"Fraktionsregel-Embed in {channel_id} gesendet von {interaction.user}")
        await interaction.response.send_message("✅ Fraktionsregel-Embed wurde gesendet.", ephemeral=True)

    # Command für jede Guild explizit registrieren
    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_frakrules",
                description="Sendet ein Embed mit den Fraktionsregeln aus der Config",
                callback=create_frakrules
            ),
            guild=discord.Object(id=guild.id)
        )
