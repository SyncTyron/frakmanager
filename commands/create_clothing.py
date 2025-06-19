# commands/create_clothing.py
import discord
from discord import app_commands
import os
import json
from logs import debug

def register_create_clothing_command(bot):
    async def create_clothing(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"

        if not os.path.exists(config_path):
            debug(f"Keine Config gefunden für {guild_id}")
            await interaction.response.send_message("Keine Konfigurationsdatei gefunden.", ephemeral=True)
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        clothing_embed = config.get("clothing_embed", {})
        channel_id = clothing_embed.get("clothing_channel_id")
        if not channel_id:
            debug(f"clothing_channel_id fehlt in der Config von {guild_id}")
            await interaction.response.send_message("clothing_channel_id ist nicht konfiguriert.", ephemeral=True)
            return

        channel = bot.get_channel(int(channel_id))
        if not channel:
            debug(f"Channel mit ID {channel_id} nicht gefunden in Guild {guild_id}")
            await interaction.response.send_message("Der konfigurierte Channel wurde nicht gefunden.", ephemeral=True)
            return

        title = clothing_embed.get("title", f"{interaction.guild.name} Kleiderordnung!")
        description = clothing_embed.get("description", "")
        thumbnail_url = clothing_embed.get("thumbnail_url", "")
        color_hex = clothing_embed.get("color", "6a0606")
        color = int(color_hex, 16)

        embed = discord.Embed(
            title=title.replace("{guild_name}", interaction.guild.name),
            description=description,
            color=color
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        # ✅ Füge die Felder aus der Config hinzu
        fields = clothing_embed.get("fields", [])
        for field in fields:
            name = field.get("name")
            value = field.get("value")
            inline = field.get("inline", True)
            if name and value:
                embed.add_field(name=name, value=value, inline=inline)

        await channel.send(embed=embed)
        debug(f"Kleider-Embed mit Feldern in {channel_id} gesendet von {interaction.user}")
        await interaction.response.send_message("✅ Kleider-Embed wurde gesendet.", ephemeral=True)

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_clothing",
                description="Sendet ein Embed mit den Kleidervorgaben aus der Config",
                callback=create_clothing
            ),
            guild=discord.Object(id=guild.id)
        )
