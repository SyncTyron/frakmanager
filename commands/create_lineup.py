
# commands/create_lineup.py
import discord
from discord import app_commands
from checklist import create_checklist_entry
from checklist_view import ChecklistView
from config_loader import load_config

def register_create_lineup_command(bot):
    async def create_lineup(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = load_config(guild_id)

        if interaction.channel_id != int(config["lineup_command_channel_id"]):
            await interaction.response.send_message("❌ Dieser Befehl ist hier nicht erlaubt.", ephemeral=True)
            return

        class LineupModal(discord.ui.Modal, title="Neue Aufstellung erstellen"):
            datum = discord.ui.TextInput(label="📅 Datum", placeholder="z. B. 01.06.2025")
            uhrzeit = discord.ui.TextInput(label="🕓 Uhrzeit", placeholder="z. B. 19:00 Uhr")
            ort = discord.ui.TextInput(label="📍 Ort", placeholder="Ort oder Treffpunkt")

            async def on_submit(modalself, i: discord.Interaction):
                await i.response.defer(ephemeral=True)

                embed_template = config["lineup_embed"]
                color_raw = embed_template.get("color", 0)
                try:
                    color = int(color_raw, 16) if isinstance(color_raw, str) else color_raw
                except Exception:
                    color = 0

                embed = discord.Embed(
                    title=embed_template["title"],
                    description=embed_template["description"]
                        .replace("{datum}", str(modalself.datum))
                        .replace("{uhrzeit}", str(modalself.uhrzeit))
                        .replace("{ort}", str(modalself.ort)),
                    color=color
                )
                embed.set_footer(text=embed_template.get("footer", ""))
                await i.channel.send(f"<@&{embed_template['ping_role_id']}>", embed=embed)

                category = i.guild.get_channel(int(config["lineup_category_id"]))
                overwrites = {
                    i.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    i.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                temp_channel = await i.guild.create_text_channel(
                    name=f"Aufstellung {modalself.datum} | {modalself.uhrzeit}",
                    category=category
                )

                role = i.guild.get_role(int(config["checklist_target_role_id"]))
                members = [m for m in role.members if not m.bot]  # ✅ Member-Objekte
                checklist = create_checklist_entry(
                    guild_id,
                    str(modalself.datum),
                    str(modalself.uhrzeit),
                    str(modalself.ort),
                    members,
                    mode="lineup"
                )

                checklist_color_raw = config["checklist_embed"].get("color", 0)
                try:
                    checklist_color = int(checklist_color_raw, 16) if isinstance(checklist_color_raw, str) else checklist_color_raw
                except Exception:
                    checklist_color = 0

                for m in members:
                    view = ChecklistView(m.id, checklist["id"], i.guild_id)
                    embed = discord.Embed(
                        title=f"Checkliste #{checklist['id']} | {modalself.datum} {modalself.uhrzeit}",
                        description=f"**👤 {m.display_name}**\n\nStatus: ⬜ Noch nicht bewertet",
                        color=checklist_color
                    )
                    await temp_channel.send(embed=embed, view=view)

                await i.followup.send(f"✅ Aufstellung + Checkliste #{checklist['id']} erstellt!", ephemeral=True)

        await interaction.response.send_modal(LineupModal())

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_lineup",
                description="Erstellt eine neue Aufstellung mit Checkliste.",
                callback=create_lineup
            ),
            guild=discord.Object(id=guild.id)
        )
