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

from scenes.game.player      import Player, move_x, move_y, touching_wall, in_reach, eject_from_blocks
from scenes.game.camera      import Camera, ChunkCache
from scenes.game.controls    import joy_btn, get_dir_p1, get_dir_p2, get_cursor
from scenes.game.sky         import sky_color, night_alpha, is_night, draw_night_overlay, draw_sky_hud, DAY_CYCLE_DURATION
from scenes.game.renderer_world  import draw_world, draw_cursor, draw_flag_in_world
from scenes.game.renderer_player import draw_player, draw_hearts, draw_compass, _HEART_W, _HEART_GAP
from scenes.game.renderer_hud    import draw_hotbar, HOTBAR_TOTAL, HOTBAR_SLOT_H as _HOTBAR_SLOT_H
from scenes.game.actions     import handle_sword, handle_flag, handle_block_actions
from scenes.game.craft       import CraftMenu


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

    def _queue(col, row, tile): _pending[(col, row)] = tile

    def _flush():
        if _pending:
            _db.save_blocks_batch(world_id, [(c, r, t) for (c, r), t in _pending.items()])
            _pending.clear()
        for p in players:
            _db.save_player(world_id, p.idx, p.x, p.y, p.inventory, flag=flag_positions[p.idx])

    mid = 1_000_000; spawn_cols = [mid - 3, mid + 3]
    def _sx(col): return col - PLAYER_W / TILE_SIZE / 2
    def _sy(col): return world.surface_at(col) - PLAYER_H / TILE_SIZE - 1
    players = [Player(_sx(c), _sy(c), clr, idx)
               for idx, (c, clr) in enumerate(zip(spawn_cols, [P1_COLOR, P2_COLOR]))]
    for p in players: eject_from_blocks(p, world)
    flag_positions = [None, None]

    for p in players:
        sv = saves.get(p.idx)
        if not sv: continue
        p.x, p.y = sv["x"], sv["y"]
        p.inventory.tool      = sv["tool"]
        p.inventory.resources = [tuple(r) for r in sv["resources"]]
        p.inventory.swords      = sv.get("swords", []);    p.inventory.sword_idx   = sv.get("sword_idx", 0)
        p.inventory.pickaxes    = sv.get("pickaxes", []);  p.inventory.pickaxe_idx = sv.get("pickaxe_idx", 0)
        p.inventory.equip = {k: [tuple(e) for e in v] for k, v in sv["equip"].items()}
        for sl, lst in p.inventory.equip.items():
            p.inventory.equip_idx[sl] = min(p.inventory.equip_idx.get(sl, 0), max(0, len(lst) - 1))
        eject_from_blocks(p, world)
        if sv.get("flag") is not None: flag_positions[p.idx] = sv["flag"]

    HALF_W = SCREEN_WIDTH // 2; max_cy = ROWS * TILE_SIZE - SCREEN_HEIGHT
    shared_cam  = Camera()
    split_cams  = [Camera(view_w=HALF_W), Camera(view_w=HALF_W)]
    split_surfs = [screen.subsurface(pygame.Rect(0, 0, HALF_W, SCREEN_HEIGHT)),
                   screen.subsurface(pygame.Rect(HALF_W, 0, HALF_W, SCREEN_HEIGHT))]
    SPLIT_DIST = int(SCREEN_HEIGHT * 0.55); UNSPLIT_DIST = int(SCREEN_HEIGHT * 0.40); is_split = False
    shared_cam.x = max(0, (players[0].px() + players[1].px()) // 2 - SCREEN_WIDTH  // 2)
    shared_cam.y = max(0, min((players[0].py() + players[1].py()) // 2 - SCREEN_HEIGHT // 2, max_cy))
    for sc in split_cams: sc.x, sc.y = shared_cam.x, shared_cam.y
    chunks.preload_around(shared_cam.x, SCREEN_WIDTH)

    mob_mgr = _mobs.MobManager(world); _mob_cd = [0.0]
    joy1 = joysticks[0] if joysticks else None
    p_ctrl = [
        (joy1, J1_BTN_MINE, -1,            J1_BTN_MODIFIER, get_dir_p1, KB_J1_MINE, KB_J1_MODIFIER),
        (joy1, J2_BTN_MINE, J2_BTN_MINE2,  J2_BTN_MODIFIER, get_dir_p2, KB_J2_MINE, KB_J2_MODIFIER),
    ]
    p_dirs=[( 0,0),(0,0)]; break_infos=[None,None]; prev_mine=[False,False]
    prev_dx=[0,0]; prev_dy=[0,0]; mine_tick_cd=[0.0,0.0]
    loot_notifs=[]; craft_menus=[CraftMenu(),CraftMenu()]

    def _draw_view(surf, cam, view_w, k, bi):
        surf.fill(_sky_c)
        chunks.preload_around(cam.x, view_w)
        draw_world(surf, chunks, cam, bi)
        for j, pl in enumerate(players):
            if pl.inventory.tool != TOOL_SWORD:
                c2, r2 = get_cursor(pl, *p_dirs[j], world)
                r2 = max(0, min(ROWS - 1, r2))
                if in_reach(pl, c2, r2): draw_cursor(surf, pl, c2, r2, cam)
        for fi, fp in enumerate(flag_positions):
            if fp: draw_flag_in_world(surf, fp[0], fp[1], players[fi].color, cam)
        mob_mgr.draw(surf, cam)
        for pl in players: draw_player(surf, pl, cam, font_sm)
        pi = players[k]
        if pi._dmg_flash > 0:
            _ds = pygame.Surface((view_w, SCREEN_HEIGHT), pygame.SRCALPHA)
            _ds.fill((200, 0, 0, min(140, int(140 * pi._dmg_flash / 0.4)))); surf.blit(_ds, (0, 0))
        _hy = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
        draw_hotbar(surf, pi.inventory, 4, pi.color, font_sm)
        draw_hearts(surf, pi.hp, pi.max_hp, 4 + HOTBAR_TOTAL + 4, _hy)
        if view_w < SCREEN_WIDTH: draw_compass(surf, cam, pi, players[1 - k], view_w, players[1 - k].color)
        if craft_menus[k].visible: craft_menus[k].draw(surf, pi.inventory, pi.color, font_sm)

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
        for e in events:
            if e.type == pygame.QUIT: _flush(); return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: _flush(); return True
                if e.key == pygame.K_p: _sounds.toggle_mute(); _music.toggle_mute()
            quit_combo.handle_event(e)

        for i, player in enumerate(players):
            joy, btn_mine, btn_mine2, btn_mod, get_dir, kb_mine, kb_mod = p_ctrl[i]
            dx, dy   = get_dir(keys, joy)
            cur_mine = joy_btn(joy, btn_mine) or joy_btn(joy, btn_mine2) or bool(keys[kb_mine])
            cur_mod  = joy_btn(joy, btn_mod)  or bool(keys[kb_mod])

            # ── Ouverture menu craft (outil actif = Table de Craft + action) ────────
            just_opened = False
            if player.inventory.tool == TOOL_CRAFT and cur_mine and not prev_mine[i]:
                if not craft_menus[i].visible:
                    craft_menus[i].toggle(); just_opened = True

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
                prev_mine[i] = cur_mine; continue

            if cur_mod:
                if dx ==  1 and prev_dx[i] !=  1: player.inventory.slot_next();  _sounds.inv_change()
                elif dx == -1 and prev_dx[i] != -1: player.inventory.slot_prev(); _sounds.inv_change()
                if dy == -1 and prev_dy[i] != -1: player.inventory.item_prev();  _sounds.inv_change()
                elif dy == 1 and prev_dy[i] != 1: player.inventory.item_next();  _sounds.inv_change()
                player.vx = 0.0
            else:
                player.vx = dx * WALK_SPEED
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
            handle_sword(player, mob_mgr, loot_notifs, cur_mine, prev_mine[i], cur_mod)
            handle_flag(player, flag_positions, loot_notifs, cur_mine, prev_mine[i], cur_mod)
            if in_reach(player, cur_col, cur_row) and player.inventory.tool != TOOL_SWORD:
                handle_block_actions(player, i, world, chunks, mob_mgr, players,
                    break_infos, mine_tick_cd, loot_notifs,
                    cur_col, cur_row, cur_mine, prev_mine[i], cur_mod, dt, _queue)
            elif not cur_mine: break_infos[i] = None; player._break_time = 0.0
            prev_mine[i] = cur_mine

        for player in players:
            player._dmg_flash = max(0.0, player._dmg_flash - dt)
        for i, player in enumerate(players):
            if player.hp <= 0 or player.y * TILE_SIZE > ROWS * TILE_SIZE + 64:
                player.hp = player.max_hp
                fp = flag_positions[i]
                if fp: player.x, player.y = fp
                else:  player.x = _sx(spawn_cols[i]); player.y = _sy(spawn_cols[i])
                player.vx = player.vy = 0.0; eject_from_blocks(player, world)

        _mob_cd[0] -= dt
        if _mob_cd[0] <= 0:
            mob_mgr.spawn_around(list({int(p.x) for p in players}), _is_nite); _mob_cd[0] = 3.0
        mob_mgr.update(dt, players, world)

        dx_d = abs(players[0].px() - players[1].px()); dy_d = abs(players[0].py() - players[1].py())
        pdist = max(dx_d, dy_d)
        if not is_split and pdist >= SPLIT_DIST:
            is_split = True
            for k, cam in enumerate(split_cams):
                cam.x = max(0, players[k].px() - HALF_W // 2)
                cam.y = max(0, min(players[k].py() - SCREEN_HEIGHT // 2, max_cy))
        elif is_split and pdist <= UNSPLIT_DIST:
            is_split = False
            shared_cam.x = max(0, (players[0].px() + players[1].px()) // 2 - SCREEN_WIDTH  // 2)
            shared_cam.y = max(0, min((players[0].py() + players[1].py()) // 2 - SCREEN_HEIGHT // 2, max_cy))
        if is_split:
            for k, cam in enumerate(split_cams): cam.follow(players[k].px(), players[k].py(), dt)
        else:
            shared_cam.follow((players[0].px() + players[1].px()) // 2,
                              (players[0].py() + players[1].py()) // 2, dt)

        screen.fill(_sky_c)
        if is_split:
            for k, (surf, cam) in enumerate(zip(split_surfs, split_cams)):
                _draw_view(surf, cam, HALF_W, k, break_infos[k])
            pygame.draw.line(screen, (200, 200, 200), (HALF_W, 0), (HALF_W, SCREEN_HEIGHT), 2)
            _sl = font_sm.render("seed:" + str(world_seed), True, (180, 180, 180))
            split_surfs[1].blit(_sl, (HALF_W - _sl.get_width() - 4, SCREEN_HEIGHT - _sl.get_height() - 2))
        else:
            _draw_view(screen, shared_cam, SCREEN_WIDTH, 0, break_infos[0] or break_infos[1])
            _hy = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
            draw_hotbar(screen, players[1].inventory, SCREEN_WIDTH - HOTBAR_TOTAL - 4, P2_COLOR, font_sm)
            _hw = players[1].max_hp // 2 * (_HEART_W + _HEART_GAP) - _HEART_GAP
            draw_hearts(screen, players[1].hp, players[1].max_hp,
                        SCREEN_WIDTH - HOTBAR_TOTAL - 4 - 4 - _hw, _hy)
            if players[1]._dmg_flash > 0:
                _ds = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                _ds.fill((200, 0, 0, min(140, int(140 * players[1]._dmg_flash / 0.4))))
                screen.blit(_ds, (0, 0))
            if craft_menus[1].visible:
                craft_menus[1].draw(screen, players[1].inventory, P2_COLOR, font_sm)
            _sl = font_sm.render("seed: " + str(world_seed), True, (180, 180, 180))
            screen.blit(_sl, (SCREEN_WIDTH - _sl.get_width() - 4, SCREEN_HEIGHT - _sl.get_height() - 2))

        if night_alpha(_day_time[0]) > 0: draw_night_overlay(screen, _day_time[0])
        draw_sky_hud(screen, _day_time[0], font_sm)
        if quit_combo.update_and_draw(screen): _flush(); return True
        if _sounds.is_muted():
            _ml = font_sm.render("[MUTE] P", True, (255, 80, 80))
            screen.blit(_ml, (SCREEN_WIDTH // 2 - _ml.get_width() // 2,
                               SCREEN_HEIGHT - _ml.get_height() - 2))

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
            _nbg = pygame.Surface((_lw + _p * 2, _lh + _p * 2), pygame.SRCALPHA)
            _nbg.fill((0, 0, 0, int(_na * 0.7)))
            _nx = SCREEN_WIDTH // 2 - (_lw + _p * 2) // 2; _ny = SCREEN_HEIGHT // 3
            screen.blit(_nbg, (_nx, _ny)); screen.blit(_lbl, (_nx + _p, _ny + _p))

        pygame.display.flip()
