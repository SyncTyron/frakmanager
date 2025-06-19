import discord
from discord import app_commands
from discord.ui import Modal, TextInput, View
import json
import os

class ReportModal(Modal):
    def __init__(self, guild_name: str, send_channel: discord.TextChannel):
        super().__init__(title=f"{guild_name} Beschwerde einreichen")
        self.send_channel = send_channel

        self.name_input = TextInput(
            label="Dein Vorname & Nachname",
            placeholder="Max Mustermann",
            required=True,
            max_length=50
        )
        self.reason_input = TextInput(
            label="Beschwerde Grund",
            style=discord.TextStyle.short,
            placeholder="Regelverstoß, Fehlverhalten, etc.",
            required=True,
            max_length=100
        )
        self.details_input = TextInput(
            label="Beschwerde",
            style=discord.TextStyle.paragraph,
            placeholder="Beschreibe hier dein Anliegen...",
            required=True,
            max_length=2000
        )

        self.add_item(self.name_input)
        self.add_item(self.reason_input)
        self.add_item(self.details_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Neue Beschwerde eingereicht",
            color=discord.Color.orange()
        )
        embed.add_field(name="Vorname Nachname", value=self.name_input.value, inline=False)
        embed.add_field(name="Grund der Beschwerde", value=self.reason_input.value, inline=False)
        embed.add_field(name="Beschwerde", value=self.details_input.value, inline=False)
        embed.set_footer(text=f"Eingereicht von {interaction.user} | ID: {interaction.user.id}")

        await self.send_channel.send(embed=embed)
        await interaction.response.send_message("Deine Beschwerde wurde übermittelt.", ephemeral=True)

class ReportButtonView(View):
    def __init__(self, send_channel: discord.TextChannel, guild_name: str):
        super().__init__(timeout=None)
        self.send_channel = send_channel
        self.guild_name = guild_name

    @discord.ui.button(label="Report", style=discord.ButtonStyle.secondary, custom_id="open_report_modal")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReportModal(self.guild_name, self.send_channel)
        await interaction.response.send_modal(modal)

def get_config(guild_id):
    path = f"configs/config_{guild_id}.json"
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def register_create_report_command(bot: discord.Client):
    @app_commands.guilds(*[discord.Object(id=guild.id) for guild in bot.guilds])
    @app_commands.command(name="create_report", description="Erstellt ein Embed zur Einreichung von Beschwerden.")
    async def create_report(interaction: discord.Interaction):
        config = get_config(interaction.guild.id)
        if not config or "report_embed" not in config:
            await interaction.response.send_message("Keine gültige Konfiguration gefunden.", ephemeral=True)
            return

        report_cfg = config["report_embed"]
        report_channel = interaction.guild.get_channel(int(report_cfg["report_channel_id"]))
        send_channel = interaction.guild.get_channel(int(report_cfg["report_send_channel_id"]))

        if not report_channel or not send_channel:
            await interaction.response.send_message("Fehler beim Laden der Channel-IDs.", ephemeral=True)
            return

        embed = discord.Embed(
            title=report_cfg["title"].replace("{guild_name}", interaction.guild.name),
            description=report_cfg.get("description", ""),
            color=int(report_cfg.get("color", "000000"), 16)
        )

        view = ReportButtonView(send_channel, interaction.guild.name)
        await report_channel.send(embed=embed, view=view)
        await interaction.response.send_message("Beschwerde-Embed wurde erfolgreich gesendet.", ephemeral=True)

    bot.tree.add_command(create_report)
