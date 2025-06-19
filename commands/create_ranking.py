# commands/create_ranking.py
import discord
from discord import app_commands
import os
import json
from logs import debug

def register_create_ranking_command(bot):
    async def create_ranking(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"

        if not os.path.exists(config_path):
            debug(f"Keine Config gefunden für {guild_id}")
            await interaction.response.send_message("Keine Konfigurationsdatei gefunden.", ephemeral=True)
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        ranking_embed = config.get("ranking_embed", {})
        channel_id = ranking_embed.get("ranking_channel_id")
        if not channel_id:
            debug(f"ranking_channel_id fehlt in der Config von {guild_id}")
            await interaction.response.send_message("ranking_channel_id ist nicht konfiguriert.", ephemeral=True)
            return

        channel = bot.get_channel(int(channel_id))
        if not channel:
            debug(f"Channel mit ID {channel_id} nicht gefunden in Guild {guild_id}")
            await interaction.response.send_message("Der konfigurierte Channel wurde nicht gefunden.", ephemeral=True)
            return

        title = ranking_embed.get("title", f"{interaction.guild.name} Rangordnung!")
        description = ranking_embed.get("description", "")
        thumbnail_url = ranking_embed.get("thumbnail_url", "")
        color_hex = ranking_embed.get("color", "6a0606")
        color = int(color_hex, 16)

        embed = discord.Embed(
            title=title.replace("{guild_name}", interaction.guild.name),
            description=description,
            color=color
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        fields = ranking_embed.get("fields", [])
        for field in fields:
            name = field.get("name")
            value = field.get("value")
            inline = field.get("inline", True)
            if name and value:
                embed.add_field(name=name, value=value, inline=inline)

        await channel.send(embed=embed)
        debug(f"Ranking-Embed mit Feldern in {channel_id} gesendet von {interaction.user}")
        await interaction.response.send_message("✅ Ranking-Embed wurde gesendet.", ephemeral=True)

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_ranking",
                description="Sendet ein Embed mit der Rangstruktur aus der Config",
                callback=create_ranking
            ),
            guild=discord.Object(id=guild.id)
        )
