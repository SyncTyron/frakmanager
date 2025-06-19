
# taxlineup_view.py
import discord
from checklist import update_checklist_status, get_checklist
from config_loader import load_config

class TaxLineupChecklistView(discord.ui.View):
    def __init__(self, member_id, checklist_id, guild_id):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.checklist_id = checklist_id
        self.guild_id = guild_id

    async def check_permission(self, interaction):
        config = load_config(str(self.guild_id))
        control_role_id = int(config["tax_checklist_control_role_id"])
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
    async def mark_paid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permission(interaction):
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
            return

        class PaidModal(discord.ui.Modal, title="Beitrag eingeben ($)"):
            betrag = discord.ui.TextInput(label="Beitrag in Dollar", placeholder="z. B. 225000", style=discord.TextStyle.short)

            async def on_submit(modalself, i):
                try:
                    amount = int(str(modalself.betrag))
                except ValueError:
                    await i.response.send_message("❌ Ungültiger Betrag!", ephemeral=True)
                    return

                update_checklist_status(self.guild_id, self.checklist_id, self.member_id, {"status": "✅", "amount": amount}, mode="tax")
                await i.response.send_message("✅ Betrag eingetragen.", ephemeral=True)
                await self.update_embed(i, f"✅ {amount}$")
                await self.try_finalize(i)

        await interaction.response.send_modal(PaidModal())

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def mark_failed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permission(interaction):
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
            return

        class FailModal(discord.ui.Modal, title="Grund für Nichtzahlung"):
            text = discord.ui.TextInput(label="Grund", placeholder="max. 500 Zeichen", max_length=500)

            async def on_submit(modalself, i):
                update_checklist_status(self.guild_id, self.checklist_id, self.member_id, {"status": "❌", "reason": str(modalself.text)}, mode="tax")
                await i.response.send_message("❌ Eingetragen.", ephemeral=True)
                await self.update_embed(i, f"❌ {modalself.text}")
                await self.try_finalize(i)

        await interaction.response.send_modal(FailModal())

    @discord.ui.button(label="🕒", style=discord.ButtonStyle.secondary)
    async def mark_pending(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permission(interaction):
            await interaction.response.send_message("Keine Berechtigung.", ephemeral=True)
            return

        class PendingModal(discord.ui.Modal, title="Verspätung begründen"):
            text = discord.ui.TextInput(label="Begründung", placeholder="z. B. Zahlung am 09.06.2025", max_length=500)

            async def on_submit(modalself, i):
                update_checklist_status(self.guild_id, self.checklist_id, self.member_id, {"status": "🕒", "note": str(modalself.text)}, mode="tax")
                await i.response.send_message("🕒 Eingetragen.", ephemeral=True)
                await self.update_embed(i, f"🕒 {modalself.text}")
                await self.try_finalize(i)

        await interaction.response.send_modal(PendingModal())

    async def try_finalize(self, interaction):
        checklist = get_checklist(self.guild_id, self.checklist_id, mode="tax")
        if checklist and all(v is not None for v in checklist["entries"].values()):
            await self.send_summary(interaction.guild)

    async def send_summary(self, guild):
        checklist = get_checklist(self.guild_id, self.checklist_id, mode="tax")
        config = load_config(str(self.guild_id))
        summary_channel = guild.get_channel(int(config["tax_summary_channel_id"]))

        color_raw = config["tax_summary_embed"].get("color", 0)
        try:
            color = int(color_raw, 16) if isinstance(color_raw, str) else color_raw
        except Exception:
            color = 0

        embed = discord.Embed(
            title=f"📋 Wochenabrechnung #{checklist['id']} | {checklist['datum']} {checklist['uhrzeit']}",
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
            line = f"{entry['status']} {name}"
            if entry['status'] == "✅":
                line += f" – {entry.get('amount')}$"
            elif entry['status'] == "❌":
                line += f" – {entry.get('reason', '')}"
            elif entry['status'] == "🕒":
                line += f" – {entry.get('note', '')}"

            embed.add_field(name="\u200b", value=line, inline=False)

        await summary_channel.send(embed=embed)
