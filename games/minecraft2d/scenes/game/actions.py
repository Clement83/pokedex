"""
Gestion des actions joueur : minage, placement, épée, drapeau.
Extrait de loop.py pour garder les fichiers sous 300 lignes.
"""
import sounds as _sounds

from config import (
    TILE_AIR, TILE_CHEST, TILE_SIZE, REACH_RADIUS,
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG,
    TILE_BREAK_TIME, TILE_PICKAXE_TIER, MAT_TIER,
    EQUIP_NAMES, PLAYER_W, PLAYER_H,
)
from scenes.game.player import in_reach, eject_from_blocks


def _pickaxe_tier(player):
    """Retourne le tier de la pioche active (0 si aucune pioche)."""
    pm = player.inventory.pickaxe_mat
    if pm is None:
        return 0
    return MAT_TIER.get(pm, 0)


def _sword_tier(player):
    """Retourne le tier de l'épée active (0 si aucune)."""
    sm = player.inventory.sword_mat
    if sm is None:
        return 0
    return MAT_TIER.get(sm, 0)


def handle_sword(player, mob_mgr, loot_notifs, cur_mine, prev_mine, cur_mod):
    """Attaque à l'épée. Retourne True si un coup a été porté."""
    if player.inventory.tool != TOOL_SWORD:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False

    tier   = _sword_tier(player)
    dmg    = _swords_dmg(player)
    killed, drops, immune = mob_mgr.attack_near(
        player.x, player.y, REACH_RADIUS, dmg, sword_tier=tier
    )

    if immune > 0:
        loot_notifs.append(["⚔ IMMUNE !", 1.2, (255, 60, 60)])
    if killed > 0:
        player.hp = player.max_hp
        _collect_drops(player, drops, loot_notifs)

    player._action_cd = 0.35
    _sounds.sword_hit()
    return True


def _swords_dmg(player):
    from config import MAT_WOOD
    from mobs.base import _SWORD_DMG
    sm = player.inventory.sword_mat
    if sm is None:
        return 1
    idx = min(sm, len(_SWORD_DMG) - 1)
    return _SWORD_DMG[idx]


def _collect_drops(player, drops, loot_notifs):
    """Ajoute les drops dans l'inventaire du joueur et affiche les notifs."""
    for item, count in drops:
        if isinstance(item, tuple):
            # équipement (equip_slot, material)
            player.inventory.add_equip(item)
            name = EQUIP_NAMES.get(item, "?")
            loot_notifs.append([f"Drop : {name}", 2.5, (255, 210, 50)])
        else:
            # bloc/ressource
            for _ in range(count):
                player.inventory.add(item)
            from config import TILE_NAMES
            name = TILE_NAMES.get(item, "?")
            loot_notifs.append([f"Drop : {name} x{count}", 2.0, (180, 255, 120)])


def handle_flag(player, flag_positions, loot_notifs, cur_mine, prev_mine, cur_mod):
    """Pose le drapeau de respawn."""
    if player.inventory.tool != TOOL_FLAG:
        return
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return
    flag_positions[player.idx] = (player.x, player.y)
    player._action_cd = 0.4
    loot_notifs.append([f"Drapeau J{player.idx + 1} placé !", 2.0, player.color])
    _sounds.flag_place()


