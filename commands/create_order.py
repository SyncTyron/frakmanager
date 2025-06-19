import asyncio
# commands/create_order.py
import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime
import os, json

# === Hilfsfunktionen ===
def load_config(guild_id):
    with open(f"configs/config_{guild_id}.json", encoding="utf-8") as f:
        return json.load(f)

def get_data_path(guild_id):
    path = f"data/{guild_id}"
    os.makedirs(path, exist_ok=True)
    return f"{path}/order_data.json"

def load_order_data(guild_id):
    path = get_data_path(guild_id)
    if not os.path.exists(path):
        return {"orders": [], "next_id": 1}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_order_data(guild_id, data):
    with open(get_data_path(guild_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# === Hauptfunktion ===
def register_create_order_command(bot):
    active_orders = {}

    class ConfirmButton(discord.ui.View):  # ← HIER EINFÜGEN
        def __init__(self, message):
            super().__init__(timeout=None)
            self.message = message

        @discord.ui.button(label="✅ Bezahlt", style=discord.ButtonStyle.success)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = self.message.embeds[0]
            if not embed:
                await interaction.response.send_message("Kein Embed gefunden.", ephemeral=True)
                return

            new_embed = embed.copy()
            if "Status: ❌ Offen" in new_embed.description:
                new_embed.description = new_embed.description.replace("Status: ❌ Offen", "Status: ✅ Bezahlt")
                await self.message.edit(embed=new_embed, view=None)


    @tasks.loop(seconds=60)
    async def check_expired_orders():
        now = datetime.now()
        for message_id, order in list(active_orders.items()):
            if now >= order['end']:
                try:
                    channel = bot.get_channel(order['channel_id'])
                    msg = await channel.fetch_message(message_id)

                    # Embed kopieren und "Offen" → "❌ Nicht bezahlt" ersetzen
                    if msg.embeds:
                        embed = msg.embeds[0]
                        if "Status: ❌ Offen" in embed.description:
                            new_embed = embed.copy()
                            new_embed.description = new_embed.description.replace("Status: ❌ Offen", "Status: Nicht bezahlt")
                            await msg.edit(embed=new_embed, view=None)
                        else:
                            await msg.edit(view=None)  # Buttons trotzdem entfernen

                except:
                    pass

                summary = {}
                for item in order['items']:
                    try:
                        msg = await channel.fetch_message(item['message_id'])
                        if not msg.embeds:
                            continue
                        embed = msg.embeds[0]
                        if "Status: ✅ Bezahlt" not in embed.description:
                            continue
                        key = item['selection']
                        summary[key] = summary.get(key, 0) + item['amount']
                    except Exception as e:
                        print(f"Fehler: {e}")
                        continue


                config = load_config(order['guild_id'])
                summary_cfg = config["order_embeds"]["summary"]
                color = int(summary_cfg.get("color", "0"), 16)

                embed = discord.Embed(
                    title=summary_cfg["title"].format(type=order['type']),
                    description="\n".join([f"{v}× {k}" for k, v in summary.items()]),
                    color=color
                )
                embed.set_footer(text=summary_cfg.get("footer", "").format(date=datetime.now().strftime("%d.%m.%Y")))
                await channel.send(embed=embed)
                await send_personal_summary(channel, order['items'], order['guild_id'], order['type'])
                del active_orders[message_id]

    async def send_personal_summary(channel, items, guild_id, typ):
        user_orders = {}
        for item in items:
            try:
                msg = await channel.fetch_message(item['message_id'])
                if not msg.embeds:
                    continue
                embed = msg.embeds[0]
                if "Status: ✅ Bezahlt" not in embed.description:
                    continue
                user_orders.setdefault(item['user_id'], []).append((item['selection'], item['amount']))
            except Exception as e:
                print(f"Fehler: {e}")
                continue

        config = load_config(guild_id)
        personal_cfg = config["order_embeds"].get("personal_summary", config["order_embeds"]["summary"])
        color = int(personal_cfg.get("color", "0"), 16)

        lines = []
        gesamt_summe = 0

        preise_lookup = {}
        for typ_liste in config["order_dropdown_options"].values():
            for eintrag in typ_liste:
                preise_lookup[eintrag["label"]] = eintrag["price"]

        for user_id, bestellungen in user_orders.items():
            member = channel.guild.get_member(int(user_id))
            name = member.display_name if member else f"<@{user_id}>"
            lines.append(f"**{name}:**")
            summe = 0
            
            produkt_mengen = {}
            for produkt, menge in bestellungen:
                produkt_mengen[produkt] = produkt_mengen.get(produkt, 0) + menge

            for produkt, menge in produkt_mengen.items():
                preis_str = preise_lookup.get(produkt, "0").replace(".", "").replace("$", "")
                try:
                    einzelpreis = int(preis_str)
                except ValueError:
                    einzelpreis = 0
                gesamt = einzelpreis * menge
                summe += gesamt
                lines.append(f"{menge}× {produkt} = {gesamt:,}$".replace(",", "."))
            lines.append(f"**➞ Gesamt: {summe:,}$\n**".replace(",", "."))
            gesamt_summe += summe
        lines.append("")

        lines.append(f"__**Gesamtsumme aller Bestellungen: {gesamt_summe:,}$**__".replace(",", "."))

        description_text = personal_cfg["description"].replace("{summary}", "\n".join(lines))

        embed = discord.Embed(
            title=personal_cfg["title"].format(type=typ),
            description=description_text,
            color=color
        )
        embed.set_footer(text=personal_cfg["footer"].format(date=datetime.now().strftime("%d.%m.%Y")))
        await channel.send(embed=embed)

    check_expired_orders.start()

    async def create_order(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        config = load_config(guild_id)

        if interaction.channel_id != int(config.get("order_command_channel_id")):
            await interaction.response.send_message("❌ Dieser Befehl ist hier nicht erlaubt.", ephemeral=True, delete_after=30)
            return

        class OrderModal(discord.ui.Modal, title="Bestellzeitraum festlegen"):
            datum_von = discord.ui.TextInput(label="Datum von:", placeholder="01.06.2025")
            datum_bis = discord.ui.TextInput(label="Datum bis:", placeholder="03.06.2025")
            uhrzeit_bis = discord.ui.TextInput(label="Uhrzeit bis:", placeholder="23:00")

            async def on_submit(modalself, i):
                from_datum = modalself.datum_von.value
                to_datum = modalself.datum_bis.value
                until = modalself.uhrzeit_bis.value

                typ = i.data['custom_id'].split("_")[-1]
                embed_cfg = config["order_embeds"]["overview"]
                color = int(embed_cfg.get("color", "0"), 16)

                embed = discord.Embed(
                    title=embed_cfg["title"].format(type=typ),
                    description=embed_cfg["description"].replace("{from}", from_datum).replace("{to}", to_datum).replace("{until}", until),
                    color=color
                )
                embed.set_footer(text=embed_cfg.get("footer", "").replace("{to}", to_datum).replace("{until}", until))

                category_id = int(config["order_category_ids"][typ])
                category = interaction.guild.get_channel(category_id)
                temp_channel = await interaction.guild.create_text_channel(
                    name=f"Bestellung_{typ}_{from_datum}_{to_datum}_{until}".replace(":", "-"),
                    category=category
                )

                dropdown_options = [
                    discord.SelectOption(
                        label=f'{opt["label"]} ({opt["price"]})',
                        value=opt["label"]
                    )
                    for opt in config["order_dropdown_options"][typ]
                ]

                class OrderDropdown(discord.ui.Select):
                    def __init__(self):
                        super().__init__(placeholder="Wähle ein Produkt", options=dropdown_options)
                        self.msg_id = None  # wird später durch set_msg_id() gesetzt

                    def set_msg_id(self, msg_id):
                        self.msg_id = msg_id

                    async def callback(self, drop_inter):
                        auswahl = self.values[0]

                        class MengeModal(discord.ui.Modal, title="Menge eingeben"):
                            menge = discord.ui.TextInput(label="Menge", placeholder="1-99", max_length=2)

                            def __init__(self, msg_id, temp_channel):
                                super().__init__()
                                self.msg_id = msg_id
                                self.temp_channel = temp_channel

                            async def on_submit(modalself2, iii):
                                menge = int(modalself2.menge.value)
                                item_embed_cfg = config["order_embeds"]["item"]
                                color = int(item_embed_cfg.get("color", "0"), 16)

                                user = iii.user
                                member = modalself2.temp_channel.guild.get_member(user.id)
                                voller_name = member.display_name if member else user.name

                                embed = discord.Embed(
                                    title=item_embed_cfg["title"].replace("{guild}", voller_name),
                                    description=item_embed_cfg["description"]
                                        .replace("{selection}", auswahl)
                                        .replace("{amount}", str(menge)),
                                    color=color
                                )
                                embed.set_footer(text=item_embed_cfg.get("footer", "").replace("{date}", datetime.now().strftime("%d.%m.%Y")))
                                msg = await modalself2.temp_channel.send(embed=embed)
                                view = ConfirmButton(msg)
                                await msg.edit(view=view)

                                active_orders[modalself2.msg_id]["items"].append({
                                    "user_id": str(iii.user.id),
                                    "selection": auswahl,
                                    "amount": menge,
                                    "message_id": msg.id
                                })

                                data = load_order_data(guild_id)
                                for o in data["orders"]:
                                    if o["id"] == active_orders[modalself2.msg_id]["order_id"]:
                                        o["items"].append({
                                            "user_id": str(iii.user.id),
                                            "selection": auswahl,
                                            "amount": menge,
                                            "message_id": msg.id
                                        })
                                        break
                                save_order_data(guild_id, data)
                                await iii.response.defer(ephemeral=True)
                                followup_msg = await iii.followup.send("✅ Bestellung gespeichert.", ephemeral=True)
                                await asyncio.sleep(10)
                                await followup_msg.delete()

                        await drop_inter.response.send_modal(MengeModal(self.msg_id, temp_channel))

                dropdown = OrderDropdown()
                view = discord.ui.View()
                view.add_item(dropdown)

                msg = await interaction.channel.send(embed=embed, view=view)

                # msg.id jetzt setzen
                dropdown.set_msg_id(msg.id)


                try:
                    end_dt = datetime.strptime(f"{to_datum} {until}", "%d.%m.%Y %H:%M")
                except ValueError:
                    await i.response.send_message("❌ Ungültiges Datum oder Uhrzeit. Bitte im Format TT.MM.JJJJ und HH:MM eingeben.", ephemeral=True)
                    return
                active_orders[msg.id] = {
                    "end": end_dt,
                    "guild_id": guild_id,
                    "channel_id": temp_channel.id,
                    "type": typ,
                    "items": [],
                    "order_id": None
                }

                data = load_order_data(guild_id)
                new_id = data["next_id"]
                data["next_id"] += 1
                data["orders"].append({
                    "id": new_id,
                    "type": typ,
                    "datum_von": from_datum,
                    "datum_bis": to_datum,
                    "uhrzeit_bis": until,
                    "message_id": msg.id,
                    "channel_id": temp_channel.id,
                    "items": []
                })
                save_order_data(guild_id, data)
                active_orders[msg.id]["order_id"] = new_id
                await i.response.send_message(f"✅ Bestellung erstellt in {temp_channel.mention}", ephemeral=True, delete_after=30)

        class OrderTypeView(discord.ui.View):
            @discord.ui.button(label="Schwarzmarkt", style=discord.ButtonStyle.primary, custom_id="modal_schwarzmarkt")
            async def schwarzmarkt(self, i, _): await i.response.send_modal(OrderModal(custom_id="modal_schwarzmarkt"))

            @discord.ui.button(label="Kurzwaffen", style=discord.ButtonStyle.primary, custom_id="modal_kurzwaffen")
            async def kurzwaffen(self, i, _): await i.response.send_modal(OrderModal(custom_id="modal_kurzwaffen"))

            @discord.ui.button(label="Langwaffen", style=discord.ButtonStyle.primary, custom_id="modal_langwaffen")
            async def langwaffen(self, i, _): await i.response.send_modal(OrderModal(custom_id="modal_langwaffen"))

        await interaction.response.send_message("Wähle den Bestelltyp:", view=OrderTypeView(), ephemeral=True, delete_after=30)

    for guild in bot.guilds:
        bot.tree.add_command(
            app_commands.Command(
                name="create_order",
                description="Erstellt eine neue Bestellung.",
                callback=create_order
            ),
            guild=discord.Object(id=guild.id)
        )
