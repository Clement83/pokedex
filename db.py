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
    try:
        cur.execute("ALTER TABLE pokemon ADD COLUMN is_shiny BOOLEAN DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            raise
    try:
        cur.execute("ALTER TABLE pokemon ADD COLUMN times_caught INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass
        else:
            raise
    finally:
        conn.close()

def get_pokemon_list(conn, max_pokedex_id=None, include_mew=False):
    cur = conn.cursor()
    query = "SELECT pokedex_id, name_fr, sprite_regular, sprite_shiny, caught, is_shiny, times_caught FROM pokemon"
    conditions = []
    params = []

    if max_pokedex_id:
        conditions.append("pokedex_id <= ?")
        params.append(max_pokedex_id)

    if not include_mew:
        conditions.append("pokedex_id != 151")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY pokedex_id"

    cur.execute(query, tuple(params))
    return cur.fetchall()

def get_pokemon_data(conn, pokedex_id):
    cur = conn.cursor()
    cur.execute("SELECT raw_json FROM pokemon WHERE pokedex_id=?", (pokedex_id,))
    row = cur.fetchone()
    if row:
        import json
        return json.loads(row[0])
    return None

def update_pokemon_caught_status(conn, pokedex_id, caught, is_shiny=False):
    cur = conn.cursor()
    # Si la nouvelle capture est un shiny, on met à jour le statut shiny et on incrémente le compteur.
    # Cela empêche d'écraser un shiny précédemment capturé avec un normal.
    if is_shiny:
        cur.execute("UPDATE pokemon SET caught = ?, is_shiny = ?, times_caught = times_caught + 1 WHERE pokedex_id = ?", (caught, True, pokedex_id))
    else:
        # Si la capture n'est pas un shiny, on met à jour 'caught' et on incrémente le compteur,
        # préservant ainsi la valeur existante de 'is_shiny'.
        cur.execute("UPDATE pokemon SET caught = ?, times_caught = times_caught + 1 WHERE pokedex_id = ?", (caught, pokedex_id))
    conn.commit()

def get_caught_pokemon_count(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pokemon WHERE caught = 1")
    return cur.fetchone()[0]

def get_shiny_pokemon_count(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pokemon WHERE is_shiny = 1")
    return cur.fetchone()[0]

def mew_is_unlocked(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pokemon WHERE caught = 1 AND pokedex_id < 151")
    return cur.fetchone()[0] >= 150

def create_user_preferences_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user_preference(conn, key):
    cur = conn.cursor()
    cur.execute("SELECT value FROM user_preferences WHERE key=?", (key,))
    row = cur.fetchone()
    return row[0] if row else None

def set_user_preference(conn, key, value):
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
