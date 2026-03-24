"""
Système de troc entre les deux joueurs.

Déclenchement : outil Main + bouton action quand les joueurs sont adjacents.
Chaque joueur navigue dans son propre inventaire (haut/bas) et donne
un objet à l'autre en appuyant sur son bouton action.
Un bouton Modifier (Alt) côté n'importe quel joueur ferme le menu.
"""
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    EQUIP_NAMES, TILE_NAMES, MAT_NAMES,
)

_MENU_W  = 300
_MENU_H  = 190
_COL_W   = (_MENU_W - 24) // 2
_ROW_H   = 15
_PAD     = 6
_VIS     = (_MENU_H - 50) // _ROW_H   # lignes visibles par colonne


# ── Helpers inventaire ────────────────────────────────────────────────────────

def _tradable(inv):
    """
    Retourne la liste des objets échangeables de cet inventaire.
    Chaque entrée : {'label': str, 'kind': 'res'|'equip', 'item': ...}
    """
    items = []
    for tile, count in inv.resources:
        label = TILE_NAMES.get(tile, "?")
        items.append({'label': f"{label} \u00d7{count}", 'kind': 'res', 'item': tile})
    for mat in inv.swords:
        items.append({'label': f"\u00c9p\u00e9e {MAT_NAMES.get(mat,'?')}",
                      'kind': 'equip', 'item': (EQUIP_SWORD, mat)})
    for mat in inv.pickaxes:
        items.append({'label': f"Pioche {MAT_NAMES.get(mat,'?')}",
                      'kind': 'equip', 'item': (EQUIP_PICKAXE, mat)})
    for slot in (EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET):
        for piece in inv.equip.get(slot, []):
            items.append({'label': EQUIP_NAMES.get(piece, '?'),
                          'kind': 'equip', 'item': piece})
    return items


def _do_give(src, dst, entry):
    """Transfère un objet de src vers dst. Retourne True si succès."""
    kind = entry['kind']
    item = entry['item']

    if kind == 'res':
        tile = item
        for i, (t, c) in enumerate(src.resources):
            if t == tile and c > 0:
                if c == 1:
                    src.resources.pop(i)
                else:
                    src.resources[i] = (t, c - 1)
                src.resource_idx = max(0, min(src.resource_idx,
                                              len(src.resources) - 1))
                dst.add(tile)
                return True
        return False

    else:  # 'equip'
        eslot, mat = item
        if eslot == EQUIP_SWORD:
            if mat in src.swords:
                src.swords.remove(mat)
                src.sword_idx = max(0, min(src.sword_idx,
                                           len(src.swords) - 1))
                dst.add_equip(item)
                return True
        elif eslot == EQUIP_PICKAXE:
            if mat in src.pickaxes:
                src.pickaxes.remove(mat)
                src.pickaxe_idx = max(0, min(src.pickaxe_idx,
                                             len(src.pickaxes) - 1))
                dst.add_equip(item)
                return True
        else:
            lst = src.equip.get(eslot, [])
            if item in lst:
                lst.remove(item)
                src.equip_idx[eslot] = max(0, min(src.equip_idx.get(eslot, 0),
                                                   len(lst) - 1))
                dst.add_equip(item)
                return True
        return False


# ── Classe principale ─────────────────────────────────────────────────────────

