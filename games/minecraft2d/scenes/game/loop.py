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

from scenes.game.player     import Player, solid, move_x, move_y, touching_wall, in_reach, eject_from_blocks, player_cols
from scenes.game.camera     import Camera, ChunkCache, _CHUNK_H
from scenes.game.controls   import joy_btn, get_dir_p1, get_dir_p2, get_cursor
from scenes.game.sky        import sky_color, night_alpha, is_night, draw_night_overlay, draw_sky_hud, DAY_CYCLE_DURATION
from scenes.game.renderer_world  import draw_world, draw_cursor, draw_flag_in_world
from scenes.game.renderer_player import draw_player, draw_hearts, draw_compass, _HEART_W, _HEART_GAP
from scenes.game.renderer_hud    import draw_hotbar, HOTBAR_TOTAL, HOTBAR_SLOT_H as _HOTBAR_SLOT_H


def run(screen, joysticks, world_id, seed):
    """
    Lance la partie.
    world_id : int 1-4 (slot SQLite)
    seed     : int     (seed de génération)
    Retourne True (retour menu) ou None (quitter).
    """
    clock      = pygame.time.Clock()
    quit_combo = QuitCombo()
    font_sm    = pygame.font.SysFont("Arial", 9)
    font_med   = pygame.font.SysFont("Arial", 11, bold=True)

    world      = generate(seed)
    world_seed = world.seed
    world.mods.update(_db.load_blocks(world_id))
    _saved_players = _db.load_players(world_id)

    chunks    = ChunkCache(world)
    _day_time = [0.12]   # démarre en plein jour

    # ── Batch SQLite ──────────────────────────────────────────────────────────
    _pending_saves = {}
    _last_flush    = [0.0]
    _FLUSH_INTERVAL = 2.0

    def _queue_block(col, row, tile):
        _pending_saves[(col, row)] = tile

    def _flush_all():
        if _pending_saves:
            _db.save_blocks_batch(world_id,
                [(c, r, t) for (c, r), t in _pending_saves.items()])
            _pending_saves.clear()
        for p in players:
            _db.save_player(world_id, p.idx, p.x, p.y, p.inventory,
                            flag=flag_positions[p.idx])

    # ── Spawn initial ─────────────────────────────────────────────────────────
    def _spawn_x(col): return col - PLAYER_W / TILE_SIZE / 2
    def _spawn_y(col): return world.surface_at(col) - PLAYER_H / TILE_SIZE - 1

    mid    = 1_000_000
    p1_col = mid - 3
    p2_col = mid + 3
    players = [
        Player(_spawn_x(p1_col), _spawn_y(p1_col), P1_COLOR, 0),
        Player(_spawn_x(p2_col), _spawn_y(p2_col), P2_COLOR, 1),
    ]
    for p in players:
        eject_from_blocks(p, world)

    flag_positions = [None, None]

    # ── Restaurer sauvegarde ──────────────────────────────────────────────────
    for p in players:
        sv = _saved_players.get(p.idx)
        if sv:
            p.x = sv["x"]
            p.y = sv["y"]
            p.inventory.tool         = sv["tool"]
            p.inventory.resources    = [tuple(r) for r in sv["resources"]]
            p.inventory.swords       = sv.get("swords", [])
            p.inventory.sword_idx    = sv.get("sword_idx", 0)
            p.inventory.pickaxes     = sv.get("pickaxes", [])
            p.inventory.pickaxe_idx  = sv.get("pickaxe_idx", 0)
            p.inventory.equip        = {
                k: [tuple(e) for e in v]
                for k, v in sv["equip"].items()
            }
            for eslot, lst in p.inventory.equip.items():
                p.inventory.equip_idx[eslot] = min(
                    p.inventory.equip_idx.get(eslot, 0),
                    max(0, len(lst) - 1)
                )
            eject_from_blocks(p, world)
            if sv.get("flag") is not None:
                flag_positions[p.idx] = sv["flag"]

    # ── Caméras ───────────────────────────────────────────────────────────────
    HALF_W     = SCREEN_WIDTH // 2
    shared_cam = Camera()
    split_cams = [Camera(view_w=HALF_W), Camera(view_w=HALF_W)]
    split_surfs = [
        screen.subsurface(pygame.Rect(0,      0, HALF_W, SCREEN_HEIGHT)),
        screen.subsurface(pygame.Rect(HALF_W, 0, HALF_W, SCREEN_HEIGHT)),
    ]
    SPLIT_DIST   = int(SCREEN_HEIGHT * 0.55)
    UNSPLIT_DIST = int(SCREEN_HEIGHT * 0.40)
    is_split     = False

    spawn_mid_px = (players[0].px() + players[1].px()) // 2
    spawn_mid_py = (players[0].py() + players[1].py()) // 2
    max_cy = ROWS * TILE_SIZE - SCREEN_HEIGHT
    shared_cam.x = max(0, spawn_mid_px - SCREEN_WIDTH  // 2)
    shared_cam.y = max(0, min(spawn_mid_py - SCREEN_HEIGHT // 2, max_cy))
    for sc in split_cams:
        sc.x, sc.y = shared_cam.x, shared_cam.y

    chunks.preload_around(shared_cam.x, SCREEN_WIDTH)

    # ── Mobs ──────────────────────────────────────────────────────────────────
    mob_mgr      = _mobs.MobManager(world)
    _mob_spawn_cd = [0.0]

    # ── Joysticks / contrôles ─────────────────────────────────────────────────
    joy1 = joysticks[0] if len(joysticks) > 0 else None
    joy2 = joy1   # une seule manette partagée

    player_controls = [
        (joy1, J1_BTN_MINE, -1,           J1_BTN_MODIFIER, get_dir_p1, KB_J1_MINE, KB_J1_MODIFIER),
        (joy2, J2_BTN_MINE, J2_BTN_MINE2, J2_BTN_MODIFIER, get_dir_p2, KB_J2_MINE, KB_J2_MODIFIER),
    ]

    p_dirs       = [(0, 0), (0, 0)]
    break_infos  = [None, None]
    prev_mine    = [False, False]
    prev_dx      = [0, 0]
    prev_dy      = [0, 0]
    mine_tick_cd = [0.0, 0.0]
    loot_notifs  = []   # [[texte, temps_restant, couleur], ...]

    # ─────────────────────────────────────────────────────────────────────────
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        # Cycle jour/nuit
        _day_time[0] = (_day_time[0] + dt / DAY_CYCLE_DURATION) % 1.0
        _sky_c   = sky_color(_day_time[0])
        _is_nite = is_night(_day_time[0])

        _last_flush[0] += dt
        if _last_flush[0] >= _FLUSH_INTERVAL:
            _flush_all()
            _last_flush[0] = 0.0
        mine_tick_cd[0] = max(0.0, mine_tick_cd[0] - dt)
        mine_tick_cd[1] = max(0.0, mine_tick_cd[1] - dt)

        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.QUIT:
                _flush_all()
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                _flush_all()
                return True
            if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                _sounds.toggle_mute()
                _music.toggle_mute()
            quit_combo.handle_event(e)

        # ── Physique + contrôles par joueur ───────────────────────────────────
        for i, player in enumerate(players):
            joy, btn_mine, btn_mine2, btn_mod, get_dir, kb_mine, kb_mod = player_controls[i]

            dx, dy   = get_dir(keys, joy)
            cur_mine = joy_btn(joy, btn_mine) or joy_btn(joy, btn_mine2) or bool(keys[kb_mine])
            cur_mod  = joy_btn(joy, btn_mod)  or bool(keys[kb_mod])

            # Mode MODIFIER : navigation inventaire
            if cur_mod:
                if dx ==  1 and prev_dx[i] !=  1:
                    player.inventory.slot_next()
                    _sounds.inv_change()
                elif dx == -1 and prev_dx[i] != -1:
                    player.inventory.slot_prev()
                    _sounds.inv_change()
                if dy == -1 and prev_dy[i] != -1:
                    player.inventory.item_prev()
                    _sounds.inv_change()
                elif dy ==  1 and prev_dy[i] !=  1:
                    player.inventory.item_next()
                    _sounds.inv_change()
                player.vx = 0.0
            else:
                player.vx = dx * WALK_SPEED

            if dx != 0 or dy != 0:
                p_dirs[i] = (dx, dy)
            prev_dx[i] = dx
            prev_dy[i] = dy

            # Escalade de mur
            player.on_wall = touching_wall(player, world)
            climbing = dy < 0 and player.on_wall and not player.on_ground and not cur_mod

            if climbing:
                player.vy = -CLIMB_SPEED
            else:
                if dy < 0 and player.on_ground and not cur_mod:
                    player.vy = JUMP_VEL
                    _sounds.jump()
                player.vy = min(player.vy + GRAVITY * dt, MAX_FALL_SPEED)

            player.on_ground = False
            move_x(player, world, player.vx * dt)
            move_y(player, world, player.vy * dt)

            if player._action_cd > 0:
                player._action_cd -= dt

            cdx, cdy = p_dirs[i]
            cur_col, cur_row = get_cursor(player, cdx, cdy, world)
            cur_row = max(0, min(ROWS - 1, cur_row))
            _in_reach = in_reach(player, cur_col, cur_row)

            # Épée : attaque
            if player.inventory.tool == TOOL_SWORD and player._action_cd <= 0:
                if cur_mine and not prev_mine[i] and not cur_mod:
                    dmg    = (player.inventory.sword_mat or 0) + 1
                    killed = mob_mgr.attack_near(player.x, player.y, REACH_RADIUS, dmg)
                    if killed > 0:
                        player.hp = player.max_hp
                    player._action_cd = 0.35
                    _sounds.sword_hit()

            # Drapeau : poser le point de respawn
            if player.inventory.tool == TOOL_FLAG and player._action_cd <= 0:
                if cur_mine and not prev_mine[i] and not cur_mod:
                    flag_positions[i] = (player.x, player.y)
                    player._action_cd = 0.4
                    loot_notifs.append(["Drapeau J" + str(i + 1) + " placé !", 2.0, player.color])
                    _sounds.flag_place()

            if _in_reach and player._action_cd <= 0 and player.inventory.tool != TOOL_SWORD:
                tile_at = world.get(cur_col, cur_row)

                if cur_mine and not prev_mine[i] and not cur_mod:
                    # Poser un bloc (Canon)
                    if player.inventory.tool == TOOL_PLACER and tile_at == TILE_AIR:
                        selected = player.inventory.selected_tile()
                        if selected != TILE_AIR:
                            occupied = any(
                                int(p.x + PLAYER_W / TILE_SIZE / 2) == cur_col and
                                int(p.y + PLAYER_H / TILE_SIZE / 2) == cur_row
                                for p in players
                            )
                            if not occupied:
                                world.set(cur_col, cur_row, selected)
                                chunks.update_tile(cur_col, cur_row, selected)
                                for p in players:
                                    eject_from_blocks(p, world)
                                player.inventory.consume()
                                player._action_cd = 0.2
                                _queue_block(cur_col, cur_row, selected)
                                _sounds.place()

                elif cur_mine and not cur_mod:
                    # Minage continu
                    if tile_at == TILE_CHEST and player.inventory.tool == TOOL_HAND:
                        if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                            player._break_time += dt
                            progress = min(player._break_time / 0.6, 1.0)
                            break_infos[i] = (cur_col, cur_row, progress)
                            if player._break_time >= 0.6:
                                item = world.chest_loot()
                                player.inventory.add_equip(item)
                                loot_notifs.append([EQUIP_NAMES.get(item, "?"), 2.5, player.color])
                                world.set(cur_col, cur_row, TILE_AIR)
                                chunks.update_tile(cur_col, cur_row, TILE_AIR)
                                break_infos[i] = None
                                player._break_time = 0.0
                                player._action_cd  = 0.3
                                _queue_block(cur_col, cur_row, TILE_AIR)
                                _sounds.chest_open()
                        else:
                            player._break_time = 0.0
                            break_infos[i] = (cur_col, cur_row, 0.0)

                    elif (tile_at != TILE_AIR and tile_at != TILE_CHEST
                            and player.inventory.tool == TOOL_PICKAXE):
                        if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                            player._break_time += dt
                            req_time = TILE_BREAK_TIME.get(tile_at, 0.5)
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
                                break_infos[i] = None
                                player._break_time = 0.0
                                player._action_cd  = 0.1
                                _queue_block(cur_col, cur_row, TILE_AIR)
                                _sounds.mine_done()
                                mine_tick_cd[i] = 0.0
                        else:
                            player._break_time = 0.0
                            break_infos[i] = (cur_col, cur_row, 0.0)
                    else:
                        break_infos[i]    = None
                        player._break_time = 0.0
                else:
                    break_infos[i]    = None
                    player._break_time = 0.0
            else:
                if not cur_mine:
                    break_infos[i]    = None
                    player._break_time = 0.0

            prev_mine[i] = cur_mine

        # Flash de dégâts
        for player in players:
            player._dmg_flash = max(0.0, player._dmg_flash - dt)

        # Respawn
        for i, player in enumerate(players):
            dead = player.hp <= 0 or player.y * TILE_SIZE > ROWS * TILE_SIZE + 64
            if dead:
                player.hp = player.max_hp
                fp = flag_positions[i]
                if fp:
                    player.x, player.y = fp
                else:
                    col = p1_col if i == 0 else p2_col
                    player.x = _spawn_x(col)
                    player.y = _spawn_y(col)
                player.vx = 0.0
                player.vy = 0.0
                eject_from_blocks(player, world)

        # Mobs
        _mob_spawn_cd[0] -= dt
        if _mob_spawn_cd[0] <= 0:
            centers = list({int(p.x) for p in players})
            mob_mgr.spawn_around(centers, _is_nite)
            _mob_spawn_cd[0] = 3.0
        mob_mgr.update(dt, players, world)

        # Caméras
        dx_dist     = abs(players[0].px() - players[1].px())
        dy_dist     = abs(players[0].py() - players[1].py())
        player_dist = max(dx_dist, dy_dist)

        if not is_split and player_dist >= SPLIT_DIST:
            is_split = True
            for i, cam in enumerate(split_cams):
                cam.x = max(0, players[i].px() - HALF_W       // 2)
                cam.y = max(0, min(players[i].py() - SCREEN_HEIGHT // 2,
                                   ROWS * TILE_SIZE - SCREEN_HEIGHT))
        elif is_split and player_dist <= UNSPLIT_DIST:
            is_split = False
            mx = (players[0].px() + players[1].px()) // 2
            my = (players[0].py() + players[1].py()) // 2
            shared_cam.x = max(0, mx - SCREEN_WIDTH  // 2)
            shared_cam.y = max(0, min(my - SCREEN_HEIGHT // 2,
                                      ROWS * TILE_SIZE - SCREEN_HEIGHT))

        if is_split:
            for i, cam in enumerate(split_cams):
                cam.follow(players[i].px(), players[i].py(), dt)
        else:
            mid_px = (players[0].px() + players[1].px()) // 2
            mid_py = (players[0].py() + players[1].py()) // 2
            shared_cam.follow(mid_px, mid_py, dt)

        # ── Rendu ─────────────────────────────────────────────────────────────
        screen.fill(_sky_c)

        if is_split:
            for i, (surf, cam) in enumerate(zip(split_surfs, split_cams)):
                surf.fill(_sky_c)
                chunks.preload_around(cam.x, HALF_W)
                draw_world(surf, chunks, cam, break_infos[i])

                for j, player in enumerate(players):
                    if player.inventory.tool == TOOL_SWORD:
                        continue
                    cdx, cdy = p_dirs[j]
                    c_col, c_row = get_cursor(player, cdx, cdy, world)
                    c_row = max(0, min(ROWS - 1, c_row))
                    if in_reach(player, c_col, c_row):
                        draw_cursor(surf, player, c_col, c_row, cam)

                for fi, fp in enumerate(flag_positions):
                    if fp:
                        draw_flag_in_world(surf, fp[0], fp[1], players[fi].color, cam)

                mob_mgr.draw(surf, cam)
                for player in players:
                    draw_player(surf, player, cam, font_sm)

                # Flash dégâts
                pi = players[i]
                if pi._dmg_flash > 0:
                    _alpha = int(140 * pi._dmg_flash / 0.4)
                    _ds = pygame.Surface((HALF_W, SCREEN_HEIGHT), pygame.SRCALPHA)
                    _ds.fill((200, 0, 0, min(140, _alpha)))
                    surf.blit(_ds, (0, 0))

                draw_hotbar(surf, pi.inventory, 4, pi.color, font_sm)
                _hearts_y = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
                draw_hearts(surf, pi.hp, pi.max_hp,
                            4 + HOTBAR_TOTAL + 4, _hearts_y)
                draw_compass(surf, cam, pi, players[1 - i], HALF_W, players[1 - i].color)

            pygame.draw.line(screen, (200, 200, 200),
                             (HALF_W, 0), (HALF_W, SCREEN_HEIGHT), 2)
            seed_lbl = font_sm.render("seed:" + str(world_seed), True, (180, 180, 180))
            split_surfs[1].blit(seed_lbl, (HALF_W - seed_lbl.get_width() - 4,
                                           SCREEN_HEIGHT - seed_lbl.get_height() - 2))

        else:
            chunks.preload_around(shared_cam.x, SCREEN_WIDTH)
            draw_world(screen, chunks, shared_cam, break_infos[0] or break_infos[1])

            for i, player in enumerate(players):
                if player.inventory.tool == TOOL_SWORD:
                    continue
                cdx, cdy = p_dirs[i]
                c_col, c_row = get_cursor(player, cdx, cdy, world)
                c_row = max(0, min(ROWS - 1, c_row))
                if in_reach(player, c_col, c_row):
                    draw_cursor(screen, player, c_col, c_row, shared_cam)

            mob_mgr.draw(screen, shared_cam)
            for fi, fp in enumerate(flag_positions):
                if fp:
                    draw_flag_in_world(screen, fp[0], fp[1], players[fi].color, shared_cam)
            for i, player in enumerate(players):
                draw_player(screen, player, shared_cam, font_sm)

            draw_hotbar(screen, players[0].inventory, 4, P1_COLOR, font_sm)
            draw_hotbar(screen, players[1].inventory,
                        SCREEN_WIDTH - HOTBAR_TOTAL - 4, P2_COLOR, font_sm)

            _hearts_y = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
            _hearts_w = players[0].max_hp // 2 * (_HEART_W + _HEART_GAP) - _HEART_GAP
            draw_hearts(screen, players[0].hp, players[0].max_hp,
                        4 + HOTBAR_TOTAL + 4, _hearts_y)
            draw_hearts(screen, players[1].hp, players[1].max_hp,
                        SCREEN_WIDTH - HOTBAR_TOTAL - 4 - 4 - _hearts_w, _hearts_y)

            for _pp in players:
                if _pp._dmg_flash > 0:
                    _alpha = int(140 * _pp._dmg_flash / 0.4)
                    _ds = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    _ds.fill((200, 0, 0, min(140, _alpha)))
                    screen.blit(_ds, (0, 0))

            seed_lbl = font_sm.render("seed: " + str(world_seed), True, (180, 180, 180))
            screen.blit(seed_lbl, (SCREEN_WIDTH - seed_lbl.get_width() - 4,
                                   SCREEN_HEIGHT - seed_lbl.get_height() - 2))

        # Overlay nuit
        _na = night_alpha(_day_time[0])
        if _na > 0:
            draw_night_overlay(screen, _day_time[0])
        draw_sky_hud(screen, _day_time[0], font_sm)

        # SELECT+START combo
        if quit_combo.update_and_draw(screen):
            _flush_all()
            return True

        # Indicateur mute
        if _sounds.is_muted():
            mute_lbl = font_sm.render("[MUTE] P", True, (255, 80, 80))
            screen.blit(mute_lbl, (SCREEN_WIDTH // 2 - mute_lbl.get_width() // 2,
                                   SCREEN_HEIGHT - mute_lbl.get_height() - 2))

        # Notifications loot
        ni = 0
        while ni < len(loot_notifs):
            loot_notifs[ni][1] -= dt
            if loot_notifs[ni][1] <= 0:
                loot_notifs.pop(ni)
            else:
                ni += 1
        if loot_notifs:
            _ntxt, _ntime, _ncol = loot_notifs[-1]
            _nalpha = 255 if _ntime > 0.6 else int(_ntime / 0.6 * 255)
            _nlbl   = font_med.render("Obtenu : " + _ntxt + " !", True, (255, 220, 60))
            _nlbl.set_alpha(_nalpha)
            _nlw, _nlh = _nlbl.get_size()
            _npad = 6
            _nbg  = pygame.Surface((_nlw + _npad * 2, _nlh + _npad * 2), pygame.SRCALPHA)
            _nbg.fill((0, 0, 0, int(_nalpha * 0.7)))
            _nnx = SCREEN_WIDTH  // 2 - (_nlw + _npad * 2) // 2
            _nny = SCREEN_HEIGHT // 3
            screen.blit(_nbg,  (_nnx, _nny))
            screen.blit(_nlbl, (_nnx + _npad, _nny + _npad))

        pygame.display.flip()
