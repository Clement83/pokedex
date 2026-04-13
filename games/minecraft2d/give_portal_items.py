"""
give_portal_items.py
Ajoute à tous les joueurs sauvegardés (tous les mondes) :
  - 1 Livre ancien      (TILE_BOOK = 79)
  - 3 Pierres de Portail (TILE_PORTAL_STONE = 80)
  - 7 Obsidienne         (TILE_OBSIDIAN = 9)

Utilisation :
  python give_portal_items.py
  python give_portal_items.py --world 2        (monde 2 uniquement)
  python give_portal_items.py --world 1 --dry  (simulation sans écrire)
"""
import sqlite3
import json
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(__file__), "worlds.db")

TILE_OBSIDIAN    = 9
TILE_BOOK        = 79
TILE_PORTAL_STONE = 80

ITEMS_TO_GIVE = [
    (TILE_BOOK,         1),
    (TILE_PORTAL_STONE, 3),
    (TILE_OBSIDIAN,     7),
]


def add_items(resources: list, items: list) -> list:
    """Fusionne les items dans la liste resources (list of [tile, count])."""
    res = [list(r) for r in resources]
    for tile, qty in items:
        for entry in res:
            if entry[0] == tile:
                entry[1] += qty
                break
        else:
            res.append([tile, qty])
    return res


def run(world_filter=None, dry=False):
    if not os.path.exists(DB_PATH):
        print(f"Base de données introuvable : {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT world_id, player_idx, resources FROM players"
    ).fetchall()

    if not rows:
        print("Aucun joueur sauvegardé trouvé dans la base.")
        conn.close()
        return

    updated = 0
    for world_id, player_idx, res_json in rows:
        if world_filter is not None and world_id != world_filter:
            continue
        resources = json.loads(res_json)
        new_resources = add_items(resources, ITEMS_TO_GIVE)
        new_json = json.dumps(new_resources)
        label = f"Monde {world_id} / Joueur {player_idx}"
        if dry:
            print(f"[DRY] {label} → {new_resources}")
        else:
            conn.execute(
                "UPDATE players SET resources = ? WHERE world_id = ? AND player_idx = ?",
                (new_json, world_id, player_idx)
            )
            print(f"[OK]  {label} mis à jour")
        updated += 1

    if not dry:
        conn.commit()
    conn.close()

    if updated == 0:
        print("Aucun joueur ne correspond aux critères (monde introuvable ?).")
    else:
        print(f"\n{'Simulation' if dry else 'Injection'} terminée : {updated} joueur(s) traité(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Donne les items portail aux joueurs sauvegardés.")
    parser.add_argument("--world", type=int, default=None, help="Numéro du monde (1-4). Omis = tous.")
    parser.add_argument("--dry",   action="store_true",   help="Simulation sans écrire en BDD.")
    args = parser.parse_args()
    run(world_filter=args.world, dry=args.dry)
