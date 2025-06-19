# commands/create_verify.py
import discord
from discord import app_commands
import json
import os
from logs import debug

def register_create_verify_command(bot):
    class VerifyButton(discord.ui.View):
        def __init__(self, guild_id):
            super().__init__(timeout=None)
            self.guild_id = guild_id
            self.add_item(discord.ui.Button(label="Verifizieren", custom_id="verify_button"))

    @bot.tree.command(name="create_verify", description="Sendet die Embed Verifizierungsnachricht")
    async def create_verify(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"

        if not os.path.exists(config_path):
            debug(f"Keine Config gefunden für {guild_id}")
            await interaction.response.send_message("Keine Config gefunden.", ephemeral=True)
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        verify_config = config.get("verify_embed", {})
        channel_id = verify_config.get("verify_channel_id")
        if not channel_id:
            debug(f"verify_channel_id fehlt in verify_embed der Config von {guild_id}")
            await interaction.response.send_message("verify_channel_id ist nicht konfiguriert.", ephemeral=True)
            return

        channel = bot.get_channel(int(channel_id))
        if channel is None:
            debug(f"Channel mit ID {channel_id} nicht gefunden in Guild {guild_id}.")
            await interaction.response.send_message("Konfigurierter Channel nicht gefunden.", ephemeral=True)
            return

        title = verify_config.get("title", f"Willkommen auf {interaction.guild.name}!")
        description = verify_config.get("description", "Verifiziere dich um ein Vollwertiges Mitglied zu werden.")
        thumbnail_url = verify_config.get("thumbnail_url", "")
        color = int(verify_config.get("color", "ffffff"), 16)

        embed = discord.Embed(
            title=title.replace("{guild_name}", interaction.guild.name),
            description=description,
            color=color
        )
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        new_msg = await channel.send(embed=embed, view=VerifyButton(guild_id))
        config["verify_embed"]["verify_message_id"] = str(new_msg.id)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        debug(f"Verifizierungsnachricht gesendet in {channel_id} und ID gespeichert.")
        await interaction.response.send_message("✅ Verifizierungsnachricht gesendet.", ephemeral=True)
