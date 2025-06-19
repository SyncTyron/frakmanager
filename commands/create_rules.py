# commands/create_rules.py
import discord
from discord import app_commands
import json
import os
from logs import debug

def register_create_rules_command(bot):
    @bot.tree.command(name="create_rules", description="Sendet ein Embed mit den Serverregeln aus der Config")
    async def create_rules(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"

        if not os.path.exists(config_path):
            debug(f"Keine Config gefunden für {guild_id}")
            await interaction.response.send_message("Keine Konfigurationsdatei gefunden.", ephemeral=True)
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        rules_channel_id = config.get("rules_embed", {}).get("rules_channel_id")
        if not rules_channel_id:
            debug(f"rules_channel_id fehlt in rules_embed der Config von {guild_id}")
            await interaction.response.send_message("rules_channel_id ist nicht konfiguriert.", ephemeral=True)
            return

        channel = bot.get_channel(int(rules_channel_id))
        if not channel:
            debug(f"Channel mit ID {rules_channel_id} nicht gefunden in Guild {guild_id}")
            await interaction.response.send_message("Der konfigurierte Channel wurde nicht gefunden.", ephemeral=True)
            return

        rules_embed = config.get("rules_embed", {})
        title = rules_embed.get("title", f"Regeln auf {interaction.guild.name}")
        description = rules_embed.get("description", "Keine Regeln konfiguriert.")
        thumbnail_url = rules_embed.get("thumbnail_url", "")
        color_hex = rules_embed.get("color", "2ecc71")
        color = int(color_hex, 16)

        embed = discord.Embed(
            title=title.replace("{guild_name}", interaction.guild.name),
            description=description,
            color=color
        )
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        await channel.send(embed=embed)
        debug(f"Regel-Embed in {rules_channel_id} gesendet von {interaction.user}")
        await interaction.response.send_message("✅ Regel-Embed wurde gesendet.", ephemeral=True)
