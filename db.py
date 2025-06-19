import json
from contextlib import closing
import mysql.connector
from mysql.connector import connect
from config_loader import get_db_params


def _init(conn):
    with conn.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS json_data (
                   `key` VARCHAR(255) PRIMARY KEY,
                   `value` LONGTEXT
               )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS verifications (
                   Vorname VARCHAR(255),
                   Nachname VARCHAR(255),
                   Telefonnummer VARCHAR(255),
                   Rang VARCHAR(255),
                   Mitglied_seit VARCHAR(255),
                   User_ID VARCHAR(255) UNIQUE
               )"""
        )
    conn.commit()

def get_conn(guild_id: str):
    params = get_db_params(guild_id)
    conn = connect(
        host=params.get("host", "localhost"),
        port=params.get("port", 3306),
        user=params.get("user"),
        password=params.get("password"),
        database=params.get("database"),
    )
    _init(conn)
    return conn


def load_json(guild_id: str, key: str, default=None):
    with closing(get_conn(guild_id)) as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM json_data WHERE `key`=%s", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
    return default if default is not None else {}


def save_json(guild_id: str, key: str, data) -> None:
    dump = json.dumps(data, ensure_ascii=False)
    with closing(get_conn(guild_id)) as conn, conn.cursor() as cur:
        cur.execute(
            "REPLACE INTO json_data(`key`, `value`) VALUES (%s, %s)",
            (key, dump),
        )
        conn.commit()


def is_user_verified(guild_id: str, user_id: str) -> bool:
    with closing(get_conn(guild_id)) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM verifications WHERE User_ID=%s LIMIT 1",
            (user_id,),
        )
        return cur.fetchone() is not None


def add_verification(guild_id: str, entry: dict) -> None:
    with closing(get_conn(guild_id)) as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT IGNORE INTO verifications
               (Vorname, Nachname, Telefonnummer, Rang, Mitglied_seit, User_ID)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                entry.get("Vorname"),
                entry.get("Nachname"),
                entry.get("Telefonnummer"),
                entry.get("Rang"),
                entry.get("Mitglied seit"),
                entry.get("User-ID"),
            ),
        )
        conn.commit()