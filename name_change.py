# name_change.py
import discord
import os
import json
from logs import debug
from db import is_user_verified, add_verification
from discord import app_commands

def setup(bot):
    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id") == "verify_button":
            debug(f"✅ Verify-Button gedrückt von {interaction.user}")
            modal = NameModal(guild_id=str(interaction.guild_id))
            await interaction.response.send_modal(modal)

    @bot.event
    async def on_member_remove(member: discord.Member):
        debug(f"👋 Mitglied hat den Server verlassen: {member.name}")
        for role in member.roles:
            if role.name.startswith("📞 "):
                users_with_role = [m for m in member.guild.members if role in m.roles]
                if len(users_with_role) == 0:
                    try:
                        await role.delete(reason="Benutzer mit Telefonnummer-Rolle hat den Server verlassen")
                        debug(f"🗑️ Telefonnummer-Rolle '{role.name}' gelöscht (nicht mehr verwendet)")
                    except Exception as e:
                        debug(f"⚠️ Fehler beim Löschen der Rolle '{role.name}': {e}")

class NameModal(discord.ui.Modal, title="Verifizierung"):
    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id
        self.first_name = discord.ui.TextInput(label="Vorname")
        self.last_name = discord.ui.TextInput(label="Nachname")
        self.phone_number = discord.ui.TextInput(
            label="Telefonnummer",
            placeholder="Nur Zahlen eingeben",
            style=discord.TextStyle.short,
            required=True,
            min_length=5,
            max_length=15
        )

        self.add_item(self.first_name)
        self.add_item(self.last_name)
        self.add_item(self.phone_number)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # WICHTIG!

        if not self.phone_number.value.isdigit():
            await interaction.followup.send("❌ Telefonnummer darf nur Zahlen enthalten.", ephemeral=True)
            return

        new_nickname = f"{self.first_name.value} {self.last_name.value}"
        try:
            await interaction.user.edit(nick=new_nickname)
            debug(f"✏️ Nickname von {interaction.user} geändert zu {new_nickname}")
        except Exception as e:
            debug(f"⚠️ Fehler beim Ändern des Nicknames: {e}")

        # Rollen aus Config laden und vergeben
        config_path = f"configs/config_{self.guild_id}.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            role_ids = config.get("verify_embed", {}).get("roles", [])
            for role_id in role_ids:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    try:
                        await interaction.user.add_roles(role, reason="Verifizierung abgeschlossen")
                        debug(f"✅ Rolle '{role.name}' an {interaction.user} vergeben")
                    except Exception as e:
                        debug(f"⚠️ Fehler beim Vergeben der Rolle {role.name}: {e}")
                else:
                    debug(f"⚠️ Rolle mit ID {role_id} nicht gefunden in Guild {self.guild_id}")

        mitglied_seit = interaction.user.joined_at.strftime("%d.%m.%Y") if interaction.user.joined_at else "Unbekannt"
        aktuelle_rangliste = [role.name for role in interaction.user.roles if role.name != "@everyone"]
        rang = ", ".join(aktuelle_rangliste)

        user_entry = {
            "Vorname": self.first_name.value,
            "Nachname": self.last_name.value,
            "Telefonnummer": self.phone_number.value,
            "Rang": rang,
            "Mitglied seit": mitglied_seit,
            "User-ID": str(interaction.user.id)
        }

        if is_user_verified(self.guild_id, str(interaction.user.id)):
            await interaction.followup.send("⚠️ Du bist bereits verifiziert.", ephemeral=True)
            return

        add_verification(self.guild_id, user_entry)
        debug(f"📝 Verifizierungsdaten für {interaction.user} gespeichert")

        debug(f"📝 Verifizierungsdaten für {interaction.user} gespeichert in {csv_path}")

        # Telefonnummer-Rolle erstellen und zuweisen
        phone_role_name = f"📞 {self.first_name.value} {self.last_name.value}: {self.phone_number.value}"
        existing_role = discord.utils.get(interaction.guild.roles, name=phone_role_name)

        if existing_role is None:
            try:
                new_role = await interaction.guild.create_role(
                    name=phone_role_name,
                    hoist=False,
                    mentionable=False,
                    permissions=discord.Permissions.none(),
                    colour=discord.Colour(0xFF69B4),  # Pink
                    reason="Telefonnummer-Rolle für Verifizierung"
                )
                debug(f"➕ Telefonnummer-Rolle '{phone_role_name}' erstellt")
            except Exception as e:
                debug(f"⚠️ Fehler beim Erstellen der Telefonnummer-Rolle: {e}")
                new_role = None
        else:
            new_role = existing_role

        if new_role:
            try:
                await interaction.user.add_roles(new_role, reason="Telefonnummer gespeichert")
                debug(f"📎 Telefonnummer-Rolle '{new_role.name}' an {interaction.user} vergeben")
            except Exception as e:
                debug(f"⚠️ Fehler beim Zuweisen der Telefonnummer-Rolle: {e}")

        await interaction.followup.send("✅ Erfolgreich verifiziert!", ephemeral=True)
