
# checklist.py
import os
import json

def _get_data_path(guild_id: str, mode: str) -> str:
    folder = f"data/{guild_id}"
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{mode}_data.json")

def _load_data(guild_id: str, mode: str) -> dict:
    path = _get_data_path(guild_id, mode)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"checklists": [], "next_id": 1}

def _save_data(guild_id: str, mode: str, data: dict):
    path = _get_data_path(guild_id, mode)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def create_checklist_entry(guild_id, datum, uhrzeit, ort, members, mode="lineup"):
    data = _load_data(guild_id, mode)
    try:
        entries = {str(m.id): None for m in members}
    except AttributeError as e:
        raise TypeError("❌ FEHLER: 'members' muss eine Liste von discord.Member-Objekten sein, nicht von Strings.") from e

    checklist = {
        "id": data["next_id"],
        "datum": datum,
        "uhrzeit": uhrzeit,
        "ort": ort,
        "entries": entries
    }
    data["checklists"].append(checklist)
    data["next_id"] += 1
    _save_data(guild_id, mode, data)
    return checklist

def update_checklist_status(guild_id, checklist_id, user_id, status_data, mode="lineup"):
    data = _load_data(guild_id, mode)
    for cl in data["checklists"]:
        if cl["id"] == checklist_id:
            cl["entries"][str(user_id)] = status_data
            break
    _save_data(guild_id, mode, data)

def get_checklist(guild_id, checklist_id, mode="lineup"):
    data = _load_data(guild_id, mode)
    for cl in data["checklists"]:
        if cl["id"] == checklist_id:
            return cl
    return None
