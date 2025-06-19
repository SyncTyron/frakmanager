from db import load_json, save_json
def _get_data_key(mode: str) -> str:
    return f"{mode}_data"

def _load_data(guild_id: str, mode: str) -> dict:
    key = _get_data_key(mode)
    return load_json(guild_id, key, {"checklists": [], "next_id": 1})

def _save_data(guild_id: str, mode: str, data: dict):
    key = _get_data_key(mode)
    save_json(guild_id, key, data)

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
