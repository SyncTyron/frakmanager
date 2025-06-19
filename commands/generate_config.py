# commands/generate_config.py
def register_generate_config_command(bot):
    import discord
    from discord import app_commands
    import os
    import json
    import shutil
    from logs import debug

    @bot.tree.command(name="generate_config", description="Erstellt eine Konfigurationsdatei aus dem Template.")
    async def generate_config(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config_path = f"configs/config_{guild_id}.json"
        if os.path.exists(config_path):
            debug(f"Config für Guild {guild_id} existiert bereits.")
            await interaction.response.send_message("Konfigurationsdatei existiert bereits.", ephemeral=True)
            return

        try:
            shutil.copyfile("templates/config_guild_id.json", config_path)
            with open(config_path, 'r+', encoding='utf-8') as f:
                config_data = json.load(f)
                config_data['guild_id'] = guild_id
                config_data.setdefault('embed', {
                    "title": "Willkommen auf {guild_name}!",
                    "description": "Verifiziere dich um ein vollwertiges Mitglied zu werden."
                })
                config_data.setdefault('rules_embed', {
                    "title": "Regeln auf {guild_name}",
                    "description": "Bitte halte dich an folgende Regeln...",
                    "thumbnail_url": "",
                    "color": "2ecc71"
                })
                f.seek(0)
                json.dump(config_data, f, indent=4)
                f.truncate()
            debug(f"Konfiguration für Guild {guild_id} erstellt.")
            await interaction.response.send_message("Konfiguration erfolgreich erstellt.", ephemeral=True)
        except Exception as e:
            debug(f"Fehler beim Erstellen der Konfiguration: {e}")
            await interaction.response.send_message("Fehler beim Erstellen der Konfiguration.", ephemeral=True)