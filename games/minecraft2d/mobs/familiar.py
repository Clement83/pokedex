"""
Systeme de familiers (animaux domestiques).

Chaque joueur peut avoir un seul familier :
  - Loup  : suit le joueur, attaque les mobs hostiles proches
  - Chat  : suit le joueur, ne fait rien (comme dans la vraie vie)
  - Poule : suit le joueur, pond un oeuf toutes les 60 s
"""
import math
import pygame
import sounds as _sounds

from config import TILE_SIZE, TILE_FISH, TILE_EGG, PLAYER_W, PLAYER_H, GRAVITY, MAX_FALL_SPEED, JUMP_VEL
from mobs.base import (
    Mob, MOB_CHICKEN, MOB_WOLF, MOB_CAT,
    _PASSIVE_MOBS, _TAMEABLE_MOBS,
    _mw, _mh, _MOB_PW, _MOB_PH, _MOB_COLOR, _MOB_HP,
)
from mobs.physics import _solid, _move_mob_x, _move_mob_y
from mobs.renderer import draw_mob

# ── Constantes familiers ────────────────────────────────────────────────────
_TAME_ITEMS = {
    MOB_WOLF:    TILE_FISH,    # apprivoiser avec du poisson
    MOB_CAT:     TILE_FISH,    # apprivoiser avec du poisson
    MOB_CHICKEN: None,         # gratuit (approche avec la main)
}

_TAME_RANGE       = 2.5    # distance max pour apprivoiser (tuiles)
_FOLLOW_DIST      = 2.0    # distance à laquelle le familier essaie de rester
_TELEPORT_DIST    = 20.0   # si trop loin → téléportation
_WOLF_ATTACK_RANGE = 6.0   # rayon de détection des ennemis pour le loup
_WOLF_ATTACK_DMG   = 2     # dégâts du loup par attaque
_WOLF_ATTACK_CD    = 1.5   # cooldown attaque loup (secondes)
_EGG_INTERVAL      = 60.0  # secondes entre chaque ponte

_FAM_NAMES = {
    MOB_WOLF:    "Loup",
    MOB_CAT:     "Chat",
    MOB_CHICKEN: "Poule",
}


class Familiar:
    """Un familier rattaché à un joueur."""

    def __init__(self, mob_type, x, y, owner_idx):
        self.mob_type   = mob_type
        self.x          = float(x)
        self.y          = float(y)
        self.vx         = 0.0
        self.vy         = 0.0
        self.on_ground  = False
        self.owner_idx  = owner_idx
        self.hp         = _MOB_HP[mob_type]
        self._attack_cd = 0.0
        self._egg_timer = 0.0
        self._jump_cd   = 0.0
        self._fly_phase = 0.0   # pour l'animation

    # ── Helpers géométriques (compatibles avec draw_mob) ────────────────
    def center_col(self):
        return self.x + _mw(self.mob_type) / 2

    def center_row(self):
        return self.y + _mh(self.mob_type) / 2

    def px(self):
        return self.x * TILE_SIZE

    def py(self):
        return self.y * TILE_SIZE


