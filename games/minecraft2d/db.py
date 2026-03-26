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
                flag_x     REAL,
                flag_y     REAL,
                PRIMARY KEY (world_id, player_idx)
            )
        """)
        # Migration : ajoute les colonnes flag si l'ancienne table n'en a pas
        existing = {row[1] for row in conn.execute("PRAGMA table_info(players)").fetchall()}
        if "flag_x" not in existing:
            conn.execute("ALTER TABLE players ADD COLUMN flag_x REAL")
        if "flag_y" not in existing:
            conn.execute("ALTER TABLE players ADD COLUMN flag_y REAL")


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
        conn.execute("DELETE FROM blocks  WHERE world_id = ?", (slot_id,))
        conn.execute("DELETE FROM players WHERE world_id = ?", (slot_id,))
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

def save_player(world_id, player_idx, x, y, inventory, flag=None, familiar=None):
    """
    Enregistre la position et l'inventaire d'un joueur.
    inventory : instance de scenes.game.inventory.Inventory
    flag      : (flag_x, flag_y) en tuiles ou None
    familiar  : dict {type, hp, egg} ou None
    """
    init()
    # Sérialisation JSON de l'inventaire
    resources_json = json.dumps(inventory.resources)
    # equip : clés converties en str pour JSON ({0: [...]} → {"0": [...]})
    # "sm" = sword_mat (None si pas d'épée)
    equip_raw = {str(k): [[item[0], item[1]] for item in v]
                 for k, v in inventory.equip.items()}
    equip_raw["ct"]  = inventory.craft_tier          # niveau table de craft
    equip_raw["tm"]  = inventory._tool_mat           # matériau outil actif
    equip_raw["fam"] = familiar                      # familier (dict ou None)
    equip_json = json.dumps(equip_raw)
    flag_x = flag[0] if flag else None
    flag_y = flag[1] if flag else None
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO players
                (world_id, player_idx, x, y, tool, resources, equip, flag_x, flag_y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (world_id, player_idx, x, y, inventory.tool,
              resources_json, equip_json, flag_x, flag_y))


def load_players(world_id):
    """
    Retourne un dict {player_idx: {x, y, tool, resources, equip}}
    pour tous les joueurs sauvegardés dans ce monde.
    equip est un dict {int_key: [(slot, mat), ...]}
    """
    init()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT player_idx, x, y, tool, resources, equip, flag_x, flag_y "
            "FROM players WHERE world_id = ?",
            (world_id,)
        ).fetchall()
    result = {}
    for player_idx, x, y, tool, res_json, eq_json, flag_x, flag_y in rows:
        resources = json.loads(res_json)   # [[tile, count], ...]
        eq_raw    = json.loads(eq_json)    # {"0": [[s, m], ...], "sm": ..., "pm": ...}
        # ── Migration des anciennes sauvegardes ─────────────────────────
        _has_sm = "sm" in eq_raw
        def _load_equip_list(raw):
            if isinstance(raw, dict):
                if "items" in raw:
                    return [tuple(x) for x in raw["items"]], raw.get("idx", 0)
                return [(m, 1) for m in raw.get("mats", [])], raw.get("idx", 0)
            if raw is not None:
                return [(raw, 1)], 0
            return [], 0
        sm_raw = eq_raw.pop("sm", None)
        pm_raw = eq_raw.pop("pm", None)
        bm_raw = eq_raw.pop("bm", None)
        _old_rod = "rod" in eq_raw
        has_rod  = bool(eq_raw.pop("rod", False))
        craft_tier = eq_raw.pop("ct", 1)
        tool_mat   = eq_raw.pop("tm", None)
        familiar   = eq_raw.pop("fam", None)
        equip = {int(k): [tuple(item) for item in v] for k, v in eq_raw.items()}
        # Migration : convertir épées/pioches/arcs en tiles-ressources
        if _has_sm:
            from config import EQUIP_TO_TILE, EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_BOW
            from config import TILE_FLAG, TILE_CRAFT, TILE_ROD
            swords, sword_idx     = _load_equip_list(sm_raw)
            pickaxes, pickaxe_idx = _load_equip_list(pm_raw)
            bows, bow_idx         = _load_equip_list(bm_raw)
            for lst, eslot in ((swords, EQUIP_SWORD), (pickaxes, EQUIP_PICKAXE), (bows, EQUIP_BOW)):
                for mat, count in lst:
                    tile = EQUIP_TO_TILE.get((eslot, mat))
                    if tile and not any(t == tile for t, _ in resources):
                        resources.append([tile, count])
            # Déduire tool_mat depuis l'ancien index
            if tool == 1 and pickaxes:  # TOOL_PICKAXE
                tool_mat = pickaxes[min(pickaxe_idx, len(pickaxes) - 1)][0]
            elif tool == 3 and swords:  # TOOL_SWORD
                tool_mat = swords[min(sword_idx, len(swords) - 1)][0]
            elif tool == 6 and bows:    # TOOL_BOW
                tool_mat = bows[min(bow_idx, len(bows) - 1)][0]
        if _old_rod:
            from config import TILE_FLAG, TILE_CRAFT, TILE_ROD
            if has_rod and not any(t == TILE_ROD for t, _ in resources):
                resources.append([TILE_ROD, 1])
            for _tile in (TILE_FLAG, TILE_CRAFT):
                if not any(t == _tile for t, _ in resources):
                    resources.append([_tile, 1])
        result[player_idx] = {
            "x": x, "y": y, "tool": tool,
            "tool_mat": tool_mat,
            "resources": resources,
            "equip": equip,
            "craft_tier": craft_tier,
            "flag": (flag_x, flag_y) if flag_x is not None and flag_y is not None else None,
            "familiar": familiar,
        }
    return result
