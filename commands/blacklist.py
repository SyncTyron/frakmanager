
import discord
from discord import app_commands, ui
from datetime import datetime
from logs import debug
from config_loader import load_config
from db import load_json, save_json

def load_data(guild_id: str):
    return load_json(guild_id, "blacklist", {"entries": []})

def save_data(guild_id: str, data):
    save_json(guild_id, "blacklist", data)

def format_entry(entry, template):
    return template.format(**entry)

def register_blacklist_commands(bot):
    @app_commands.command(name="add_blacklist", description="Person manuell zur Blacklist hinzufügen")
    async def add_blacklist(interaction: discord.Interaction):
        class BlacklistModal(ui.Modal, title="Blacklist hinzufügen"):
            def __init__(self, interaction):
                super().__init__()
                self.interaction = interaction

            vorname = ui.TextInput(label="Vorname", required=True)
            nachname = ui.TextInput(label="Nachname", required=True)
            nummer = ui.TextInput(label="Handynummer", required=True)
            durch = ui.TextInput(label="Eingetragen durch", required=True)
            grund = ui.TextInput(label="Grund", required=True)

            async def on_submit(self, modal_interaction: discord.Interaction):
                guild_id = str(self.interaction.guild.id)
                config = load_config(guild_id).get("blacklist", {})

                if not config.get("enabled"):
                    return await modal_interaction.response.send_message("Blacklist-System ist deaktiviert.", ephemeral=True)

                if modal_interaction.channel.id != config.get("command_channel_id"):
                    return await modal_interaction.response.send_message("Dieser Command ist hier nicht erlaubt.", ephemeral=True)

                data = load_data(guild_id)
                entries = data.get("entries", [])
                new_id = len(entries) + 1

                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M Uhr")
                entry = {
                    "id": new_id,
                    "vorname": self.vorname.value,
                    "nachname": self.nachname.value,
                    "nummer": self.nummer.value,
                    "durch": self.durch.value,
                    "grund": self.grund.value,
                    "timestamp": timestamp
                }

                entries.append(entry)
                data["entries"] = entries
                save_data(guild_id, data)

                embed = discord.Embed(
                    title=f"Blacklist Eintrag #{new_id}, {timestamp}",
                    description=f"**Vor- Nachname:** {entry['vorname']} {entry['nachname']}\n**Handynummer:** {entry['nummer']}\n**Eingetragen:** {entry['durch']}\n**Grund:** {entry['grund']}",
                    color=0x6a0606
                )
                channel = modal_interaction.guild.get_channel(config["blacklist_channel_id"])
                if channel:
                    await channel.send(embed=embed)
                await modal_interaction.response.send_message("Blacklist-Eintrag hinzugefügt.", ephemeral=True)

        await interaction.response.send_modal(BlacklistModal(interaction))

    @app_commands.command(name="remove_blacklist", description="Blacklist-Eintrag entfernen")
    @app_commands.describe(id="ID des Eintrags")
    async def remove_blacklist(interaction: discord.Interaction, id: int):
        config = load_config(str(interaction.guild.id)).get("blacklist", {})
        if not config.get("enabled") or not config.get("allow_remove_command"):
            return await interaction.response.send_message("Befehl nicht erlaubt.", ephemeral=True)

        guild_id = str(interaction.guild.id)
        data = load_data(guild_id)
        entries = data.get("entries", [])
        new_entries = [e for e in entries if e["id"] != id]

        if len(entries) == len(new_entries):
            return await interaction.response.send_message("Eintrag nicht gefunden.", ephemeral=True)

        data["entries"] = new_entries
        save_data(guild_id, data)
        await interaction.response.send_message(f"Eintrag #{id} entfernt. Bitte Nachricht manuell löschen.", ephemeral=True)

    @app_commands.command(name="check_blacklist", description="Suche nach einer Handynummer auf der Blacklist")
    @app_commands.describe(handynummer="Handynummer, nach der gesucht werden soll")
    async def check_blacklist(interaction: discord.Interaction, handynummer: str):
        config = load_config(str(interaction.guild.id)).get("blacklist", {})
        if not config.get("enabled") or not config.get("allow_check_command"):
            return await interaction.response.send_message("Befehl nicht erlaubt.", ephemeral=True)

        channel = interaction.guild.get_channel(config["blacklist_channel_id"])
        if not channel:
            return await interaction.response.send_message("Blacklist-Channel nicht gefunden.", ephemeral=True)

        async for msg in channel.history(limit=100):
            if handynummer in msg.content and msg.author == interaction.client.user:
                return await interaction.response.send_message(f"Eintrag gefunden: {msg.jump_url}", ephemeral=True)

        await interaction.response.send_message("Nicht auf der Blacklist.", ephemeral=True)

    for guild in bot.guilds:
        try:
            bot.tree.add_command(add_blacklist, guild=discord.Object(id=guild.id))
            bot.tree.add_command(remove_blacklist, guild=discord.Object(id=guild.id))
            bot.tree.add_command(check_blacklist, guild=discord.Object(id=guild.id))
            debug(f"✅ Blacklist-Commands für Guild {guild.id} registriert.")
        except Exception as e:
            debug(f"❌ Fehler bei Registrierung für Guild {guild.id}: {e}")
