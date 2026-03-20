"""
Persistance des mondes – SQLite.

Schéma :
  worlds(id INTEGER PK, seed INTEGER, created_at TEXT, last_played TEXT)
  blocks(world_id INTEGER, col INTEGER, row INTEGER, tile INTEGER,
         PRIMARY KEY (world_id, col, row))
  players(world_id INTEGER, player_idx INTEGER, x REAL, y REAL,
          tool INTEGER, resources TEXT, equip TEXT,
          PRIMARY KEY (world_id, player_idx))

"blocks" stocke uniquement les deltas par rapport au monde généré :
  - bloc posé par un joueur  → tile != TILE_AIR
  - bloc miné par un joueur  → tile  = TILE_AIR  (même si la génération avait mis autre chose)
On applique ces deltas après generate(seed) pour retrouver l'état exact.

"players" stocke la position et l'inventaire de chaque joueur (JSON).
"""
import sqlite3
import json
import os
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(__file__), "worlds.db")
MAX_WORLDS = 4


def _connect():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")   # plus robuste aux crash
    return conn


def init():
    """Crée les tables si elles n'existent pas encore."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS worlds (
                id          INTEGER PRIMARY KEY,
                seed        INTEGER NOT NULL,
                created_at  TEXT    NOT NULL,
                last_played TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                world_id  INTEGER NOT NULL,
                col       INTEGER NOT NULL,
                row       INTEGER NOT NULL,
                tile      INTEGER NOT NULL,
                PRIMARY KEY (world_id, col, row)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                world_id   INTEGER NOT NULL,
                player_idx INTEGER NOT NULL,
                x          REAL    NOT NULL,
                y          REAL    NOT NULL,
                tool       INTEGER NOT NULL DEFAULT 0,
                resources  TEXT    NOT NULL DEFAULT '[]',
                equip      TEXT    NOT NULL DEFAULT '{}',
                PRIMARY KEY (world_id, player_idx)
            )
        """)


def list_worlds():
    """
    Retourne une liste de 4 entrées (slots 1-4).
    Chaque entrée est soit None (vide) soit un dict
    {id, seed, created_at, last_played}.
    """
    init()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, seed, created_at, last_played FROM worlds ORDER BY id"
        ).fetchall()
    by_id = {r[0]: {"id": r[0], "seed": r[1], "created_at": r[2], "last_played": r[3]}
             for r in rows}
    return [by_id.get(i) for i in range(1, MAX_WORLDS + 1)]


def create_world(slot_id, seed):
    """Crée un nouveau monde dans le slot donné (1-4), écrase l'existant."""
    init()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _connect() as conn:
        conn.execute("DELETE FROM blocks WHERE world_id = ?", (slot_id,))
        conn.execute("""
            INSERT OR REPLACE INTO worlds (id, seed, created_at, last_played)
            VALUES (?, ?, ?, ?)
        """, (slot_id, seed, now, now))


def delete_world(slot_id):
    """Supprime un monde et tous ses blocs."""
    init()
    with _connect() as conn:
        conn.execute("DELETE FROM blocks   WHERE world_id = ?", (slot_id,))
        conn.execute("DELETE FROM players  WHERE world_id = ?", (slot_id,))
        conn.execute("DELETE FROM worlds   WHERE id = ?",       (slot_id,))


def touch_world(slot_id):
    """Met à jour last_played."""
    init()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _connect() as conn:
        conn.execute("UPDATE worlds SET last_played = ? WHERE id = ?", (now, slot_id))


def load_blocks(world_id):
    """
    Retourne un dict {(col, row): tile} des blocs modifiés.
    """
    init()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT col, row, tile FROM blocks WHERE world_id = ?", (world_id,)
        ).fetchall()
    return {(r[0], r[1]): r[2] for r in rows}


def save_block(world_id, col, row, tile):
    """
    Enregistre un delta de bloc.
    tile = TILE_AIR signifie "miné".
    """
    init()
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO blocks (world_id, col, row, tile)
            VALUES (?, ?, ?, ?)
        """, (world_id, col, row, tile))


def save_blocks_batch(world_id, changes):
    """
    Enregistre plusieurs deltas d'un coup.
    changes : list of (col, row, tile)
    """
    if not changes:
        return
    init()
    with _connect() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO blocks (world_id, col, row, tile)
            VALUES (?, ?, ?, ?)
        """, [(world_id, c, r, t) for c, r, t in changes])


# ── Persistance joueurs ───────────────────────────────────────────────────────

def save_player(world_id, player_idx, x, y, inventory):
    """
    Enregistre la position et l'inventaire d'un joueur.
    inventory : instance de scene_game.Inventory
    """
    init()
    # Sérialisation JSON de l'inventaire
    resources_json = json.dumps(inventory.resources)
    # equip : clés converties en str pour JSON ({0: [...]} → {"0": [...]})
    equip_raw = {str(k): [[item[0], item[1]] for item in v]
                 for k, v in inventory.equip.items()}
    equip_json = json.dumps(equip_raw)
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO players
                (world_id, player_idx, x, y, tool, resources, equip)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (world_id, player_idx, x, y, inventory.tool,
              resources_json, equip_json))


def load_players(world_id):
    """
    Retourne un dict {player_idx: {x, y, tool, resources, equip}}
    pour tous les joueurs sauvegardés dans ce monde.
    equip est un dict {int_key: [(slot, mat), ...]}
    """
    init()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT player_idx, x, y, tool, resources, equip "
            "FROM players WHERE world_id = ?",
            (world_id,)
        ).fetchall()
    result = {}
    for player_idx, x, y, tool, res_json, eq_json in rows:
        resources = json.loads(res_json)   # [[tile, count], ...]
        eq_raw    = json.loads(eq_json)    # {"0": [[s, m], ...], ...}
        equip = {int(k): [tuple(item) for item in v] for k, v in eq_raw.items()}
        result[player_idx] = {
            "x": x, "y": y, "tool": tool,
            "resources": resources,
            "equip": equip,
        }
    return result