class TradeMenu:
    def __init__(self):
        self.visible   = False
        self._cursor   = [0, 0]
        self._bg_surf  = None   # alloué à la demande

    def open(self):
        self.visible   = True
        self._cursor   = [0, 0]

    def close(self):
        self.visible = False

    def navigate(self, player_idx, dy):
        """Déplace le curseur du joueur player_idx (dy = -1 ou +1)."""
        # On calcule la longueur à draw() time, ici on clipse au prochain draw
        self._cursor[player_idx] = max(0, self._cursor[player_idx] + dy)

    def give(self, giver_idx, players):
        """
        Le joueur giver_idx donne son objet sélectionné à l'autre joueur.
        Retourne un message de notification ou None si impossible.
        """
        src = players[giver_idx].inventory
        dst = players[1 - giver_idx].inventory

        items = _tradable(src)
        if not items:
            return None

        # Clamp cursor
        self._cursor[giver_idx] = min(self._cursor[giver_idx], len(items) - 1)
        entry = items[self._cursor[giver_idx]]

        if _do_give(src, dst, entry):
            # Reclamper après suppression
            new_items = _tradable(src)
            self._cursor[giver_idx] = min(self._cursor[giver_idx],
                                          max(0, len(new_items) - 1))
            label = entry['label'].split(' ×')[0]   # sans la quantité
            return f"J{giver_idx + 1} \u2192 J{2 - giver_idx}: {label}"
        return None

    def draw(self, screen, players, font):
        """Affiche le panneau de troc centré à l'écran."""
        mx = (SCREEN_WIDTH  - _MENU_W) // 2
        my = (SCREEN_HEIGHT - _MENU_H) // 2

        # Fond semi-transparent (pré-alloué)
        if self._bg_surf is None:
            self._bg_surf = pygame.Surface((_MENU_W, _MENU_H), pygame.SRCALPHA)
        self._bg_surf.fill((12, 12, 22, 225))
        screen.blit(self._bg_surf, (mx, my))

        # Bordure fine blanche
        pygame.draw.rect(screen, (200, 200, 200), (mx, my, _MENU_W, _MENU_H), 1)

        # Titre centré
        title = font.render("\u2500\u2500 TROC \u2500\u2500  Mod=quitter", True, (220, 220, 120))
        screen.blit(title, (mx + (_MENU_W - title.get_width()) // 2, my + _PAD))
        pygame.draw.line(screen, (80, 80, 80),
                         (mx + _PAD, my + 18), (mx + _MENU_W - _PAD, my + 18), 1)

        # Séparateur central
        cx_mid = mx + _MENU_W // 2
        pygame.draw.line(screen, (60, 60, 70),
                         (cx_mid, my + 18), (cx_mid, my + _MENU_H - 18), 1)
        arrow = font.render("\u21c4", True, (160, 160, 160))
        screen.blit(arrow, (cx_mid - arrow.get_width() // 2,
                            my + _MENU_H // 2 - arrow.get_height() // 2))

        for pi, player in enumerate(players):
            inv   = player.inventory
            items = _tradable(inv)

            # Clamp cursor
            if items:
                self._cursor[pi] = min(self._cursor[pi], len(items) - 1)
            else:
                self._cursor[pi] = 0

            col_x = mx + _PAD + pi * (_COL_W + 12)

            # Header joueur
            hdr = font.render(f"J{pi + 1}", True, player.color)
            screen.blit(hdr, (col_x, my + 22))

            if not items:
                empty = font.render("(vide)", True, (100, 100, 100))
                screen.blit(empty, (col_x, my + 36))
                continue

            # Scroll
            cursor  = self._cursor[pi]
            start   = max(0, cursor - _VIS + 1)
            visible = items[start: start + _VIS]

            for vi, entry in enumerate(visible):
                ri  = start + vi
                ry  = my + 35 + vi * _ROW_H
                act = (ri == cursor)

                if act:
                    pygame.draw.rect(screen, (55, 45, 10),
                                     (col_x - 1, ry - 1, _COL_W - 2, _ROW_H))
                color = (255, 225, 60) if act else (185, 185, 185)
                label = entry['label']
                if len(label) > 16:
                    label = label[:15] + "\u2026"
                lbl = font.render(label, True, color)
                screen.blit(lbl, (col_x + 2, ry + 1))

        # Légende bas
        leg = font.render("\u2191\u2193 nav   Action = donner", True, (100, 100, 100))
        screen.blit(leg, (mx + _PAD, my + _MENU_H - 13))
