"""
Boucle principale du jeu Minecraft 2D.
Lance une partie et retourne True (retour menu) ou None (quitter).
"""
import pygame
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))

from config import *
from world import generate
from quit_combo import QuitCombo
import db as _db
import sounds as _sounds
import music_player as _music
import mobs as _mobs
from mobs.familiar import FamiliarManager

from scenes.game.player      import Player, move_x, move_y, touching_wall, in_reach, eject_from_blocks, on_ice, in_lava, in_water, in_portal, effective_max_hp, crystal_bonuses
from scenes.game.camera      import Camera, ChunkCache
from scenes.game.controls    import joy_btn, get_dir_p1, get_dir_p2, get_cursor
from scenes.game.sky         import sky_color, night_alpha, is_night, draw_night_overlay, draw_sky_hud, DAY_CYCLE_DURATION, biome_sky_tint
from scenes.game.renderer_world  import draw_world, draw_cursor, draw_flag_in_world
from scenes.game.renderer_player import draw_player, draw_hearts, draw_compass, _HEART_W, _HEART_GAP
from scenes.game.renderer_hud    import draw_hotbar, HOTBAR_TOTAL, HOTBAR_SLOT_H as _HOTBAR_SLOT_H
from scenes.game.actions     import handle_sword, handle_flag, handle_block_actions, handle_bow, handle_rod, handle_torch, handle_consumable, handle_book, handle_hoe
from scenes.game.craft        import CraftMenu
from scenes.game.trade        import TradeMenu
from scenes.game.projectiles  import ProjectileManager


