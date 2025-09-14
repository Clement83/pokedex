import sqlite3
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_pokemon_list(conn):
    cur = conn.cursor()
    cur.execute("SELECT pokedex_id, name_fr, sprite_regular FROM pokemon ORDER BY pokedex_id")
    return cur.fetchall()

def get_pokemon_data(conn, pokedex_id):
    cur = conn.cursor()
    cur.execute("SELECT raw_json FROM pokemon WHERE pokedex_id=?", (pokedex_id,))
    row = cur.fetchone()
    if row:
        import json
        return json.loads(row[0])
    return None