class FamiliarManager:
    """Gère les familiers des deux joueurs."""

    def __init__(self):
        self.familiars = [None, None]   # un par joueur

    # ── Apprivoisement ──────────────────────────────────────────────────

    def try_tame(self, player, player_idx, mob_mgr, loot_notifs):
        """
        Tente d'apprivoiser un mob sauvage proche.
        Retourne True si réussi.
        """
        if self.familiars[player_idx] is not None:
            loot_notifs.append(["Vous avez déjà un familier !", 1.5, (220, 160, 60)])
            return False

        px_center = player.x + PLAYER_W / TILE_SIZE / 2
        py_center = player.y + PLAYER_H / TILE_SIZE / 2

        best_mob  = None
        best_dist = _TAME_RANGE + 1

        for m in mob_mgr._mobs:
            if m.mob_type not in _TAMEABLE_MOBS:
                continue
            dx = m.center_col() - px_center
            dy = m.center_row() - py_center
            d  = math.hypot(dx, dy)
            if d < best_dist:
                best_dist = d
                best_mob  = m

        if best_mob is None:
            return False

        # Vérifier l'item requis
        required = _TAME_ITEMS.get(best_mob.mob_type)
        if required is not None:
            found = False
            for i, (tile, count) in enumerate(player.inventory.resources):
                if tile == required and count > 0:
                    if count == 1:
                        player.inventory.resources.pop(i)
                        player.inventory.resource_idx = max(
                            0, min(player.inventory.resource_idx, len(player.inventory.resources) - 1)
                        )
                    else:
                        player.inventory.resources[i] = (tile, count - 1)
                    found = True
                    break
            if not found:
                from config import TILE_NAMES
                name = TILE_NAMES.get(required, "?")
                loot_notifs.append([f"Il faut du {name} !", 1.5, (220, 120, 60)])
                return False

        # Créer le familier
        fam = Familiar(best_mob.mob_type, best_mob.x, best_mob.y, player_idx)
        self.familiars[player_idx] = fam

        # Retirer le mob du monde
        mob_mgr._mobs.remove(best_mob)

        name = _FAM_NAMES.get(best_mob.mob_type, "?")
        loot_notifs.append([f"{name} apprivoisé !", 3.0, (100, 255, 100)])
        _sounds.tame()
        return True

    # ── Mise à jour ─────────────────────────────────────────────────────

    def update(self, dt, players, world, mob_mgr, loot_notifs):
        for idx, fam in enumerate(self.familiars):
            if fam is None:
                continue
            player = players[idx]
            fam._attack_cd = max(0.0, fam._attack_cd - dt)
            fam._jump_cd   = max(0.0, fam._jump_cd - dt)
            fam._fly_phase += dt * 2.0

            # ── Téléportation si trop loin ──────────────────────────────
            dx = player.x - fam.x
            dy = player.y - fam.y
            dist = math.hypot(dx, dy)
            if dist > _TELEPORT_DIST:
                fam.x = player.x + (1.0 if dx > 0 else -1.0)
                fam.y = player.y
                fam.vx = fam.vy = 0.0
                continue

            # ── Loup : attaque les mobs hostiles ────────────────────────
            if fam.mob_type == MOB_WOLF and fam._attack_cd <= 0:
                self._wolf_attack(fam, player, mob_mgr, loot_notifs)

            # ── Poule : ponte d'œuf ─────────────────────────────────────
            if fam.mob_type == MOB_CHICKEN:
                fam._egg_timer += dt
                if fam._egg_timer >= _EGG_INTERVAL:
                    fam._egg_timer = 0.0
                    player.inventory.add(TILE_EGG)
                    loot_notifs.append(["Votre poule a pondu un oeuf !", 2.5, (245, 235, 210)])
                    _sounds.egg()

            # ── Suivi du joueur ─────────────────────────────────────────
            self._follow_owner(fam, player, dt, world)

    def _wolf_attack(self, fam, owner, mob_mgr, loot_notifs):
        """Le loup attaque le mob hostile le plus proche du joueur."""
        pcx = owner.x + PLAYER_W / TILE_SIZE / 2
        pcy = owner.y + PLAYER_H / TILE_SIZE / 2

        target = None
        target_dist = _WOLF_ATTACK_RANGE + 1

        for m in mob_mgr._mobs:
            if m.mob_type in _PASSIVE_MOBS or m.mob_type in _TAMEABLE_MOBS:
                continue
            dx = m.center_col() - pcx
            dy = m.center_row() - pcy
            d  = math.hypot(dx, dy)
            if d < target_dist:
                target_dist = d
                target = m

        if target is None:
            return

        # Distance loup → cible
        tdx   = target.center_col() - fam.center_col()
        tdist = abs(tdx)

        if tdist < 1.5:
            # Attaquer
            target.hp -= _WOLF_ATTACK_DMG
            fam._attack_cd = _WOLF_ATTACK_CD
            if target.hp <= 0:
                target.vanish = True
                from mobs.drops import roll_drops
                from scenes.game.actions import _collect_drops
                drops = roll_drops(target.mob_type)
                if drops:
                    _collect_drops(owner, drops, loot_notifs)
            _sounds.sword_hit()
        else:
            # Se diriger vers la cible (override le suivi du joueur)
            speed = 4.5
            fam.vx = math.copysign(speed, tdx)

    def _follow_owner(self, fam, owner, dt, world):
        """Déplace le familier pour suivre son propriétaire."""
        pw = PLAYER_W / TILE_SIZE
        ph = PLAYER_H / TILE_SIZE

        target_x = owner.x - _mw(fam.mob_type) / 2 + pw / 2
        target_y = owner.y

        dx = target_x - fam.x
        dy = target_y - fam.y
        dist = math.hypot(dx, dy)

        # Se déplace vers le joueur si trop loin
        if dist > _FOLLOW_DIST:
            speed = 4.5 if dist > 5.0 else 3.0
            fam.vx = math.copysign(speed, dx) if abs(dx) > 0.3 else 0.0

            # Saut si mur devant
            if fam.on_ground and fam._jump_cd <= 0:
                dir_x = 1 if dx > 0 else -1
                check_col = int(fam.x + dir_x * (_mw(fam.mob_type) + 0.1))
                if _solid(world, check_col, int(fam.center_row())):
                    fam.vy = JUMP_VEL * 0.75
                    fam._jump_cd = 0.5
        else:
            fam.vx *= 0.8  # friction douce quand assez proche

        # Gravité
        fam.vy = min(fam.vy + GRAVITY * dt, MAX_FALL_SPEED)

        # Déplacement avec collision
        _move_mob_x(fam, world, fam.vx * dt)
        _move_mob_y(fam, world, fam.vy * dt)

    # ── Rendu ───────────────────────────────────────────────────────────

    def draw(self, screen, camera):
        for fam in self.familiars:
            if fam is None:
                continue
            sx, sy = camera.world_to_screen(fam.px(), fam.py())
            mw = _MOB_PW[fam.mob_type]
            mh = _MOB_PH[fam.mob_type]
            vw = camera.view_w
            vh = camera.view_h
            if sx + mw < 0 or sx > vw or sy + mh < 0 or sy > vh:
                continue
            # Dessiner le mob normalement
            draw_mob(screen, fam, camera)
            # Petit coeur au-dessus
            hx = sx + mw // 2 - 3
            hy = sy - 6
            _draw_heart(screen, hx, hy)

    # ── Sérialisation ───────────────────────────────────────────────────

    def save_data(self, player_idx):
        """Retourne les données sérialisables du familier (ou None)."""
        fam = self.familiars[player_idx]
        if fam is None:
            return None
        return {
            "type": fam.mob_type,
            "hp":   fam.hp,
            "egg":  fam._egg_timer,
        }

    def load_data(self, player_idx, data, player):
        """Charge un familier depuis les données sauvegardées."""
        if data is None:
            self.familiars[player_idx] = None
            return
        fam = Familiar(
            data["type"],
            player.x + 1.0,
            player.y,
            player_idx,
        )
        fam.hp = data.get("hp", _MOB_HP[data["type"]])
        fam._egg_timer = data.get("egg", 0.0)
        self.familiars[player_idx] = fam

    # ── Libérer un familier ─────────────────────────────────────────────

    def release(self, player_idx, loot_notifs):
        """Libère le familier du joueur (redevient sauvage)."""
        fam = self.familiars[player_idx]
        if fam is None:
            return
        name = _FAM_NAMES.get(fam.mob_type, "?")
        self.familiars[player_idx] = None
        loot_notifs.append([f"{name} libéré !", 2.0, (180, 180, 180)])


def _draw_heart(screen, x, y):
    """Dessine un petit coeur rouge 5×4 px."""
    dr = pygame.draw.rect
    c = (255, 60, 80)
    dr(screen, c, (x,     y,     2, 1))
    dr(screen, c, (x + 3, y,     2, 1))
    dr(screen, c, (x,     y + 1, 5, 1))
    dr(screen, c, (x + 1, y + 2, 3, 1))
    dr(screen, c, (x + 2, y + 3, 1, 1))
