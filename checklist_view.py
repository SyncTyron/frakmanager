
# checklist_view.py
import discord
from checklist import update_checklist_status, get_checklist
from config_loader import load_config

class ChecklistView(discord.ui.View):
    def __init__(self, member_id, checklist_id, guild_id):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.checklist_id = checklist_id
        self.guild_id = guild_id

    async def check_permission(self, interaction):
        config = load_config(str(self.guild_id))
        control_role_id = int(config["checklist_control_role_id"])
        return any(role.id == control_role_id for role in interaction.user.roles)

    async def update_embed(self, interaction, new_status):
        message = interaction.message
        embed = message.embeds[0]
        lines = embed.description.split("\n")
        for idx, line in enumerate(lines):
            if line.startswith("Status:"):
                lines[idx] = f"Status: {new_status}"
                break
        embed.description = "\n".join(lines)
        await message.edit(embed=embed, view=self)

    @discord.ui.button(label="✅", style=discord.ButtonStyle.success)
    async def mark_present(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permission(interaction):
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
            return
        update_checklist_status(self.guild_id, self.checklist_id,  self.member_id, {"status": "✅"}, mode="lineup")
        await interaction.response.send_message("✅ markiert.", ephemeral=True)
        await self.update_embed(interaction, "✅ Anwesend")
        await self.try_finalize(interaction)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def mark_absent(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permission(interaction):
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
            return

        class AbsentModal(discord.ui.Modal, title="Abwesenheit begründen"):
            grund = discord.ui.TextInput(label="Grund (abgemeldet/nicht abgemeldet)")
            async def on_submit(modalself, i):
                update_checklist_status(self.guild_id, self.checklist_id,  self.member_id, {"status": "❌", "comment": str(modalself.grund)})
                await i.response.send_message("❌ markiert.", ephemeral=True)
                await self.update_embed(i, f"❌ Abwesend – {modalself.grund}")
                await self.try_finalize(i)

        await interaction.response.send_modal(AbsentModal())

    @discord.ui.button(label="🕒", style=discord.ButtonStyle.secondary)
    async def mark_late(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permission(interaction):
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
            return

        class LateModal(discord.ui.Modal, title="Verspätung eintragen"):
            minuten = discord.ui.TextInput(label="Verspätung in Minuten", placeholder="z. B. 15")
            async def on_submit(modalself, i):
                update_checklist_status(self.guild_id, self.checklist_id,  self.member_id, {
                    "status": "🕒", "minutes": int(str(modalself.minuten))
                })
                await i.response.send_message("🕒 markiert.", ephemeral=True)
                await self.update_embed(i, f"🕒 Verspätet – {modalself.minuten} Minuten")
                await self.try_finalize(i)

        await interaction.response.send_modal(LateModal())

    async def try_finalize(self, interaction):
        checklist = get_checklist(self.guild_id, self.checklist_id, mode="lineup")
        if checklist and all(v is not None for v in checklist["entries"].values()):
            await self.send_summary(interaction.guild)

    async def send_summary(self, guild):
        checklist = get_checklist(self.guild_id, self.checklist_id, mode="lineup")
        config = load_config(str(self.guild_id))
        summary_channel = guild.get_channel(int(config["summary_channel_id"]))

        color_raw = config["summary_embed"].get("color", 0)
        try:
            color = int(color_raw, 16) if isinstance(color_raw, str) else color_raw
        except Exception:
            color = 0

        embed = discord.Embed(
            title=f"✅ Abschluss – Checkliste #{checklist['id']} | {checklist['datum']} {checklist['uhrzeit']}",
            description="**📅 Datum:** {datum}\n**🕓 Uhrzeit:** {uhrzeit}\n**📍 Ort:** {ort}".format(
                datum=checklist['datum'],
                uhrzeit=checklist['uhrzeit'],
                ort=checklist['ort']
            ),
            color=color
        )

        for uid, entry in checklist["entries"].items():
            member = guild.get_member(int(uid))
            name = member.display_name if member else "Unbekannt"
            if entry["status"] == "✅":
                text = f"✅ {name}"
            elif entry["status"] == "❌":
                text = f"❌ {name} – {entry.get('comment', '')}"
            elif entry["status"] == "🕒":
                text = f"🕒 {name} – {entry.get('minutes')} Minuten"
            else:
                text = f"⬜ {name}"
            embed.add_field(name="\u200b", value=text, inline=False)

        await summary_channel.send(embed=embed)
