"""
Gestion des actions joueur : minage, placement, épée, drapeau.
Extrait de loop.py pour garder les fichiers sous 300 lignes.
"""
import random
import sounds as _sounds

from config import (
    TILE_AIR, TILE_CHEST, TILE_LAVA, TILE_WATER, TILE_FISH, TILE_TORCH, TILE_SIZE, REACH_RADIUS,
    TILE_HEART_CRYSTAL, TILE_TOTEM, TILE_BOOK, TILE_PORTAL_STONE, TILE_PORTAL, TILE_OBSIDIAN,
    TILE_DIRT, TILE_GRASS, TILE_FARMLAND,
    TILE_BUCKET_EMPTY, TILE_BUCKET_WATER,
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_BOW, TOOL_ROD, TOOL_TORCH,
    TOOL_HOE,
    TILE_BREAK_TIME, TILE_PICKAXE_TIER, MAT_TIER,
    EQUIP_NAMES, PLAYER_W, PLAYER_H, ROWS,
    SEED_TO_CROP, CROP_HARVEST, CROP_SEED_BACK, CROP_TILES,
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
        from scenes.game.player import effective_max_hp
        player.hp = effective_max_hp(player)
        _collect_drops(player, drops, loot_notifs)

    player._action_cd = 0.35
    _sounds.sword_hit()
    return True


def _swords_dmg(player):
    from config import MAT_WOOD
    from mobs.base import _SWORD_DMG
    from scenes.game.player import crystal_bonuses
    sm = player.inventory.sword_mat
    if sm is None:
        base = 1
    else:
        idx = min(sm, len(_SWORD_DMG) - 1)
        base = _SWORD_DMG[idx]
    return base + crystal_bonuses(player)[1]


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


def handle_bow(player, proj_mgr, loot_notifs, cur_mine, prev_mine, cur_mod, p_dir):
    """Tire une flèche à l'arc dans la direction tenue par le joueur."""
    if player.inventory.tool != TOOL_BOW:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False
    dx, dy = p_dir
    if dx == 0 and dy == 0:
        dx = 1   # direction par défaut : droite
    fired = proj_mgr.spawn(player, float(dx), float(dy))
    if fired:
        _sounds.sword_hit()
        player._action_cd = 0.5
    else:
        loot_notifs.append(["Pas de flèches !", 1.0, (220, 100, 80)])
        player._action_cd = 0.3
    return fired


def handle_consumable(player, loot_notifs, cur_mine, prev_mine, cur_mod):
    """Utilise un consommable (Cœur de cristal → +2 PV max)."""
    if player.inventory.tool != TOOL_HAND:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False
    sel = player.inventory.selected_tile()
    if sel == TILE_HEART_CRYSTAL:
        player.inventory.consume()
        player.max_hp += 2
        from scenes.game.player import effective_max_hp
        player.hp = min(player.hp + 2, effective_max_hp(player))
        player._action_cd = 0.5
        loot_notifs.append(["❤ +2 PV max !", 3.0, (220, 100, 255)])
        _sounds.chest_open()
        return True
    return False


_ROD_RANGE = 4   # distance max à l'eau pour pêcher (tuiles)


def handle_rod(player, world, loot_notifs, cur_mine, prev_mine, cur_mod):
    """Lance une ligne de pêche si de l'eau est à proximité."""
    if player.inventory.tool != TOOL_ROD:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False
    player._action_cd = 3.0   # délai réaliste entre deux lancers
    # Rechercher de l'eau dans un rayon
    cx = int(player.x + PLAYER_W / TILE_SIZE / 2)
    cy = int(player.y + PLAYER_H / TILE_SIZE / 2)
    found_water = False
    for dc in range(-_ROD_RANGE, _ROD_RANGE + 1):
        for dr in range(-_ROD_RANGE, _ROD_RANGE + 1):
            r = cy + dr
            if 0 <= r < ROWS and world.get(cx + dc, r) == TILE_WATER:
                found_water = True
                break
        if found_water:
            break
    if not found_water:
        loot_notifs.append(["Pas d'eau à portée !", 1.5, (100, 150, 220)])
        player._action_cd = 0.5
        return False
    _sounds.chest_open()
    if random.random() < 0.4:
        player.inventory.add(TILE_FISH)
        loot_notifs.append(["Pêché : Poisson ×1 !", 2.5, (60, 200, 200)])
    else:
        loot_notifs.append(["Rien de pêché...", 1.5, (140, 140, 140)])
    return True


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


def handle_torch(player, world, chunks, all_players, loot_notifs,
                 cur_col, cur_row, cur_mine, prev_mine, cur_mod, queue_block_fn):
    """Pose une torche depuis la main (TOOL_TORCH) à la position curseur."""
    if player.inventory.tool != TOOL_TORCH:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False
    if player.inventory.torch_count <= 0:
        loot_notifs.append(["Plus de torches !", 1.0, (220, 160, 50)])
        player._action_cd = 0.3
        return False
    if world.get(cur_col, cur_row) != TILE_AIR:
        return False
    occupied = any(
        int(p.x + PLAYER_W / TILE_SIZE / 2) == cur_col and
        int(p.y + PLAYER_H / TILE_SIZE / 2) == cur_row
        for p in all_players
    )
    if occupied:
        return False
    # Consomme une torche des ressources et la pose
    inv = player.inventory
    inv.resources = [(t, c - 1) if t == TILE_TORCH and c > 0 else (t, c)
                     for t, c in inv.resources]
    inv.resources = [(t, c) for t, c in inv.resources if c > 0]
    # Si plus de torches, revient à TOOL_HAND
    if inv.torch_count == 0:
        inv.tool = TOOL_HAND
    world.set(cur_col, cur_row, TILE_TORCH)
    chunks.update_tile(cur_col, cur_row, TILE_TORCH)
    for p in all_players:
        eject_from_blocks(p, world)
    player._action_cd = 0.25
    queue_block_fn(cur_col, cur_row, TILE_TORCH)
    _sounds.place()
    return True


def handle_hoe(player, world, chunks, loot_notifs,
               cur_col, cur_row, cur_mine, prev_mine, cur_mod, queue_block_fn):
    """Laboure la terre/herbe en terre labourée avec la houe."""
    if player.inventory.tool != TOOL_HOE:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False
    tile_at = world.get(cur_col, cur_row)
    if tile_at not in (TILE_DIRT, TILE_GRASS):
        return False
    world.set(cur_col, cur_row, TILE_FARMLAND)
    chunks.update_tile(cur_col, cur_row, TILE_FARMLAND)
    queue_block_fn(cur_col, cur_row, TILE_FARMLAND)
    player._action_cd = 0.3
    _sounds.place()
    return True


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

    # ── Seau : ramasser / poser de l'eau ─────────────────────────────────
    if tool == TOOL_PLACER and cur_mine and not prev_mine and not cur_mod:
        selected = player.inventory.selected_tile()
        if selected == TILE_BUCKET_EMPTY and tile_at == TILE_WATER:
            world.set(cur_col, cur_row, TILE_AIR)
            chunks.update_tile(cur_col, cur_row, TILE_AIR)
            queue_block_fn(cur_col, cur_row, TILE_AIR)
            # Remplacer seau vide → seau plein dans l'inventaire
            inv = player.inventory
            idx = inv.resource_idx
            t, c = inv.resources[idx]
            if c == 1:
                inv.resources[idx] = (TILE_BUCKET_WATER, 1)
            else:
                inv.resources[idx] = (t, c - 1)
                inv.add(TILE_BUCKET_WATER)
            player._action_cd = 0.3
            _sounds.place()
            return
        if selected == TILE_BUCKET_WATER and tile_at == TILE_AIR:
            world.set(cur_col, cur_row, TILE_WATER)
            chunks.update_tile(cur_col, cur_row, TILE_WATER)
            queue_block_fn(cur_col, cur_row, TILE_WATER)
            # Activer les liquides voisins
            for _ac, _ar in ((cur_col, cur_row - 1), (cur_col, cur_row + 1),
                             (cur_col - 1, cur_row), (cur_col + 1, cur_row)):
                if (_ac, _ar) not in world.mods and world.get(_ac, _ar) in (TILE_LAVA, TILE_WATER):
                    world.mods[(_ac, _ar)] = world.get(_ac, _ar)
            # Remplacer seau plein → seau vide
            inv = player.inventory
            idx = inv.resource_idx
            t, c = inv.resources[idx]
            if c == 1:
                inv.resources[idx] = (TILE_BUCKET_EMPTY, 1)
            else:
                inv.resources[idx] = (t, c - 1)
                inv.add(TILE_BUCKET_EMPTY)
            player._action_cd = 0.3
            _sounds.place()
            return

    # ── Placement ──────────────────────────────────────────────────────────
    if tool == TOOL_PLACER and cur_mine and not prev_mine and not cur_mod:
        if tile_at == TILE_AIR:
            selected = player.inventory.selected_tile()
            if selected != TILE_AIR:
                # Graines → planter sur terre labourée (le bloc en-dessous doit être FARMLAND)
                crop_tile = SEED_TO_CROP.get(selected)
                if crop_tile:
                    below = world.get(cur_col, cur_row + 1)
                    if below != TILE_FARMLAND:
                        loot_notifs.append(["Terre labourée requise !", 1.0, (180, 140, 60)])
                        player._action_cd = 0.3
                        return
                    # Vérifier eau à proximité (4 tiles)
                    _has_water = False
                    for _dc in range(-4, 5):
                        for _dr in range(-4, 5):
                            if world.get(cur_col + _dc, cur_row + 1 + _dr) == TILE_WATER:
                                _has_water = True
                                break
                        if _has_water:
                            break
                    if not _has_water:
                        loot_notifs.append(["Eau requise à proximité !", 1.0, (60, 140, 220)])
                        player._action_cd = 0.3
                        return
                    world.set(cur_col, cur_row, crop_tile)
                    chunks.update_tile(cur_col, cur_row, crop_tile)
                    player.inventory.consume()
                    player._action_cd = 0.3
                    queue_block_fn(cur_col, cur_row, crop_tile)
                    _sounds.place()
                    return
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
                    # Vérifier activation portail si c'est une Pierre de Portail
                    if selected == TILE_PORTAL_STONE:
                        if check_portal_activation(cur_col, cur_row, world, chunks, queue_block_fn):
                            loot_notifs.append(["Le portail s'active !", 3.0, (180, 100, 255)])
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

    # ── Récolte de cultures (main ou pioche, instantanée) ───────────────
    if tile_at in CROP_TILES and cur_mine and not cur_mod:
        world.set(cur_col, cur_row, TILE_AIR)
        chunks.update_tile(cur_col, cur_row, TILE_AIR)
        queue_block_fn(cur_col, cur_row, TILE_AIR)
        # Récolte mature → produits + graines
        harvest = CROP_HARVEST.get(tile_at)
        if harvest:
            from config import TILE_NAMES
            for item, mn, mx in harvest:
                count = random.randint(mn, mx)
                for _ in range(count):
                    player.inventory.add(item)
                if count > 0:
                    name = TILE_NAMES.get(item, "?")
                    loot_notifs.append([f"Récolte : {name} x{count}", 2.0, (120, 200, 60)])
        else:
            # Culture immature → rend la graine
            seed = CROP_SEED_BACK.get(tile_at)
            if seed:
                player.inventory.add(seed)
                from config import TILE_NAMES
                loot_notifs.append([f"Récupéré : {TILE_NAMES.get(seed, '?')}", 1.5, (180, 180, 100)])
        break_infos[i] = None
        player._break_time = 0.0
        player._action_cd = 0.2
        _sounds.mine_done()
        return

    # ── Minage (pioche ou mains) ─────────────────────────────────────────
    _UNMINABLE = (TILE_AIR, TILE_CHEST, TILE_LAVA, TILE_WATER, TILE_PORTAL)
    if tile_at not in _UNMINABLE and tool in (TOOL_PICKAXE, TOOL_HAND):
        if cur_mine and not cur_mod:
            # Vérification du tier (mains = tier 0)
            req_tier  = TILE_PICKAXE_TIER.get(tile_at, 0)
            player_t  = _pickaxe_tier(player) if tool == TOOL_PICKAXE else 0
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
                base = TILE_BREAK_TIME.get(tile_at, 0.5)
                req_time = base * 2.0 if tool == TOOL_HAND else base / max(1, player_t)
                progress = min(player._break_time / req_time, 1.0)
                break_infos[i] = (cur_col, cur_row, progress)
                if mine_tick_cd[i] <= 0.0:
                    _sounds.mine_tick()
                    mine_tick_cd[i] = 0.15
                if player._break_time >= req_time:
                    if world._cabin_tile(cur_col, cur_row) != TILE_AIR:
                        mob_mgr.trigger_cabin_break(cur_col)
                    # Minage d'herbe → chance de drop graines de blé
                    if tile_at == TILE_GRASS and random.random() < 0.30:
                        from config import TILE_SEED_WHEAT, TILE_NAMES
                        player.inventory.add(TILE_SEED_WHEAT)
                        loot_notifs.append([f"Trouvé : {TILE_NAMES[TILE_SEED_WHEAT]}", 1.5, (160, 180, 60)])
                    player.inventory.add(tile_at)
                    world.set(cur_col, cur_row, TILE_AIR)
                    chunks.update_tile(cur_col, cur_row, TILE_AIR)
                    break_infos[i]     = None
                    player._break_time = 0.0
                    player._action_cd  = 0.1
                    queue_block_fn(cur_col, cur_row, TILE_AIR)
                    # Activer les liquides voisins (pour qu'ils coulent au prochain tick)
                    for _ac, _ar in ((cur_col, cur_row - 1), (cur_col, cur_row + 1),
                                     (cur_col - 1, cur_row), (cur_col + 1, cur_row)):
                        if (_ac, _ar) not in world.mods and world.get(_ac, _ar) in (TILE_LAVA, TILE_WATER):
                            world.mods[(_ac, _ar)] = world.get(_ac, _ar)
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


# ── Lecture de livre ─────────────────────────────────────────────────────────

def handle_book(player, loot_notifs, cur_mine, prev_mine, cur_mod,
                book_state, dy=0, prev_dy=0):
    """Ouvre/ferme un livre. Scroll haut/bas. Cycle les textes à chaque ouverture."""
    if book_state.get("open"):
        # Scroll haut/bas
        if dy == -1 and prev_dy != -1:
            book_state["scroll"] = max(0, book_state.get("scroll", 0) - 1)
        elif dy == 1 and prev_dy != 1:
            max_scroll = max(0, len(book_state.get("text", [])) - book_state.get("max_vis", 18))
            book_state["scroll"] = min(max_scroll, book_state.get("scroll", 0) + 1)
        # Action ou Modifier ferme le livre
        if (cur_mine and not prev_mine) or cur_mod:
            book_state["open"] = False
            player._action_cd = 0.3
        return True
    if player.inventory.tool != TOOL_HAND:
        return False
    if player._action_cd > 0 or not cur_mine or prev_mine or cur_mod:
        return False
    sel = player.inventory.selected_tile()
    if sel != TILE_BOOK:
        return False
    # Ouvrir le livre suivant (cycle dans la collection)
    from config import BOOK_TEXTS
    idx = book_state.get("book_idx", 0)
    book_state["open"] = True
    book_state["text"] = BOOK_TEXTS[idx % len(BOOK_TEXTS)]
    book_state["book_idx"] = (idx + 1) % len(BOOK_TEXTS)
    book_state["scroll"] = 0
    player._action_cd = 0.3
    _sounds.chest_open()
    return True


# ── Activation portail (vérification du pattern) ────────────────────────────

def check_portal_activation(col, row, world, chunks, queue_block_fn):
    """Vérifie si le placement d'une PORTAL_STONE complète un portail valide.
    Pattern attendu (5 large × 2 haut) :
       OBS  STONE STONE STONE  OBS   ← row (ligne du haut)
       OBS  OBS   OBS   OBS   OBS   ← row+1 (sol)
    Si valide, les 3 PORTAL_STONEs deviennent TILE_PORTAL.
    """
    # Chercher les bornes de la série de PORTAL_STONEs contiguë
    left = col
    while world.get(left - 1, row) == TILE_PORTAL_STONE:
        left -= 1
    right = col
    while world.get(right + 1, row) == TILE_PORTAL_STONE:
        right += 1
    width = right - left + 1
    if width < 3:
        return False
    # Vérifier le cadre d'obsidienne
    # Murs gauche/droit
    if world.get(left - 1, row) != TILE_OBSIDIAN:
        return False
    if world.get(right + 1, row) != TILE_OBSIDIAN:
        return False
    # Sol complet sous le portail
    for c in range(left - 1, right + 2):
        if world.get(c, row + 1) != TILE_OBSIDIAN:
            return False
    # Activer le portail : convertir les PORTAL_STONEs en TILE_PORTAL
    for c in range(left, right + 1):
        world.set(c, row, TILE_PORTAL)
        chunks.update_tile(c, row, TILE_PORTAL)
        queue_block_fn(c, row, TILE_PORTAL)
    return True
