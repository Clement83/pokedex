"""
Écran de sélection de monde – style Minecraft.
4 slots ; navigation avec les directions, action pour jouer/créer,
modifier+action pour écraser/supprimer un slot.

Retourne : (slot_id, seed) ou None si quitter.
"""
import pygame
import sys
import os
import random
import math

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    P1_COLOR, P2_COLOR, TEXT_COLOR,
    J1_BTN_MINE, J1_BTN_MODIFIER, KB_J1_MINE, KB_J1_MODIFIER,
    KB_J1_UP, KB_J1_DOWN, KB_J1_LEFT, KB_J1_RIGHT,
    AXIS_DEAD, BTN_A, BTN_B, BTN_X, BTN_Y,
)
import db
from quit_combo import QuitCombo

# ── Palettes ─────────────────────────────────────────────────────────────────
_MC_SKY    = ( 58, 109, 171)
_MC_YELLOW = (255, 215,   0)
_MC_SHADOW = ( 60,  40,  20)
_MC_DARK   = ( 30,  30,  30)
_MC_GREEN  = ( 90, 180,  30)
_MC_BROWN  = (101,  67,  33)
_MC_GRAY   = (100, 100, 100)
_SLOT_BG   = ( 50,  50,  50)
_SLOT_SEL  = ( 90,  80,  20)
_SLOT_HOV  = ( 70,  60,  15)
_RED       = (200,  50,  50)

MAX_SLOTS  = 4
SLOT_W     = 200
SLOT_H     = 60
SLOT_GAP   = 10


def _joy_btn(joy, btn):
    try:
        return bool(joy and joy.get_button(btn))
    except Exception:
        return False


def _get_dir(keys, joy):
    if joy:
        try:
            ay = joy.get_axis(1)
            if ay < -AXIS_DEAD: return 0, -1
            if ay >  AXIS_DEAD: return 0,  1
        except Exception:
            pass
        try:
            hx, hy = joy.get_hat(0)
            if hy != 0: return 0, -hy
        except Exception:
            pass
    if keys[KB_J1_UP]:   return 0, -1
    if keys[KB_J1_DOWN]: return 0,  1
    return 0, 0


