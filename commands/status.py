### commands/status.py
def register_status_command(bot):
    import discord
    from discord import app_commands
    from logs import debug
    from whitelist import is_guild_whitelisted
    import os

    @bot.tree.command(name="status", description="Zeigt den Whitelist-Status und die verbundene Config-Datei.")
    async def status(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        whitelisted = is_guild_whitelisted(guild_id)
        config_path = f"configs/config_{guild_id}.json"
        config_exists = os.path.exists(config_path)
        debug(f"/status aufgerufen in Guild {guild_id}")
        await interaction.response.send_message(
            f"Whitelisted: {whitelisted}\nConfig gefunden: {config_exists}",
            ephemeral=True
        )
