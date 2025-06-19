import os
import json
import sqlite3
from contextlib import closing

_DB_DIR = 'databases'
os.makedirs(_DB_DIR, exist_ok=True)


def _get_db_path(guild_id: str) -> str:
    return os.path.join(_DB_DIR, f"{guild_id}.db")


def _init(conn: sqlite3.Connection):
    with conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS json_data (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS verifications (Vorname TEXT, Nachname TEXT, Telefonnummer TEXT, Rang TEXT, Mitglied_seit TEXT, User_ID TEXT UNIQUE)"
        )


def get_conn(guild_id: str) -> sqlite3.Connection:
    path = _get_db_path(guild_id)
    conn = sqlite3.connect(path)
    _init(conn)
    return conn


def load_json(guild_id: str, key: str, default=None):
    with closing(get_conn(guild_id)) as conn:
        cur = conn.execute("SELECT value FROM json_data WHERE key=?", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
    return default if default is not None else {}


def save_json(guild_id: str, key: str, data) -> None:
    dump = json.dumps(data, ensure_ascii=False)
    with closing(get_conn(guild_id)) as conn:
        with conn:
            conn.execute(
                "REPLACE INTO json_data(key, value) VALUES (?, ?)",
                (key, dump),
            )


def is_user_verified(guild_id: str, user_id: str) -> bool:
    with closing(get_conn(guild_id)) as conn:
        cur = conn.execute(
            "SELECT 1 FROM verifications WHERE User_ID=? LIMIT 1",
            (user_id,),
        )
        return cur.fetchone() is not None


def add_verification(guild_id: str, entry: dict) -> None:
    with closing(get_conn(guild_id)) as conn:
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO verifications(Vorname, Nachname, Telefonnummer, Rang, Mitglied_seit, User_ID) VALUES (?,?,?,?,?,?)",
                (
                    entry.get("Vorname"),
                    entry.get("Nachname"),
                    entry.get("Telefonnummer"),
                    entry.get("Rang"),
                    entry.get("Mitglied seit"),
                    entry.get("User-ID"),
                ),
            )
