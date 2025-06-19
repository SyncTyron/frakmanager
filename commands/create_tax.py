
# commands/create_tax.py
import discord
from discord import app_commands
from checklist import create_checklist_entry
from tax_view import TaxLineupChecklistView
from config_loader import load_config

def register_create_tax_command(bot):
    async def create_tax(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = load_config(guild_id)

        if interaction.channel_id != int(config["tax_lineup_command_channel_id"]):
            await interaction.response.send_message("❌ Dieser Befehl ist hier nicht erlaubt.", ephemeral=True)
            return

        class TaxLineupModal(discord.ui.Modal, title="Neue Wochenabgabe"):
            von = discord.ui.TextInput(label="Von (Datum)", placeholder="01.06.2025")
            bis = discord.ui.TextInput(label="Bis (Datum)", placeholder="07.06.2025")
            uhrzeit = discord.ui.TextInput(label="Uhrzeit", placeholder="19:00 Uhr")
            abgeben_an = discord.ui.TextInput(label="Abgeben an", placeholder="Vor- und Nachname")

            async def on_submit(modalself, i):
                await i.response.defer(ephemeral=True)

                embed_template = config["tax_lineup_embed"]
                color_raw = embed_template.get("color", 0)
                try:
                    color = int(color_raw, 16) if isinstance(color_raw, str) else color_raw
                except Exception:
                    color = 0

                embed = discord.Embed(
                    title=embed_template["title"],
                    description=embed_template["description"]
                        .replace("{von}", str(modalself.von))
                        .replace("{bis}", str(modalself.bis))
                        .replace("{uhrzeit}", str(modalself.uhrzeit))
                        .replace("{abgeben_an}", str(modalself.abgeben_an)),
                    color=color
                )
                embed.set_footer(text=embed_template.get("footer", ""))
                await i.channel.send(f"<@&{embed_template['ping_role_id']}>", embed=embed)

                category = i.guild.get_channel(int(config["tax_lineup_category_id"]))
                overwrites = {
                    i.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    i.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                temp_channel = await i.guild.create_text_channel(
                    name=f"Wochenabgabe-{modalself.von}--{modalself.bis}--{modalself.uhrzeit}",
                    category=category
                )

                role = i.guild.get_role(int(config["tax_checklist_target_role_id"]))
                members = [m for m in role.members if not m.bot]
                checklist = create_checklist_entry(guild_id,
                    f"{modalself.von} - {modalself.bis}",
                    str(modalself.uhrzeit),
                    str(modalself.abgeben_an),
                    members,
                    mode="tax"
                )

                checklist_color_raw = config["tax_checklist_embed"].get("color", 0)
                try:
                    checklist_color = int(checklist_color_raw, 16) if isinstance(checklist_color_raw, str) else checklist_color_raw
                except Exception:
                    checklist_color = 0

                for m in members:
                    view = TaxLineupChecklistView(m.id, checklist["id"], i.guild_id)
                    embed = discord.Embed(
                        title=f"Checkliste #{checklist['id']} | {modalself.von} - {modalself.bis} {modalself.uhrzeit}",
                        description=f"👤 {m.display_name}\n\nStatus: ⬜ Noch nicht bewertet",
                        color=checklist_color
                    )
                    await temp_channel.send(embed=embed, view=view)

                await i.followup.send(f"✅ Wochenabgabe + Checkliste #{checklist['id']} erstellt!", ephemeral=True)

        await interaction.response.send_modal(TaxLineupModal())

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_tax",
                description="Erstellt eine neue Wochenabgabe mit Checkliste.",
                callback=create_tax
            ),
            guild=discord.Object(id=guild.id)
        )
