"""
Lecture des entrées clavier / manette et calcul du curseur cible.
"""
import pygame
from config import (
    AXIS_DEAD,
    J1_BTN_MINE, J1_BTN_MODIFIER,
    J1_BTN_UP, J1_BTN_DOWN, J1_BTN_LEFT, J1_BTN_RIGHT,
    BTN_A, BTN_B, BTN_X, BTN_Y,
    J2_BTN_MINE, J2_BTN_MINE2, J2_BTN_MODIFIER,
    KB_J1_UP, KB_J1_DOWN, KB_J1_LEFT, KB_J1_RIGHT,
    KB_J1_MINE, KB_J1_MODIFIER,
    KB_J2_UP, KB_J2_DOWN, KB_J2_LEFT, KB_J2_RIGHT,
    KB_J2_MINE, KB_J2_MODIFIER,
    PLAYER_W, PLAYER_H, TILE_SIZE, TILE_AIR,
)


def joy_btn(joy, btn):
    try:
        return bool(joy and joy.get_button(btn))
    except Exception:
        return False


# ── Directions ────────────────────────────────────────────────────────────────

def get_dir_p1(keys, joy):
    if joy:
        try:
            ax = joy.get_axis(0)
            ay = joy.get_axis(1)
            if ax < -AXIS_DEAD: return -1, 0
            if ax >  AXIS_DEAD: return  1, 0
            if ay < -AXIS_DEAD: return  0, -1
            if ay >  AXIS_DEAD: return  0,  1
        except Exception:
            pass
        try:
            hx, hy = joy.get_hat(0)
            if hx != 0 or hy != 0:
                return hx, -hy
        except Exception:
            pass
        try:
            if joy.get_button(J1_BTN_UP):    return  0, -1
            if joy.get_button(J1_BTN_DOWN):  return  0,  1
            if joy.get_button(J1_BTN_LEFT):  return -1,  0
            if joy.get_button(J1_BTN_RIGHT): return  1,  0
        except Exception:
            pass
    dx = dy = 0
    if keys[KB_J1_RIGHT]: dx =  1
    elif keys[KB_J1_LEFT]: dx = -1
    if keys[KB_J1_UP]: dy = -1
    elif keys[KB_J1_DOWN]: dy = 1
    return dx, dy


def get_dir_p2(keys, joy):
    if joy:
        try:
            pressed = {b for b in range(joy.get_numbuttons()) if joy.get_button(b)}
            dx = dy = 0
            if BTN_B in pressed: dx =  1
            if BTN_Y in pressed: dx = -1
            if BTN_X in pressed: dy = -1
            if BTN_A in pressed: dy =  1
            if dx != 0 or dy != 0:
                return dx, dy
        except Exception:
            pass
    dx = dy = 0
    if keys[KB_J2_RIGHT]: dx =  1
    elif keys[KB_J2_LEFT]: dx = -1
    if keys[KB_J2_UP]: dy = -1
    elif keys[KB_J2_DOWN]: dy = 1
    return dx, dy


# ── Curseur de bloc visé ──────────────────────────────────────────────────────

def get_cursor(player, dx, dy, world=None):
    """
    Retourne (col, row) du bloc ciblé en fonction de la direction tenue.
    En horizontal pur : pieds d'abord, remonte à la tête si pieds = air.
    """
    pw = PLAYER_W / TILE_SIZE
    ph = PLAYER_H / TILE_SIZE
    if dx == 0 and dy == 0:
        dx = 1

    if dx > 0:
        col = int(player.x + pw - 0.01) + 1
    elif dx < 0:
        col = int(player.x) - 1
    else:
        col = int(player.x + pw / 2)

    if dy > 0:
        row = int(player.y + ph - 0.01) + 1
    elif dy < 0:
        row = int(player.y) - 1
    else:
        feet_row = int(player.y + ph - 0.01)
        head_row = feet_row - 1
        if world is None or world.get(col, feet_row) != TILE_AIR:
            row = feet_row              # bloc solide aux pieds → miner
        elif world.get(col, head_row) != TILE_AIR:
            row = head_row              # bloc solide à la tête → miner surplomb
        elif world.get(col, feet_row + 1) != TILE_AIR:
            row = feet_row              # air au sol devant → placement naturel
        else:
            row = head_row              # au-dessus d'un trou

    return col, row
