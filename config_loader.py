# config_loader.py
import json
import os

def load_config(guild_id):
    path = f"configs/config_{guild_id}.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"⚠️ Config für Guild {guild_id} wurde nicht gefunden.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