def run(screen, joysticks, world_id, seed):
    """Lance la partie. Retourne True (retour menu) ou None (quitter)."""
    clock      = pygame.time.Clock()
    quit_combo = QuitCombo()
    font_sm    = pygame.font.SysFont("Arial", 9)
    font_med   = pygame.font.SysFont("Arial", 11, bold=True)

    world = generate(seed); world_seed = world.seed
    world.mods.update(_db.load_blocks(world_id))
    saves = _db.load_players(world_id)
    chunks = ChunkCache(world); _day_time = [0.12]
    _pending = {}; _last_flush = [0.0]; _FLUSH = 2.0

    # Surfaces SRCALPHA pré-allouées (jamais réallouées dans la boucle)
    _dmg_surf_half = pygame.Surface((SCREEN_WIDTH // 2, SCREEN_HEIGHT), pygame.SRCALPHA)
    _dmg_surf_full = pygame.Surface((SCREEN_WIDTH,      SCREEN_HEIGHT), pygame.SRCALPHA)
    # Fond notif loot : réalloué uniquement si le texte change
    _notif_bg_surf = [None]   # [Surface|None]
    _notif_prev_w  = [0]

    # Labels statiques pré-rendus
    _seed_label = font_sm.render("seed: " + str(world_seed), True, (180, 180, 180))
    _mute_label = font_sm.render("[MUTE] P", True, (255, 80, 80))

    def _queue(col, row, tile): _pending[(col, row)] = tile

    def _flush():
        if _pending:
            _db.save_blocks_batch(world_id, [(c, r, t) for (c, r), t in _pending.items()])
            _pending.clear()
        for p in players:
            fam_data = fam_mgr.save_data(p.idx) if fam_mgr else None
            # Si dans l'arène boss, sauvegarder la position normale
            sx, sy = p.x, p.y
            sf = flag_positions[p.idx]
            if _boss_arena["in_arena"][p.idx] and _boss_arena["saved_pos"][p.idx]:
                sx, sy = _boss_arena["saved_pos"][p.idx]
                sf = _boss_arena["saved_flags"][p.idx]
            _db.save_player(world_id, p.idx, sx, sy, p.inventory,
                            flag=sf, familiar=fam_data)

    mid = 1_000_000; spawn_cols = [mid - 3, mid + 3]
    def _sx(col): return col - PLAYER_W / TILE_SIZE / 2
    def _sy(col): return world.surface_at(col) - PLAYER_H / TILE_SIZE - 1
    players = [Player(_sx(c), _sy(c), clr, idx)
               for idx, (c, clr) in enumerate(zip(spawn_cols, [P1_COLOR, P2_COLOR]))]
    for p in players: eject_from_blocks(p, world)
    flag_positions = [None, None]

    fam_mgr = FamiliarManager()

    for p in players:
        sv = saves.get(p.idx)
        if not sv: continue
        p.x, p.y = sv["x"], sv["y"]
        p.inventory.tool      = sv["tool"]
        p.inventory._tool_mat = sv.get("tool_mat")
        p.inventory.resources = [tuple(r) for r in sv["resources"]]
        p.inventory.craft_tier  = sv.get("craft_tier", 1)
        # Migration : anciennes armures stockées dans equip dict → resources
        from config import EQUIP_TO_TILE, EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET
        for armor_slot in (EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET):
            for piece in sv["equip"].get(armor_slot, []):
                tile = EQUIP_TO_TILE.get(tuple(piece))
                if tile:
                    p.inventory.add(tile)
        eject_from_blocks(p, world)
        if sv.get("flag") is not None: flag_positions[p.idx] = sv["flag"]
        fam_mgr.load_data(p.idx, sv.get("familiar"), p)

    HALF_W = SCREEN_WIDTH // 2; max_cy = ROWS * TILE_SIZE - SCREEN_HEIGHT
    shared_cam  = Camera()
    split_cams  = [Camera(view_w=HALF_W), Camera(view_w=HALF_W)]
    split_surfs = [screen.subsurface(pygame.Rect(0, 0, HALF_W, SCREEN_HEIGHT)),
                   screen.subsurface(pygame.Rect(HALF_W, 0, HALF_W, SCREEN_HEIGHT))]
    SPLIT_DIST = int(SCREEN_HEIGHT * 0.55); UNSPLIT_DIST = int(SCREEN_HEIGHT * 0.40); is_split = False
    shared_cam.x = max(0, (players[0].px() + players[1].px()) // 2 - SCREEN_WIDTH  // 2)
    shared_cam.y = max(0, min((players[0].py() + players[1].py()) // 2 - SCREEN_HEIGHT // 2, max_cy))
    for sc in split_cams: sc.x, sc.y = shared_cam.x, shared_cam.y
    chunks.preload_around(shared_cam.x, shared_cam.y, SCREEN_WIDTH)

    mob_mgr = _mobs.MobManager(world); _mob_cd = [0.0]
    joy1 = joysticks[0] if joysticks else None
    p_ctrl = [
        (joy1, J1_BTN_MINE, -1,            J1_BTN_MODIFIER, get_dir_p1, KB_J1_MINE, KB_J1_MODIFIER),
        (joy1, J2_BTN_MINE, J2_BTN_MINE2,  J2_BTN_MODIFIER, get_dir_p2, KB_J2_MINE, KB_J2_MODIFIER),
    ]
    p_dirs=[( 0,0),(0,0)]; break_infos=[None,None]; prev_mine=[False,False]
    prev_dx=[0,0]; prev_dy=[0,0]; mine_tick_cd=[0.0,0.0]
    prev_mod=[False,False]; mod_used=[False,False]  # détection tap sur modifier
    loot_notifs=[]; craft_menus=[CraftMenu(),CraftMenu()]; trade_menu=TradeMenu()
    proj_mgr = ProjectileManager()
    lava_dmg_cd = [0.0, 0.0]   # cooldown dégâts lave par joueur (1 PV/s)
    _liquid_cd = [0.0]         # tick physique liquides (lave/eau future)
    _crop_cd   = [0.0]         # tick croissance des cultures

    # ── Portail & Arène Boss ─────────────────────────────────────────────────
    _boss_arena = {
        "active": False,           # True si AU MOINS UN joueur dans l'arène
        "in_arena": [False, False], # par joueur
        "built": False,            # True si l'arène a déjà été construite
        "saved_pos": [None, None],  # positions sauvegardées [(x,y), (x,y)]
        "saved_flags": [None, None],
        "gorgon_spawned": False,
        "gorgon_dead": False,
        "portal_cd": 0.0,
    }
    _book_states = [{"open": False, "text": []}, {"open": False, "text": []}]

    def _build_boss_arena():
        """Construit l'arène boss dans le monde via world.mods."""
        if _boss_arena["built"]:
            return
        from config import BOSS_ARENA_COL, BOSS_ARENA_W, BOSS_ARENA_H, TILE_OBSIDIAN, TILE_STONE
        ac = BOSS_ARENA_COL
        ar_top = 50   # rangée du plafond
        # Cadre obsidienne + intérieur AIR
        for dc in range(BOSS_ARENA_W):
            for dr in range(BOSS_ARENA_H):
                c = ac + dc
                r = ar_top + dr
                if dc == 0 or dc == BOSS_ARENA_W - 1 or dr == 0 or dr == BOSS_ARENA_H - 1:
                    world.set(c, r, TILE_OBSIDIAN)
                    _queue(c, r, TILE_OBSIDIAN)
                else:
                    world.set(c, r, TILE_AIR)
                    _queue(c, r, TILE_AIR)
        # Sol en pierre tout en bas
        floor_row = ar_top + BOSS_ARENA_H - 2
        for dc in range(1, BOSS_ARENA_W - 1):
            world.set(ac + dc, floor_row, TILE_STONE)
            _queue(ac + dc, floor_row, TILE_STONE)
        # ── Bassin d'eau central (où la Gorgone est ancrée) ──────────────
        # Largeur 24 tuiles, profondeur 4, parois en pierre pour contenir l'eau
        pool_w     = 24
        pool_left  = ac + (BOSS_ARENA_W - pool_w) // 2
        pool_depth = 4
        # Parois latérales en pierre (rows floor_row-1 à floor_row-pool_depth)
        for dy in range(1, pool_depth + 1):
            world.set(pool_left - 1, floor_row - dy, TILE_STONE)
            _queue(pool_left - 1, floor_row - dy, TILE_STONE)
            world.set(pool_left + pool_w, floor_row - dy, TILE_STONE)
            _queue(pool_left + pool_w, floor_row - dy, TILE_STONE)
        # Eau à l'intérieur (au-dessus du sol stone, entre les parois)
        for dc in range(pool_w):
            for dy in range(1, pool_depth + 1):
                c = pool_left + dc
                r = floor_row - dy
                world.set(c, r, TILE_WATER)
                _queue(c, r, TILE_WATER)
        # ── 3 grands arbres-plateformes (tronc bois + couronnes feuilles) ─
        # Permettent au joueur de grimper jusqu'à la tête de la Gorgone (~20 tuiles)
        tree_cols = [ac + 5, ac + BOSS_ARENA_W - 6, ac + BOSS_ARENA_W // 2 - 12]
        water_top_row = floor_row - pool_depth   # rangée juste au-dessus de l'eau
        for tc in tree_cols:
            # Tronc : depuis water_top_row - 1 jusqu'à 22 rangées au-dessus du sol
            for dy in range(1, 23):
                r = floor_row - dy
                # Évite d'écraser l'eau si l'arbre est dans le bassin
                if pool_left <= tc <= pool_left + pool_w - 1 and dy <= pool_depth:
                    continue
                world.set(tc, r, TILE_WOOD)
                _queue(tc, r, TILE_WOOD)
            # Branches/plateformes en feuillage à différentes hauteurs
            for branch_dy in (6, 11, 16, 21):
                br = floor_row - branch_dy
                for dx in range(-3, 4):
                    if dx == 0:
                        continue   # ne pas écraser le tronc
                    c = tc + dx
                    if not (ac < c < ac + BOSS_ARENA_W - 1):
                        continue
                    world.set(c, br, TILE_GRASS)
                    _queue(c, br, TILE_GRASS)
        # Portail de retour (en haut à gauche, sur le 1er arbre)
        ret_col = ac + 3
        ret_row = ar_top + 3
        for dc in range(3):
            world.set(ret_col + dc, ret_row, TILE_PORTAL)
            _queue(ret_col + dc, ret_row, TILE_PORTAL)
        # Encadrer le portail
        world.set(ret_col - 1, ret_row, TILE_OBSIDIAN)
        _queue(ret_col - 1, ret_row, TILE_OBSIDIAN)
        world.set(ret_col + 3, ret_row, TILE_OBSIDIAN)
        _queue(ret_col + 3, ret_row, TILE_OBSIDIAN)
        for dc in range(-1, 4):
            world.set(ret_col + dc, ret_row + 1, TILE_OBSIDIAN)
            _queue(ret_col + dc, ret_row + 1, TILE_OBSIDIAN)
        _boss_arena["built"] = True

    def _teleport_to_boss(player_idx):
        """Téléporte un joueur dans l'arène boss."""
        from config import BOSS_ARENA_COL, BOSS_ARENA_H
        _build_boss_arena()
        p = players[player_idx]
        # Sauvegarder position du joueur concerné
        _boss_arena["saved_pos"][player_idx] = (p.x, p.y)
        _boss_arena["saved_flags"][player_idx] = flag_positions[player_idx]
        # Téléporter dans l'arène (côté gauche, entre le mur et le 1er arbre)
        ac = BOSS_ARENA_COL
        ar_floor = 50 + BOSS_ARENA_H - 3   # ar_top=50, même valeur que _build_boss_arena
        p.x = float(ac + 2 + player_idx)
        p.y = float(ar_floor - 2)
        p.vx = p.vy = 0.0
        eject_from_blocks(p, world)
        _boss_arena["in_arena"][player_idx] = True
        _boss_arena["active"] = any(_boss_arena["in_arena"])
        chunks._cache.clear()
        chunks._pending.clear()
        _boss_arena["portal_cd"] = 2.0
        # Spawn Gorgone si pas présente dans le monde (morte ou despawnée)
        from mobs.base import Mob, MOB_GORGON, _mw
        gorgon_alive = any(m.mob_type == MOB_GORGON for m in mob_mgr._mobs)
        if not gorgon_alive:
            _body_h = 20
            gc = ac + BOSS_ARENA_W // 2
            gfloor = ar_floor
            gm = Mob(float(gc), float(gfloor - _body_h), MOB_GORGON, world.seed)
            gm._anchor_x = gc + _mw(MOB_GORGON) / 2
            gm._anchor_row = float(gfloor)
            mob_mgr._mobs.append(gm)
            _boss_arena["gorgon_spawned"] = True
            _boss_arena["gorgon_dead"] = False
        loot_notifs.append(["Vous entrez dans le repaire de la Gorgone...", 4.0, (180, 100, 255)])

    def _teleport_back(player_idx):
        """Ramène un joueur au monde normal."""
        p = players[player_idx]
        saved = _boss_arena["saved_pos"][player_idx]
        if saved:
            p.x, p.y = saved
        flag_positions[player_idx] = _boss_arena["saved_flags"][player_idx]
        p.vx = p.vy = 0.0
        eject_from_blocks(p, world)
        _boss_arena["in_arena"][player_idx] = False
        _boss_arena["active"] = any(_boss_arena["in_arena"])
        chunks._cache.clear()
        chunks._pending.clear()
        _boss_arena["portal_cd"] = 2.0
        # Vider les crachats si plus aucun joueur dans l'arène
        if not _boss_arena["active"]:
            from mobs.deep import clear_gorgon_spits
            clear_gorgon_spits()
        loot_notifs.append(["Retour au monde normal.", 3.0, (100, 200, 255)])

    def _check_gorgon_dead():
        """Marque la Gorgone comme morte ; respawn au prochain TP dans le repaire."""
        from mobs.base import MOB_GORGON
        if _boss_arena["gorgon_dead"] or not _boss_arena["gorgon_spawned"]:
            return
        if not _boss_arena["active"]:
            return
        alive = any(m.mob_type == MOB_GORGON for m in mob_mgr._mobs)
        if not alive:
            _boss_arena["gorgon_dead"] = True
            loot_notifs.append(["La Gorgone est vaincue !", 5.0, (255, 220, 50)])

    _BOOK_LINE_H = 12
    _BOOK_PAD    = 10
    _BOOK_FOOTER = 16    # hauteur réservée pour la légende en bas

    def _draw_book_overlay(surf, book_state, font):
        """Dessine l'overlay de lecture de livre avec scroll."""
        if not book_state.get("open"):
            return
        lines = book_state.get("text", [])
        bw = min(220, surf.get_width() - 10)
        bh = min(280, SCREEN_HEIGHT - 20)
        bx = (surf.get_width() - bw) // 2
        by = (SCREEN_HEIGHT - bh) // 2

        # Nombre de lignes visibles
        text_area_h = bh - _BOOK_PAD * 2 - _BOOK_FOOTER
        max_vis = max(1, text_area_h // _BOOK_LINE_H)
        book_state["max_vis"] = max_vis
        scroll = book_state.get("scroll", 0)
        max_scroll = max(0, len(lines) - max_vis)
        scroll = min(scroll, max_scroll)

        # Fond parchemin
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((40, 30, 20, 230))
        surf.blit(bg, (bx, by))
        pygame.draw.rect(surf, (160, 120, 60), (bx, by, bw, bh), 2)

        # Texte visible (fenêtre scrollée)
        ty = by + _BOOK_PAD
        visible = lines[scroll:scroll + max_vis]
        for line in visible:
            if line:
                lbl = font.render(line, True, (220, 200, 160))
                surf.blit(lbl, (bx + _BOOK_PAD, ty))
            ty += _BOOK_LINE_H

        # Barre de scroll (si nécessaire)
        if max_scroll > 0:
            bar_x = bx + bw - 6
            bar_top = by + _BOOK_PAD
            bar_h = text_area_h
            # Rail
            pygame.draw.rect(surf, (80, 60, 40), (bar_x, bar_top, 4, bar_h))
            # Curseur
            thumb_h = max(8, int(bar_h * max_vis / len(lines)))
            thumb_y = bar_top + int((bar_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(surf, (200, 170, 100), (bar_x, thumb_y, 4, thumb_h))

        # Légende
        has_scroll = max_scroll > 0
        legend = "nav  Action/Alt=fermer" if has_scroll else "Action/Alt=fermer"
        close_lbl = font.render(legend, True, (140, 120, 80))
        surf.blit(close_lbl, (bx + bw // 2 - close_lbl.get_width() // 2,
                               by + bh - _BOOK_FOOTER + 2))

    # Dirty flags caméra pour éviter preload_around si la cam n'a pas bougé
    _preload_last = {}   # {cam_id: (x, y)}

    def _preload_if_moved(cam, view_w):
        key  = id(cam)
        prev = _preload_last.get(key)
        cur  = (int(cam.x), int(cam.y))
        if prev != cur:
            chunks.preload_around(cam.x, cam.y, view_w)
            _preload_last[key] = cur

    def _draw_view(surf, cam, view_w, k, bi):
        center_col = int((cam.x + view_w // 2) / TILE_SIZE)
        if _boss_arena["active"]:
            surf.fill((15, 5, 25))   # ciel sombre violet pour l'arène boss
        else:
            _biome = world.biome_at(center_col)
            surf.fill(biome_sky_tint(_sky_c, _biome))
        _preload_if_moved(cam, view_w)
        draw_world(surf, chunks, cam, bi)
        for j, pl in enumerate(players):
            if pl.inventory.tool != TOOL_SWORD:
                c2, r2 = get_cursor(pl, *p_dirs[j], world)
                r2 = max(0, min(ROWS - 1, r2))
                if in_reach(pl, c2, r2): draw_cursor(surf, pl, c2, r2, cam)
        for fi, fp in enumerate(flag_positions):
            if fp: draw_flag_in_world(surf, fp[0], fp[1], players[fi].color, cam)
        mob_mgr.draw(surf, cam)
        from mobs.deep import draw_gorgon_spits
        draw_gorgon_spits(surf, cam.x, cam.y)
        fam_mgr.draw(surf, cam)
        proj_mgr.draw(surf, cam)
        for pl in players: draw_player(surf, pl, cam, font_sm)
        pi = players[k]
        if pi._dmg_flash > 0:
            _ds = _dmg_surf_half if view_w < SCREEN_WIDTH else _dmg_surf_full
            _ds.fill((200, 0, 0, min(140, int(140 * pi._dmg_flash / 0.4))))
            surf.blit(_ds, (0, 0))
        _hy = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
        draw_hotbar(surf, pi.inventory, 4, pi.color, font_sm)
        draw_hearts(surf, pi.hp, effective_max_hp(pi), 4 + HOTBAR_TOTAL + 4, _hy)
        if view_w < SCREEN_WIDTH: draw_compass(surf, cam, pi, players[1 - k], view_w, players[1 - k].color)
        if craft_menus[k].visible: craft_menus[k].draw(surf, pi.inventory, pi.color, font_sm)
        _draw_book_overlay(surf, _book_states[k], font_sm)

    # ─────────────────────────────────────────────────────────────────────────
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        _day_time[0] = (_day_time[0] + dt / DAY_CYCLE_DURATION) % 1.0
        _sky_c = sky_color(_day_time[0]); _is_nite = is_night(_day_time[0])
        _last_flush[0] += dt
        if _last_flush[0] >= _FLUSH: _flush(); _last_flush[0] = 0.0
        mine_tick_cd[0] = max(0.0, mine_tick_cd[0] - dt)
        mine_tick_cd[1] = max(0.0, mine_tick_cd[1] - dt)

        events = pygame.event.get(); keys = pygame.key.get_pressed()
        _music.tick(events)
        _sounds.tick(events)
        for e in events:
            if e.type == pygame.QUIT: _flush(); return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: _flush(); return True
                if e.key == pygame.K_p: _sounds.toggle_mute(); _music.toggle_mute()
                # ── DEBUG F4 : force spawn Gorgone sous le joueur 1 ──────────
                if e.key == pygame.K_F4:
                    from mobs.base import Mob, MOB_GORGON, _mw
                    _body_h = 20         # GORGON_BODY_HEIGHT tiles
                    _gc     = int(players[0].x)
                    _gfloor = int(players[0].y) + _body_h + 4
                    _gfloor = min(_gfloor, ROWS - 2)
                    # Creuser une cavité 7 tiles large, body_h+3 tiles de haut
                    for _gr in range(_gfloor - _body_h - 2, _gfloor + 2):
                        for _gdc in range(-3, 4):
                            _tc = _gc + _gdc
                            if world.get(_tc, _gr) not in (TILE_AIR, TILE_LAVA, TILE_WATER):
                                world.set(_tc, _gr, TILE_AIR)
                                chunks.update_tile(_tc, _gr, TILE_AIR)
                    _gmw = _mw(MOB_GORGON)
                    _gm  = Mob(float(_gc), float(_gfloor - _body_h), MOB_GORGON, world.seed)
                    _gm._anchor_x   = _gc + _gmw / 2
                    _gm._anchor_row = float(_gfloor)
                    mob_mgr._mobs.append(_gm)
                    loot_notifs.append(["[DEBUG] Gorgone spawned !", 2.5, (0, 240, 100)])
            quit_combo.handle_event(e)

        for i, player in enumerate(players):
            player.inventory.ensure_valid_tool()
            joy, btn_mine, btn_mine2, btn_mod, get_dir, kb_mine, kb_mod = p_ctrl[i]
            dx, dy   = get_dir(keys, joy)
            cur_mine = joy_btn(joy, btn_mine) or joy_btn(joy, btn_mine2) or bool(keys[kb_mine])
            cur_mod  = joy_btn(joy, btn_mod)  or bool(keys[kb_mod])

            # ── Menu troc actif : immobilise le joueur, passe les contrôles troc ────
            if trade_menu.visible:
                if dy == -1 and prev_dy[i] != -1: trade_menu.navigate(i, -1)
                elif dy == 1 and prev_dy[i] != 1: trade_menu.navigate(i, 1)
                if cur_mine and not prev_mine[i]:
                    msg = trade_menu.give(i, players)
                    if msg: loot_notifs.append([msg, 2.5, player.color])
                if cur_mod: trade_menu.close()
                player.vx = 0.0
                player.vy = min(player.vy + GRAVITY * dt, MAX_FALL_SPEED)
                player.on_ground = False
                move_y(player, world, player.vy * dt)
                if player._action_cd > 0: player._action_cd -= dt
                prev_mine[i] = cur_mine; prev_mod[i] = cur_mod; prev_dy[i] = dy; prev_dx[i] = dx
                continue

            # ── Ouverture troc : outil Main + action + joueurs adjacents ──────────
            if (player.inventory.tool == TOOL_HAND and cur_mine and not prev_mine[i]
                    and not craft_menus[i].visible):
                other = players[1 - i]
                if abs(player.x - other.x) < 2.5 and abs(player.y - other.y) < 2.5:
                    trade_menu.open()
                    if not is_split:
                        is_split = True
                        for k, cam in enumerate(split_cams):
                            cam.x = max(0, players[k].px() - HALF_W // 2)
                            cam.y = max(0, min(players[k].py() - SCREEN_HEIGHT // 2, max_cy))
                    prev_mine[i] = cur_mine; prev_mod[i] = cur_mod; prev_dy[i] = dy; prev_dx[i] = dx
                    continue
                # ── Apprivoisement familier (Main + action, pas de troc) ─────
                if fam_mgr.try_tame(player, i, mob_mgr, loot_notifs):
                    prev_mine[i] = cur_mine; prev_mod[i] = cur_mod; prev_dy[i] = dy; prev_dx[i] = dx
                    player._action_cd = 0.5
                    continue

            # ── Ouverture menu craft (outil actif = Table de Craft + action) ────────
            just_opened = False
            if player.inventory.tool == TOOL_CRAFT and cur_mine and not prev_mine[i]:
                if not craft_menus[i].visible:
                    craft_menus[i].toggle(); just_opened = True
                    if not is_split:
                        is_split = True
                        for k, cam in enumerate(split_cams):
                            cam.x = max(0, players[k].px() - HALF_W // 2)
                            cam.y = max(0, min(players[k].py() - SCREEN_HEIGHT // 2, max_cy))

            if craft_menus[i].visible:
                if dy == -1 and prev_dy[i] != -1: craft_menus[i].navigate(-1)
                elif dy == 1 and prev_dy[i] != 1: craft_menus[i].navigate(1)
                if cur_mine and not prev_mine[i] and not just_opened:
                    name = craft_menus[i].craft(player.inventory)
                    msg  = (f"Crafté : {name} !" if name else "Ressources insuffisantes")
                    col2 = player.color if name else (200, 80, 80)
                    loot_notifs.append([msg, 2.5 if name else 1.0, col2])
                    if name: _sounds.chest_open()
                if cur_mod: craft_menus[i].close()
                prev_mine[i] = cur_mine; prev_mod[i] = cur_mod; prev_dy[i] = dy; prev_dx[i] = dx; continue

            _on_ice = on_ice(player, world)
            if cur_mod:
                if dx ==  1 and prev_dx[i] !=  1: player.inventory.slot_next();  _sounds.inv_change(); mod_used[i] = True
                elif dx == -1 and prev_dx[i] != -1: player.inventory.slot_prev(); _sounds.inv_change(); mod_used[i] = True
                if dy == -1 and prev_dy[i] != -1: player.inventory.item_prev();  _sounds.inv_change(); mod_used[i] = True
                elif dy == 1 and prev_dy[i] != 1: player.inventory.item_next();  _sounds.inv_change(); mod_used[i] = True
                if cur_mine: mod_used[i] = True   # action pendant modifier = pas un tap
                player.vx = 0.0
            else:
                # Tap modifier (relâché sans avoir utilisé de direction) → défiler outil
                if prev_mod[i] and not mod_used[i]:
                    saved = player.inventory.active_slot
                    player.inventory.active_slot = 0
                    player.inventory.item_next()
                    player.inventory.active_slot = saved
                    _sounds.inv_change()
                mod_used[i] = False
                _speed = WALK_SPEED + crystal_bonuses(player)[2]
                if _on_ice:
                    # Glace : inertie — accélération lente, friction faible
                    target = dx * _speed
                    player.vx += (target - player.vx) * 2.5 * dt
                    if abs(dx) < 0.1:
                        player.vx *= (1.0 - 0.8 * dt)  # friction douce quand aucune touche
                else:
                    player.vx = dx * _speed
            if dx or dy: p_dirs[i] = (dx, dy)
            prev_dx[i] = dx; prev_dy[i] = dy

            player.on_wall = touching_wall(player, world)
            if dy < 0 and player.on_wall and not player.on_ground and not cur_mod:
                player.vy = -CLIMB_SPEED
            else:
                if dy < 0 and player.on_ground and not cur_mod: player.vy = JUMP_VEL; _sounds.jump()
                player.vy = min(player.vy + GRAVITY * dt, MAX_FALL_SPEED)
            player.on_ground = False
            move_x(player, world, player.vx * dt); move_y(player, world, player.vy * dt)
            if player._action_cd > 0: player._action_cd -= dt

            cdx, cdy = p_dirs[i]
            cur_col, cur_row = get_cursor(player, cdx, cdy, world)
            cur_row = max(0, min(ROWS - 1, cur_row))
            # ── Lecture de livre ──────────────────────────────────────────────
            _book_just_opened = not _book_states[i].get("open")
            if handle_book(player, loot_notifs, cur_mine, prev_mine[i], cur_mod,
                           _book_states[i], dy, prev_dy[i]):
                # Forcer le split-screen à l'ouverture (comme craft menu)
                if _book_just_opened and _book_states[i].get("open") and not is_split:
                    is_split = True
                    for k, cam in enumerate(split_cams):
                        cam.x = max(0, players[k].px() - HALF_W // 2)
                        cam.y = max(0, min(players[k].py() - SCREEN_HEIGHT // 2, max_cy))
                prev_mine[i] = cur_mine; prev_mod[i] = cur_mod; prev_dy[i] = dy; prev_dx[i] = dx
                continue
            handle_sword(player, mob_mgr, loot_notifs, cur_mine, prev_mine[i], cur_mod)
            handle_bow(player, proj_mgr, loot_notifs, cur_mine, prev_mine[i], cur_mod, p_dirs[i])
            handle_flag(player, flag_positions, loot_notifs, cur_mine, prev_mine[i], cur_mod)
            handle_consumable(player, loot_notifs, cur_mine, prev_mine[i], cur_mod)
            handle_rod(player, world, loot_notifs, cur_mine, prev_mine[i], cur_mod)
            handle_torch(player, world, chunks, players, loot_notifs,
                         cur_col, cur_row, cur_mine, prev_mine[i], cur_mod, _queue)
            if in_reach(player, cur_col, cur_row):
                handle_hoe(player, world, chunks, loot_notifs,
                           cur_col, cur_row, cur_mine, prev_mine[i], cur_mod, _queue)
            if in_reach(player, cur_col, cur_row) and player.inventory.tool not in (TOOL_SWORD, TOOL_TORCH, TOOL_HOE):
                handle_block_actions(player, i, world, chunks, mob_mgr, players,
                    break_infos, mine_tick_cd, loot_notifs,
                    cur_col, cur_row, cur_mine, prev_mine[i], cur_mod, dt, _queue)
            elif not cur_mine: break_infos[i] = None; player._break_time = 0.0
            prev_mine[i] = cur_mine; prev_mod[i] = cur_mod

        for player in players:
            player._dmg_flash = max(0.0, player._dmg_flash - dt)
            # Cap HP si le joueur retire son armure cristal
            _eff = effective_max_hp(player)
            if player.hp > _eff:
                player.hp = _eff
        # ── Dégâts de lave (1 PV par seconde) ────────────────────────────
        for i, player in enumerate(players):
            if in_lava(player, world):
                player.vy = min(player.vy, MAX_FALL_SPEED * 0.3)  # ralentit dans la lave
                lava_dmg_cd[i] -= dt
                if lava_dmg_cd[i] <= 0:
                    player.hp -= 1
                    player._dmg_flash = 0.4
                    lava_dmg_cd[i] = 1.0
            else:
                lava_dmg_cd[i] = 0.0  # reset : premiers dégâts immédiats
            # Eau : ralentit la chute et le déplacement
            if in_water(player, world):
                player.vy = min(player.vy, MAX_FALL_SPEED * 0.25)
                player.vx *= 0.85
        for i, player in enumerate(players):
            if player.hp <= 0 or player.y * TILE_SIZE > ROWS * TILE_SIZE + 64:
                # Totem de résurrection : revit sur place au lieu de respawn
                from config import TILE_TOTEM
                totem_used = False
                if player.hp <= 0:
                    new_res = []
                    for t, c in player.inventory.resources:
                        if t == TILE_TOTEM and not totem_used:
                            totem_used = True
                            if c > 1:
                                new_res.append((t, c - 1))
                        else:
                            new_res.append((t, c))
                    if totem_used:
                        player.inventory.resources = new_res
                        player.hp = effective_max_hp(player)
                        player._dmg_flash = 0.6
                        loot_notifs.append(["✟ TOTEM ! Résurrection !", 3.0, (255, 220, 100)])
                if not totem_used:
                    player.hp = effective_max_hp(player)
                    if _boss_arena["in_arena"][i]:
                        # Mort dans l'arène : retour au monde normal
                        _teleport_back(i)
                        loot_notifs.append(["Vous avez fui le repaire...", 3.0, (200, 80, 80)])
                    else:
                        fp = flag_positions[i]
                        if fp: player.x, player.y = fp
                        else:  player.x = _sx(spawn_cols[i]); player.y = _sy(spawn_cols[i])
                    player.vx = player.vy = 0.0; eject_from_blocks(player, world)

        # ── Détection portail ────────────────────────────────────────────
        _boss_arena["portal_cd"] = max(0.0, _boss_arena["portal_cd"] - dt)
        if _boss_arena["portal_cd"] <= 0:
            for pi, p in enumerate(players):
                if in_portal(p, world):
                    if not _boss_arena["in_arena"][pi]:
                        _teleport_to_boss(pi)
                    else:
                        _teleport_back(pi)
                    break
        # Vérifier si la Gorgone est morte
        _check_gorgon_dead()

        _mob_cd[0] -= dt
        if _mob_cd[0] <= 0:
            mob_mgr.spawn_around(list({int(p.x) for p in players}), _is_nite); _mob_cd[0] = 6.0
        mob_mgr.update(dt, players, world)
        # Drainer les blocs cassés par la Gorgone (chunk cache + persistance)
        from mobs.base import MOB_GORGON as _MGRG
        for _gm in mob_mgr._mobs:
            if _gm.mob_type == _MGRG and getattr(_gm, "_break_pending", None):
                for _bc, _br in _gm._break_pending:
                    chunks.update_tile(_bc, _br, TILE_AIR)
                    _queue(_bc, _br, TILE_AIR)
                _gm._break_pending.clear()
        # Crachats verts de la Gorgone (physique + dégâts joueur + casse blocs)
        from mobs.deep import update_gorgon_spits
        update_gorgon_spits(dt, players, world, chunks, _queue)
        mob_mgr.tick_day_night(_is_nite, world, players)
        # Drops de mobs tués par le poison → joueur le plus proche
        if mob_mgr._poison_drops:
            from scenes.game.actions import _collect_drops
            closest = min(players, key=lambda p: abs(p.x))
            _collect_drops(closest, mob_mgr._poison_drops, loot_notifs)
            mob_mgr._poison_drops.clear()
        proj_mgr.update(dt, world, mob_mgr, loot_notifs, players, chunks, _queue)
        fam_mgr.update(dt, players, world, mob_mgr, loot_notifs)

        # ── Tick liquides (lave + eau) : itère seulement world.mods ──────
        _liquid_cd[0] -= dt
        if _liquid_cd[0] <= 0:
            _liquid_cd[0] = 1.0
            _LIQUIDS = (TILE_LAVA, TILE_WATER)
            _liq = sorted(
                ((c, r, t) for (c, r), t in world.mods.items() if t in _LIQUIDS),
                key=lambda x: -x[1],  # bottom-to-top pour cascade
            )
            for _col, _row, _lt in _liq:
                if world.get(_col, _row) != _lt:
                    continue  # déjà déplacé ce tick
                for _dc in (0, 1, -1) if (_col + _row) % 2 else (0, -1, 1):
                    _nc, _nr = _col + (0 if _dc == 0 else _dc), _row + 1
                    _below = world.get(_nc, _nr)
                    if _below == TILE_AIR:
                        world.set(_col, _row, TILE_AIR)
                        world.set(_nc, _nr, _lt)
                        chunks.update_tile(_col, _row, TILE_AIR)
                        chunks.update_tile(_nc, _nr, _lt)
                        _queue(_col, _row, TILE_AIR)
                        _queue(_nc, _nr, _lt)
                        # Activer les voisins procéduraux au-dessus
                        for _ac, _ar in ((_col, _row - 1), (_col - 1, _row), (_col + 1, _row)):
                            if (_ac, _ar) not in world.mods and world.get(_ac, _ar) in _LIQUIDS:
                                world.mods[(_ac, _ar)] = world.get(_ac, _ar)
                        break
                    # Eau + Lave → obsidienne
                    if {_lt, _below} == {TILE_WATER, TILE_LAVA}:
                        world.set(_col, _row, TILE_AIR)
                        world.set(_nc, _nr, TILE_OBSIDIAN)
                        chunks.update_tile(_col, _row, TILE_AIR)
                        chunks.update_tile(_nc, _nr, TILE_OBSIDIAN)
                        _queue(_col, _row, TILE_AIR)
                        _queue(_nc, _nr, TILE_OBSIDIAN)
                        break

        # ── Tick croissance des cultures ─────────────────────────────────
        _crop_cd[0] -= dt
        if _crop_cd[0] <= 0:
            _crop_cd[0] = CROP_TICK_INTERVAL
            for (_cc, _cr), _ct in list(world.mods.items()):
                _next = CROP_GROWTH.get(_ct)
                if _next is None:
                    continue
                # Vérifier eau à proximité (4 tiles autour de la terre labourée)
                _water_ok = False
                for _ddc in range(-4, 5):
                    for _ddr in range(-4, 5):
                        if world.get(_cc + _ddc, _cr + 1 + _ddr) == TILE_WATER:
                            _water_ok = True
                            break
                    if _water_ok:
                        break
                if _water_ok:
                    world.set(_cc, _cr, _next)
                    chunks.update_tile(_cc, _cr, _next)
                    _queue(_cc, _cr, _next)

        dx_d = abs(players[0].px() - players[1].px()); dy_d = abs(players[0].py() - players[1].py())
        pdist = max(dx_d, dy_d)
        _cross_zone = _boss_arena["in_arena"][0] != _boss_arena["in_arena"][1]
        if _cross_zone:
            # Un joueur dans l'arène, l'autre non → split forcé permanent
            if not is_split:
                is_split = True
                for k, cam in enumerate(split_cams):
                    cam.x = players[k].px() - HALF_W // 2
                    cam.y = max(0, min(players[k].py() - SCREEN_HEIGHT // 2, max_cy))
        elif not is_split and pdist >= SPLIT_DIST:
            is_split = True
            for k, cam in enumerate(split_cams):
                cam.x = players[k].px() - HALF_W // 2
                cam.y = max(0, min(players[k].py() - SCREEN_HEIGHT // 2, max_cy))
        elif is_split and pdist <= UNSPLIT_DIST and not any(cm.visible for cm in craft_menus) and not trade_menu.visible and not any(bs.get("open") for bs in _book_states):
            is_split = False
            shared_cam.x = (players[0].px() + players[1].px()) // 2 - SCREEN_WIDTH  // 2
            shared_cam.y = max(0, min((players[0].py() + players[1].py()) // 2 - SCREEN_HEIGHT // 2, max_cy))
        if is_split:
            for k, cam in enumerate(split_cams): cam.follow(players[k].px(), players[k].py(), dt)
        else:
            shared_cam.follow((players[0].px() + players[1].px()) // 2,
                              (players[0].py() + players[1].py()) // 2, dt)

        screen.fill(_sky_c)
        chunks.flush_ready()   # intègre les chunks calculés par le worker thread
        if is_split:
            for k, (surf, cam) in enumerate(zip(split_surfs, split_cams)):
                _draw_view(surf, cam, HALF_W, k, break_infos[k])
            pygame.draw.line(screen, (200, 200, 200), (HALF_W, 0), (HALF_W, SCREEN_HEIGHT), 2)
            split_surfs[1].blit(_seed_label, (HALF_W - _seed_label.get_width() - 4, SCREEN_HEIGHT - _seed_label.get_height() - 2))
        else:
            _draw_view(screen, shared_cam, SCREEN_WIDTH, 0, break_infos[0] or break_infos[1])
            _hy = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
            draw_hotbar(screen, players[1].inventory, SCREEN_WIDTH - HOTBAR_TOTAL - 4, P2_COLOR, font_sm)
            _p2_eff_hp = effective_max_hp(players[1])
            _hw = _p2_eff_hp // 2 * (_HEART_W + _HEART_GAP) - _HEART_GAP
            draw_hearts(screen, players[1].hp, _p2_eff_hp,
                        SCREEN_WIDTH - HOTBAR_TOTAL - 4 - 4 - _hw, _hy)
            if players[1]._dmg_flash > 0:
                _ds = _dmg_surf_full
                _ds.fill((200, 0, 0, min(140, int(140 * players[1]._dmg_flash / 0.4))))
                screen.blit(_ds, (0, 0))
            if craft_menus[1].visible:
                craft_menus[1].draw(screen, players[1].inventory, P2_COLOR, font_sm)
            screen.blit(_seed_label, (SCREEN_WIDTH - _seed_label.get_width() - 4, SCREEN_HEIGHT - _seed_label.get_height() - 2))

        if night_alpha(_day_time[0]) > 0: draw_night_overlay(screen, _day_time[0])
        draw_sky_hud(screen, _day_time[0], font_sm)
        if trade_menu.visible: trade_menu.draw(screen, players, font_sm)
        # ── Indicateur arène boss ────────────────────────────────────────
        if _boss_arena["active"]:
            _arena_lbl = font_med.render("~ REPAIRE DE LA GORGONE ~", True, (200, 80, 255))
            screen.blit(_arena_lbl, (SCREEN_WIDTH // 2 - _arena_lbl.get_width() // 2, 2))
        if quit_combo.update_and_draw(screen): _flush(); return True
        if _sounds.is_muted():
            screen.blit(_mute_label, (SCREEN_WIDTH // 2 - _mute_label.get_width() // 2,
                               SCREEN_HEIGHT - _mute_label.get_height() - 2))

        ni = 0
        while ni < len(loot_notifs):
            loot_notifs[ni][1] -= dt
            if loot_notifs[ni][1] <= 0: loot_notifs.pop(ni)
            else: ni += 1
        if loot_notifs:
            _ntxt, _ntime, _ = loot_notifs[-1]
            _na  = 255 if _ntime > 0.6 else int(_ntime / 0.6 * 255)
            _lbl = font_med.render(_ntxt, True, (255, 220, 60)); _lbl.set_alpha(_na)
            _lw, _lh = _lbl.get_size(); _p = 6
            _nbg_w = _lw + _p * 2
            if _notif_bg_surf[0] is None or _notif_prev_w[0] != _nbg_w:
                _notif_bg_surf[0] = pygame.Surface((_nbg_w, _lh + _p * 2), pygame.SRCALPHA)
                _notif_prev_w[0] = _nbg_w
            _notif_bg_surf[0].fill((0, 0, 0, int(_na * 0.7)))
            _nx = SCREEN_WIDTH // 2 - _nbg_w // 2; _ny = SCREEN_HEIGHT // 3
            screen.blit(_notif_bg_surf[0], (_nx, _ny)); screen.blit(_lbl, (_nx + _p, _ny + _p))

        pygame.display.flip()