def handle_block_actions(
    player, i, world, chunks, mob_mgr, all_players,
    break_infos, mine_tick_cd, loot_notifs,
    cur_col, cur_row, cur_mine, prev_mine, cur_mod, dt,
    queue_block_fn,
):
    """
    Gestion du minage et placement de blocs.
    Modifie break_infos[i] et mine_tick_cd[i] sur place.
    """
    if player._action_cd > 0:
        return

    tile_at  = world.get(cur_col, cur_row)
    tool     = player.inventory.tool

    # ── Placement ──────────────────────────────────────────────────────────
    if tool == TOOL_PLACER and cur_mine and not prev_mine and not cur_mod:
        if tile_at == TILE_AIR:
            selected = player.inventory.selected_tile()
            if selected != TILE_AIR:
                occupied = any(
                    int(p.x + PLAYER_W / TILE_SIZE / 2) == cur_col and
                    int(p.y + PLAYER_H / TILE_SIZE / 2) == cur_row
                    for p in all_players
                )
                if not occupied:
                    world.set(cur_col, cur_row, selected)
                    chunks.update_tile(cur_col, cur_row, selected)
                    for p in all_players:
                        eject_from_blocks(p, world)
                    player.inventory.consume()
                    player._action_cd = 0.2
                    queue_block_fn(cur_col, cur_row, selected)
                    _sounds.place()
        return

    # ── Coffre (main) ──────────────────────────────────────────────────────
    if tile_at == TILE_CHEST and tool == TOOL_HAND and cur_mine and not cur_mod:
        if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
            player._break_time += dt
            progress = min(player._break_time / 0.6, 1.0)
            break_infos[i] = (cur_col, cur_row, progress)
            if player._break_time >= 0.6:
                # Profondeur pour le loot contextuel
                depth = cur_row - world.surface_at(cur_col)
                items = world.chest_loot(depth=max(0, depth))
                _collect_drops(player, items, loot_notifs)
                world.set(cur_col, cur_row, TILE_AIR)
                chunks.update_tile(cur_col, cur_row, TILE_AIR)
                break_infos[i]     = None
                player._break_time = 0.0
                player._action_cd  = 0.3
                queue_block_fn(cur_col, cur_row, TILE_AIR)
                _sounds.chest_open()
        else:
            player._break_time = 0.0
            break_infos[i]     = (cur_col, cur_row, 0.0)
        return

    # ── Minage (pioche) ────────────────────────────────────────────────────
    if tile_at != TILE_AIR and tile_at != TILE_CHEST and tool == TOOL_PICKAXE:
        if cur_mine and not cur_mod:
            # Vérification du tier
            req_tier  = TILE_PICKAXE_TIER.get(tile_at, 0)
            player_t  = _pickaxe_tier(player)
            if player_t < req_tier:
                # Pioche insuffisante : reset et feedback
                if not (break_infos[i] and break_infos[i][:2] == (cur_col, cur_row)):
                    from config import MAT_NAMES as _MN
                    needed = {v: k for k, v in {1: "Bois", 2: "Fer", 3: "Or", 4: "Diamant"}.items()}
                    tier_name = {1: "Bois", 2: "Fer", 3: "Or", 4: "Diamant"}.get(req_tier, "?")
                    loot_notifs.append([f"Pioche {tier_name} requise !", 1.0, (255, 120, 50)])
                break_infos[i]     = None
                player._break_time = 0.0
                return

            if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                player._break_time += dt
                req_time = TILE_BREAK_TIME.get(tile_at, 0.5) / player_t
                progress = min(player._break_time / req_time, 1.0)
                break_infos[i] = (cur_col, cur_row, progress)
                if mine_tick_cd[i] <= 0.0:
                    _sounds.mine_tick()
                    mine_tick_cd[i] = 0.15
                if player._break_time >= req_time:
                    if world._cabin_tile(cur_col, cur_row) != TILE_AIR:
                        mob_mgr.trigger_cabin_break(cur_col)
                    player.inventory.add(tile_at)
                    world.set(cur_col, cur_row, TILE_AIR)
                    chunks.update_tile(cur_col, cur_row, TILE_AIR)
                    break_infos[i]     = None
                    player._break_time = 0.0
                    player._action_cd  = 0.1
                    queue_block_fn(cur_col, cur_row, TILE_AIR)
                    _sounds.mine_done()
                    mine_tick_cd[i] = 0.0
            else:
                player._break_time = 0.0
                break_infos[i]     = (cur_col, cur_row, 0.0)
        else:
            break_infos[i]     = None
            player._break_time = 0.0
        return

    # ── Aucune action valide ───────────────────────────────────────────────
    if not cur_mine:
        break_infos[i]     = None
        player._break_time = 0.0
