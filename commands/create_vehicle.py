# commands/create_vehicle.py
import discord
from discord import app_commands
import os
import json
from logs import debug

def register_create_vehicle_command(bot):
    async def create_vehicle(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"

        if not os.path.exists(config_path):
            debug(f"Keine Config gefunden für {guild_id}")
            await interaction.response.send_message("Keine Konfigurationsdatei gefunden.", ephemeral=True)
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        channel_id = config.get("vehicle_embed", {}).get("vehicle_channel_id")
        if not channel_id:
            debug(f"vehicle_channel_id fehlt in der Config von {guild_id}")
            await interaction.response.send_message("vehicle_channel_id ist nicht konfiguriert.", ephemeral=True)
            return

        channel = bot.get_channel(int(channel_id))
        if not channel:
            debug(f"Channel mit ID {channel_id} nicht gefunden in Guild {guild_id}")
            await interaction.response.send_message("Der konfigurierte Channel wurde nicht gefunden.", ephemeral=True)
            return

        vehicle_embed = config.get("vehicle_embed", {})
        title = vehicle_embed.get("title", f"{interaction.guild.name} Fahrzeugordnung!")
        description = vehicle_embed.get("description", "")
        thumbnail_url = vehicle_embed.get("thumbnail_url", "")
        color_hex = vehicle_embed.get("color", "6a0606")
        color = int(color_hex, 16)

        embed = discord.Embed(
            title=title.replace("{guild_name}", interaction.guild.name),
            description=description,
            color=color
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        await channel.send(embed=embed)
        debug(f"Fahrzeug-Embed in {channel_id} gesendet von {interaction.user}")
        await interaction.response.send_message("✅ Fahrzeug-Embed wurde gesendet.", ephemeral=True)

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_vehicle",
                description="Sendet ein Embed mit den Fahrzeugregeln aus der Config",
                callback=create_vehicle
            ),
            guild=discord.Object(id=guild.id)
        )
