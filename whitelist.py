### whitelist.py
whitelist = {
    "1371831566669578290": False,
    "1152595573359251497": True  # Beispiel-Guild-ID
}

def is_guild_whitelisted(guild_id):
    from logs import debug
    allowed = whitelist.get(str(guild_id), False)
    debug(f"Whitelist check for {guild_id}: {allowed}")
    return allowed