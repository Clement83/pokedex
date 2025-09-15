import sqlite3
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def add_caught_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE pokemon ADD COLUMN caught BOOLEAN DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            raise
    finally:
        conn.close()

def get_pokemon_list(conn):
    cur = conn.cursor()
    cur.execute("SELECT pokedex_id, name_fr, sprite_regular, caught FROM pokemon ORDER BY pokedex_id")
    return cur.fetchall()

def get_pokemon_data(conn, pokedex_id):
    cur = conn.cursor()
    cur.execute("SELECT raw_json FROM pokemon WHERE pokedex_id=?", (pokedex_id,))
    row = cur.fetchone()
    if row:
        import json
        return json.loads(row[0])
    return None

def update_pokemon_caught_status(conn, pokedex_id, caught):
    cur = conn.cursor()
    cur.execute("UPDATE pokemon SET caught = ? WHERE pokedex_id = ?", (caught, pokedex_id))
    conn.commit()