def _draw_slot(screen, font_big, font_sm, rect, world, selected, confirm_del):
    x, y, w, h = rect
    # Fond
    if confirm_del:
        bg = _RED
    elif selected:
        bg = _SLOT_SEL
    else:
        bg = _SLOT_BG

    pygame.draw.rect(screen, bg,        (x, y, w, h))
    pygame.draw.rect(screen, _MC_YELLOW if selected else _MC_GRAY, (x, y, w, h), 2)

    if world is None:
        # Slot vide
        icon_color = (_MC_GREEN if selected else (60, 90, 60))
        pygame.draw.line(screen, icon_color, (x + 16, y + h // 2), (x + 28, y + h // 2), 3)
        pygame.draw.line(screen, icon_color, (x + 22, y + h // 2 - 6), (x + 22, y + h // 2 + 6), 3)
        lbl = font_big.render("Nouveau monde", True, TEXT_COLOR if selected else _MC_GRAY)
        screen.blit(lbl, (x + 36, y + h // 2 - lbl.get_height() // 2))
    else:
        if confirm_del:
            lbl = font_big.render("Ecraser ? (MINE = oui)", True, (255, 255, 255))
            screen.blit(lbl, (x + 10, y + h // 2 - lbl.get_height() // 2))
        else:
            seed_lbl = font_big.render("Seed : " + str(world["seed"]), True, _MC_YELLOW if selected else TEXT_COLOR)
            screen.blit(seed_lbl, (x + 10, y + 10))
            date_lbl = font_sm.render("Derniere partie : " + world["last_played"], True, _MC_GRAY)
            screen.blit(date_lbl, (x + 10, y + h - date_lbl.get_height() - 6))


def run(screen, joysticks):
    """
    Retourne (slot_id: int, seed: int) ou None pour quitter.
    slot_id est 1-indexed.
    """
    clock      = pygame.time.Clock()
    quit_combo = QuitCombo()
    font_big   = pygame.font.SysFont("Courier New", 13, bold=True)
    font_sm    = pygame.font.SysFont("Courier New", 10)
    font_title = pygame.font.SysFont("Courier New", 22, bold=True)
    font_hint  = pygame.font.SysFont("Courier New", 10)

    joy = joysticks[0] if joysticks else None

    selected    = 0          # slot sélectionné (0-3)
    confirm_del = None       # slot en attente de confirmation d'écrasement
    prev_dy     = 0
    prev_mine   = False
    prev_mod    = False
    start_t     = pygame.time.get_ticks()

    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None
            quit_combo.handle_event(e)

        if quit_combo.update_and_draw(screen):
            return None

        worlds   = db.list_worlds()   # [None | dict, ...]  index 0-3
        cur_mine = _joy_btn(joy, J1_BTN_MINE) or bool(keys[KB_J1_MINE])
        cur_mod  = _joy_btn(joy, J1_BTN_MODIFIER) or bool(keys[KB_J1_MODIFIER])
        _, dy    = _get_dir(keys, joy)

        # ── Navigation ───────────────────────────────────────────────────
        if dy != prev_dy and dy != 0:
            selected = (selected + dy) % MAX_SLOTS
            confirm_del = None

        # ── Action MINE seul = jouer / créer ─────────────────────────────
        if cur_mine and not prev_mine and not cur_mod:
            slot_id = selected + 1   # 1-indexed
            if confirm_del == selected:
                # Confirme l'écrasement
                seed = random.randint(0, 0xFFFF_FFFF)
                db.create_world(slot_id, seed)
                confirm_del = None
                return slot_id, seed
            elif worlds[selected] is None:
                # Slot vide → créer
                seed = random.randint(0, 0xFFFF_FFFF)
                db.create_world(slot_id, seed)
                return slot_id, seed
            else:
                # Slot occupé → charger
                db.touch_world(slot_id)
                return slot_id, worlds[selected]["seed"]

        # ── MODIFIER + MINE = demande d'écrasement ────────────────────────
        if cur_mod and cur_mine and not prev_mine:
            if worlds[selected] is not None:
                confirm_del = selected
            # Si slot vide + modifier+mine = aussi créer
            elif worlds[selected] is None:
                slot_id = selected + 1
                seed = random.randint(0, 0xFFFF_FFFF)
                db.create_world(slot_id, seed)
                return slot_id, seed

        # Annule la confirmation si on bouge
        if dy != 0:
            confirm_del = None

        prev_dy   = dy
        prev_mine = cur_mine
        prev_mod  = cur_mod

        # ── Rendu ─────────────────────────────────────────────────────────
        t = (pygame.time.get_ticks() - start_t) / 1000.0

        # Fond dégradé ciel
        for y in range(SCREEN_HEIGHT):
            r = min(255, int(_MC_SKY[0] + _MC_SKY[0] * 0.3 * y / SCREEN_HEIGHT))
            g = min(255, int(_MC_SKY[1] + _MC_SKY[1] * 0.1 * y / SCREEN_HEIGHT))
            b = max(0,   int(_MC_SKY[2] - _MC_SKY[2] * 0.3 * y / SCREEN_HEIGHT))
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Titre
        wiggle = int(math.sin(t * 2.5) * 1)
        title  = font_title.render("CHOISIR UN MONDE", True, _MC_YELLOW)
        shadow = font_title.render("CHOISIR UN MONDE", True, _MC_SHADOW)
        tx = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(shadow, (tx + 2, 12 + wiggle + 2))
        screen.blit(title,  (tx,     12 + wiggle))

        # Slots
        total_h = MAX_SLOTS * SLOT_H + (MAX_SLOTS - 1) * SLOT_GAP
        start_y = (SCREEN_HEIGHT - total_h) // 2 + 16
        for i in range(MAX_SLOTS):
            sx = (SCREEN_WIDTH - SLOT_W) // 2
            sy = start_y + i * (SLOT_H + SLOT_GAP)
            _draw_slot(
                screen, font_big, font_sm,
                (sx, sy, SLOT_W, SLOT_H),
                worlds[i],
                selected == i,
                confirm_del == i,
            )

        # Hints bas de page
        hints = [
            "MINE = Jouer / Creer",
            "MOD + MINE = Ecraser",
            "SELECT+START = Quitter",
        ]
        panel = pygame.Surface((SCREEN_WIDTH, 28), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        screen.blit(panel, (0, SCREEN_HEIGHT - 28))
        hint_txt = "  |  ".join(hints)
        hl = font_hint.render(hint_txt, True, (180, 180, 180))
        screen.blit(hl, ((SCREEN_WIDTH - hl.get_width()) // 2, SCREEN_HEIGHT - 20))

        pygame.display.flip()
