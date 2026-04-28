# Motodash + Beta Toggle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 2D Trials-style motorcycle game (`motodash`) and add a `F4`-toggled beta filter to the launcher so unstable games (`motodash` + `doom`) are hidden by default.

**Architecture:** Self-contained pygame game with hand-rolled rigid-body physics (single bike body, two derived wheel positions tested against a polyline terrain). The launcher gains a `beta` flag per game and a keyboard-only filter. No new dependencies — pygame + numpy only.

**Tech Stack:** Python 3.10, pygame 2.6.1, numpy 1.24.4. No test framework — validation is manual run-and-play, consistent with the rest of this codebase.

**Spec:** `docs/superpowers/specs/2026-04-28-motodash-beta-toggle-design.md`

---

## File Map

**Modified outside `games/motodash/`:**
- `main.py` (root) — adds beta entries, passes full list to launcher, accepts dict return.
- `launcher.py` — refactors image storage to dicts, adds beta filter + F4 toggle + BETA badge, returns dict from `handle_event`.

**Created in `games/motodash/`:**
- `config.py` — constants (screen, physics, controls, medals).
- `levels.py` — 3 fixed level definitions (terrain polyline, start, finish, checkpoints, target times).
- `scores.py` — JSON I/O for best times at `~/.config/pokedex/motodash.json`.
- `bike.py` — bike state + Euler integration step.
- `terrain.py` — terrain rendering + per-wheel collision against polyline.
- `scene_game.py` — input → physics → render loop, chrono, checkpoints.
- `scene_select.py` — level selection menu with medals.
- `scene_result.py` — end screen (time, medal, retry/back).
- `main.py` — pygame init, splash, scene state machine.
- `CLAUDE.md` — internal doc, mirroring other games' style.
- `cover.png` — generated procedurally on first task that needs it.

---

## Part A — Launcher Beta Toggle

This part lands first because it's prerequisite to wiring `motodash` and `doom` as beta entries, and validates the refactor independently of the new game.

### Task 1: Refactor launcher images to dicts keyed by game id

**Why:** Currently `self.images` and `self.bg_images` are lists indexed parallel to `self.games`. Once we filter the list, those indices desync. Switching to dicts keyed by a stable id (the `title` field — guaranteed unique across `GAMES`) makes filtering safe.

**Files:**
- Modify: `launcher.py`

- [ ] **Step 1.1 — Replace `_load_images` and `_load_bg_images` to return dicts**

In `launcher.py`, replace the two methods:

```python
def _load_images(self):
    images = {}
    for game in self.games:
        img = None
        img_path = game.get("image")
        if img_path and os.path.exists(img_path):
            try:
                raw = pygame.image.load(img_path).convert()
                img = self._cover_crop(raw, IMG_W, IMG_H)
            except Exception:
                pass
        images[game["title"]] = img
    return images

def _load_bg_images(self):
    sw, sh = self.screen.get_size()
    bgs = {}
    for game in self.games:
        bg = None
        img_path = game.get("image")
        if img_path and os.path.exists(img_path):
            try:
                raw = pygame.image.load(img_path).convert()
                bg = self._cover_crop(raw, sw, sh)
            except Exception:
                pass
        bgs[game["title"]] = bg
    return bgs
```

- [ ] **Step 1.2 — Update `render` to look up images by title**

Replace the two image lookups in `render`:

```python
# Was: bg = self.bg_images[self.selected]
bg = self.bg_images.get(self.games[self.selected]["title"])
```

```python
# Was: if self.images[i]:
img = self.images.get(g["title"])
if img:
    self.screen.blit(img, (img_x, img_y))
else:
```

(Adjust the `else` branch accordingly — keep the existing placeholder code, just change the condition.)

- [ ] **Step 1.3 — Run launcher and verify the 5 existing games still display correctly**

```bash
cd /home/clement/Documents/projets/POC/pokedex
python main.py
```

Expected: carousel shows the 5 games with their cover art, navigation works left/right, selecting launches the game. Close after verifying.

- [ ] **Step 1.4 — Commit**

```bash
git add launcher.py
git commit -m "refactor(launcher): index images by game title instead of position"
```

---

### Task 2: Make `handle_event` return the selected game dict, not an index

**Why:** Once the launcher filters its visible list, returning an index is ambiguous (index into which list?). Returning the game dict directly removes the question.

**Files:**
- Modify: `launcher.py`
- Modify: `main.py`

- [ ] **Step 2.1 — Update `handle_event` to return the dict**

In `launcher.py`, replace each `return self.selected` (or `return idx`) line that yields an index by `return self.games[self.selected]`. Keep `return -1` for ESC and `return None` otherwise.

Specifically the four `return` paths in `handle_event`:

```python
# K_RETURN / K_n
if self.is_available(self.games[self.selected]):
    return self.games[self.selected]
```

```python
# K_ESCAPE
return -1
```

```python
# JOYBUTTONDOWN buttons 0/1
if self.is_available(self.games[self.selected]):
    return self.games[self.selected]
```

The other navigation branches still `return None` implicitly.

- [ ] **Step 2.2 — Update `main.py` consumer**

In `main.py`, replace:

```python
if result is not None:
    if result == -1:
        running = False
    else:
        game = GAMES[result]
        _music.stop()
        launch_game(game)
        sys.exit(0)
```

With:

```python
if result is not None:
    if result == -1:
        running = False
    else:
        _music.stop()
        launch_game(result)
        sys.exit(0)
```

- [ ] **Step 2.3 — Run launcher, verify selecting each game still launches it**

```bash
python main.py
```

Click into each of the 5 games, hit Échap from each (or quit_combo) to come back. All 5 should launch correctly.

- [ ] **Step 2.4 — Commit**

```bash
git add launcher.py main.py
git commit -m "refactor(launcher): return game dict from handle_event instead of index"
```

---

### Task 3: Add `beta` field, `show_beta` flag, and visible-list filtering

**Why:** Core of the toggle feature. After this task, `F4` won't work yet but the `beta` mechanism is wired and the visible list is filtered.

**Files:**
- Modify: `launcher.py`

- [ ] **Step 3.1 — Add filtering state in `__init__`**

In `launcher.py`, after `self.games = games`, add:

```python
self.show_beta = False
self.visible_games = self._compute_visible()
```

Add the helper method (anywhere in the class, e.g. after `_load_bg_images`):

```python
def _compute_visible(self):
    if self.show_beta:
        return list(self.games)
    return [g for g in self.games if not g.get("beta", False)]
```

- [ ] **Step 3.2 — Replace all `self.games` reads in event handling and rendering with `self.visible_games`**

In `handle_event`:
- `len(self.games)` → `len(self.visible_games)` (4 occurrences in the navigation branches).
- `self.games[self.selected]` → `self.visible_games[self.selected]` (3 occurrences in confirm-selection branches).

In `render`:
- `self.games[self.selected]` → `self.visible_games[self.selected]`
- `for i, g in enumerate(self.games):` → `for i, g in enumerate(self.visible_games):`
- `len(self.games) - 1` → `len(self.visible_games) - 1`
- `n = len(self.games)` → `n = len(self.visible_games)`

In `update`:
- `self.selected * step` is fine (uses `self.selected`, no list reference).

Defensive: at top of `render`, before `bg = ...`:

```python
if not self.visible_games:
    self.screen.fill(BG_COLOR)
    msg = self.font_header.render("Aucun jeu disponible", True, HEADER_COLOR)
    w, h = self.screen.get_size()
    self.screen.blit(msg, ((w - msg.get_width()) // 2, (h - msg.get_height()) // 2))
    return
self.selected = max(0, min(self.selected, len(self.visible_games) - 1))
```

- [ ] **Step 3.3 — Run launcher and verify 5 games still display (no beta entries yet, no behavior change visible)**

```bash
python main.py
```

Expected: identical to before. This is a refactor-only task. Quit.

- [ ] **Step 3.4 — Commit**

```bash
git add launcher.py
git commit -m "feat(launcher): add beta filter scaffolding (visible_games + show_beta)"
```

---

### Task 4: Hook F4 to toggle `show_beta`

**Files:**
- Modify: `launcher.py`

- [ ] **Step 4.1 — Add F4 handler in `handle_event`**

In `launcher.py`, inside `if event.type == pygame.KEYDOWN:`, add as the first sub-branch:

```python
if event.key == pygame.K_F4:
    self.show_beta = not self.show_beta
    self.visible_games = self._compute_visible()
    self.selected = 0
    return None
```

- [ ] **Step 4.2 — Verify run still OK (still no beta entries to test against, but no regression)**

```bash
python main.py
```

Press F4 several times — should be silent (no beta games yet). Quit.

- [ ] **Step 4.3 — Commit**

```bash
git add launcher.py
git commit -m "feat(launcher): F4 toggles show_beta"
```

---

### Task 5: Render BETA badge on beta tiles

**Files:**
- Modify: `launcher.py`

- [ ] **Step 5.1 — Add BETA badge rendering inside the tile loop**

In `launcher.py`, inside `render`'s `for i, g in enumerate(self.visible_games):` loop, after the title is drawn (after `self.screen.blit(title_surf, (title_x, title_y))`), add:

```python
if g.get("beta"):
    badge_w, badge_h = 40, 14
    badge_x = x + TILE_W - badge_w - 4
    badge_y = tile_y + 4
    badge_rect = pygame.Rect(badge_x, badge_y, badge_w, badge_h)
    pygame.draw.rect(self.screen, (245, 200, 60), badge_rect, border_radius=3)
    badge_font = pygame.font.SysFont("Arial", 10, bold=True)
    badge_surf = badge_font.render("BETA", True, (20, 20, 20))
    self.screen.blit(
        badge_surf,
        (badge_x + (badge_w - badge_surf.get_width()) // 2,
         badge_y + (badge_h - badge_surf.get_height()) // 2),
    )
```

- [ ] **Step 5.2 — Commit (no visual change yet — wired in Task 6)**

```bash
git add launcher.py
git commit -m "feat(launcher): render BETA badge on tiles flagged beta"
```

---

### Task 6: Add Doom and Motodash placeholders to GAMES with `beta=True`

**Files:**
- Modify: `main.py`

- [ ] **Step 6.1 — Add the two new entries**

In `main.py` (root), at the end of the `GAMES` list (before the closing `]`):

```python
    {
        "title": "DOOM",
        "description": "DOOM (BETA – clavier dev uniquement)",
        "image": str(BASE_DIR / "games" / "doom" / "cover.png"),
        "path": str(BASE_DIR / "games" / "doom"),
        "entry": "main",
        "beta": True,
    },
    {
        "title": "Motodash",
        "description": "Trials 2D – chrono + médailles (BETA)",
        "image": str(BASE_DIR / "games" / "motodash" / "cover.png"),
        "path": str(BASE_DIR / "games" / "motodash"),
        "entry": "main",
        "beta": True,
    },
```

Note: `motodash/cover.png` and `motodash/main.py` don't exist yet. The launcher's `is_available` check already handles missing entries gracefully (the tile shows "(bientôt)" and won't launch). Doom's cover and main.py both exist.

- [ ] **Step 6.2 — Verify default behavior (Odroid mode): only 5 stable games show**

```bash
python main.py
```

Expected: carousel shows 5 games (Pokédex, Shifter, Pong, Bomberman, Minecraft 2D). DOOM and Motodash are NOT visible. Quit.

- [ ] **Step 6.3 — Verify F4 reveals the 2 beta games with BETA badge**

```bash
python main.py
```

Press F4. Expected: carousel now shows 7 games. DOOM and Motodash appear with a yellow `BETA` badge in the top-right of their tile. Motodash is grayed out (no main.py yet, label "(bientôt)"). DOOM is selectable and would launch. Press F4 again — back to 5 games. Quit.

- [ ] **Step 6.4 — Commit**

```bash
git add main.py
git commit -m "feat(launcher): register DOOM and Motodash as beta games"
```

---

## Part B — Motodash Game

### Task 7: Create motodash skeleton — `config.py`

**Files:**
- Create: `games/motodash/config.py`

- [ ] **Step 7.1 — Write `games/motodash/config.py`**

```python
# ── Motodash – Constantes ────────────────────────────────────────────────────

# Écran
SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 60

# Couleurs
BG_COLOR     = (135, 180, 220)   # ciel
TERRAIN_COLOR = (95, 75, 55)     # marron sol
TERRAIN_LINE  = (40, 30, 20)
BIKE_BODY     = (200, 50, 40)
BIKE_WHEEL    = (25, 25, 25)
BIKE_RIDER    = (235, 200, 165)
TEXT_COLOR    = (245, 245, 245)
HUD_BG        = (0, 0, 0, 140)

# ── Physique ─────────────────────────────────────────────────────────────────
GRAVITY        = 1200.0   # px/s²
THROTTLE_FORCE = 800.0    # poussée le long de l'axe châssis (px/s²)
BRAKE_FORCE    = 1500.0
LEAN_TORQUE    = 6.0      # rad/s² appliqué tant que l'input gauche/droite est tenu
AIR_DRAG       = 0.5      # coefficient d'amortissement linéaire en l'air
ANGULAR_DRAG   = 2.5      # amortissement rotation
WHEEL_RADIUS   = 8.0
WHEELBASE      = 28.0     # distance entre les 2 roues
SUSPENSION_K   = 1500.0   # raideur ressort (impulsion normale)
SUSPENSION_C   = 30.0     # amortissement
GROUND_FRICTION = 0.85    # coeff friction tangentielle (0=glisse, 1=accroche parfaite)
CRASH_ANGLE_DEG = 110.0   # au-delà de cette inclinaison → crash

# ── Contrôles ────────────────────────────────────────────────────────────────
AXIS_DEAD = 0.4

# Manette (indices pygame, voir CONTROLLERS.md à la racine)
BTN_THROTTLE = 1   # A
BTN_BRAKE    = 0   # B
BTN_RESET    = 2   # X
BTN_LEFT     = 10  # D-pad gauche
BTN_RIGHT    = 11  # D-pad droite
BTN_SELECT   = 12  # combo quit
BTN_START    = 17  # combo quit

# ── Médailles ────────────────────────────────────────────────────────────────
MEDAL_GOLD   = "gold"
MEDAL_SILVER = "silver"
MEDAL_BRONZE = "bronze"
MEDAL_NONE   = None
MEDAL_COLORS = {
    MEDAL_GOLD:   (235, 195, 55),
    MEDAL_SILVER: (190, 190, 200),
    MEDAL_BRONZE: (180, 110, 60),
}
```

- [ ] **Step 7.2 — Commit**

```bash
git add games/motodash/config.py
git commit -m "feat(motodash): add config constants"
```

---

### Task 8: Score persistence — `scores.py`

**Files:**
- Create: `games/motodash/scores.py`

- [ ] **Step 8.1 — Write `games/motodash/scores.py`**

```python
import json
import os
from pathlib import Path

# logger lives at the project root; we are run with sys.path including the project root
from logger import log

import config


_SCORE_PATH = Path.home() / ".config" / "pokedex" / "motodash.json"


def _empty_state():
    return {"best_times": {}}


def load():
    """Charge l'état des scores. Tolérant : retourne un état vide en cas d'erreur."""
    try:
        if not _SCORE_PATH.exists():
            return _empty_state()
        with _SCORE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "best_times" not in data:
            log("[motodash] scores.json malformed, resetting", "warning")
            return _empty_state()
        return data
    except Exception as e:
        log(f"[motodash] scores load failed: {e}", "warning")
        return _empty_state()


def save(state):
    try:
        _SCORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SCORE_PATH.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"[motodash] scores save failed: {e}", "error")


def medal_for_time(level, time_seconds):
    """Retourne 'gold' / 'silver' / 'bronze' / None pour un temps donné."""
    if time_seconds <= level["gold"]:
        return config.MEDAL_GOLD
    if time_seconds <= level["silver"]:
        return config.MEDAL_SILVER
    if time_seconds <= level["bronze"]:
        return config.MEDAL_BRONZE
    return config.MEDAL_NONE


def record_time(state, level_id, time_seconds, medal):
    """Met à jour state['best_times'][level_id] si le temps est meilleur. Modifie state in-place."""
    bt = state.setdefault("best_times", {})
    prev = bt.get(level_id)
    if prev is None or time_seconds < prev["time"]:
        bt[level_id] = {"time": time_seconds, "medal": medal}
        return True
    return False
```

- [ ] **Step 8.2 — Quick smoke test (manual REPL, no commit)**

```bash
cd /home/clement/Documents/projets/POC/pokedex/games/motodash
PYTHONPATH=/home/clement/Documents/projets/POC/pokedex python -c "
import sys; sys.path.insert(0, '.')
import scores
s = scores.load()
print('initial:', s)
scores.record_time(s, 'easy', 30.5, 'silver')
scores.save(s)
s2 = scores.load()
print('reloaded:', s2)
"
```

Expected: prints initial state (empty `best_times`), then reloaded state with `easy` entry. File exists at `~/.config/pokedex/motodash.json`.

- [ ] **Step 8.3 — Clean test artefact and commit**

```bash
rm -f ~/.config/pokedex/motodash.json
cd /home/clement/Documents/projets/POC/pokedex
git add games/motodash/scores.py
git commit -m "feat(motodash): JSON-backed best-times persistence"
```

---

### Task 9: Level data — `levels.py` with one `easy` level

**Why:** We start with one playable level so we can run the game end-to-end before defining medium/hard. The other two are added later (Task 16).

**Files:**
- Create: `games/motodash/levels.py`

- [ ] **Step 9.1 — Write `games/motodash/levels.py`**

```python
# Niveaux statiques. Terrain = liste (x, y) triée par x, y croît vers le bas
# (système pygame standard, donc valeurs y plus grandes = plus bas à l'écran).

LEVELS = [
    {
        "id": "easy",
        "name": "Premiers tours",
        # Terrain plat avec quelques bosses douces, total ~1800 px
        "terrain": [
            (-200, 240),
            (0, 240),
            (200, 240),
            (300, 230),
            (400, 240),
            (500, 240),
            (650, 220),  # petite bosse
            (800, 240),
            (950, 250),
            (1100, 235),
            (1250, 245),
            (1400, 240),
            (1550, 220),  # rampe vers fin
            (1700, 240),
            (1850, 240),
            (2050, 240),
        ],
        "start": (50, 200),
        "finish_x": 1800,
        "checkpoints": [600, 1200],
        "gold":   25.0,
        "silver": 35.0,
        "bronze": 50.0,
    },
]


def get(level_id):
    for lvl in LEVELS:
        if lvl["id"] == level_id:
            return lvl
    raise KeyError(f"Unknown level: {level_id}")
```

- [ ] **Step 9.2 — Commit**

```bash
git add games/motodash/levels.py
git commit -m "feat(motodash): level data — easy"
```

---

### Task 10: Bike physics — `bike.py`

**Files:**
- Create: `games/motodash/bike.py`

- [ ] **Step 10.1 — Write `games/motodash/bike.py`**

```python
import math

import config


class Bike:
    def __init__(self, start_pos):
        self.x, self.y = start_pos
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0          # radians, 0 = horizontal, + = nez en haut
        self.angular_vel = 0.0
        self.on_ground = False
        # Inputs
        self.throttle = 0.0
        self.brake = 0.0
        self.lean = 0.0           # -1 (gauche), 0, +1 (droite)
        self.crashed = False

    # ── Position des roues (monde) ────────────────────────────────────────
    def wheel_positions(self):
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        half = config.WHEELBASE / 2.0
        # axe local x = vers l'avant ; le pilote regarde vers la droite à angle=0
        rear_x  = self.x - cos_a * half
        rear_y  = self.y - sin_a * half
        front_x = self.x + cos_a * half
        front_y = self.y + sin_a * half
        return (rear_x, rear_y), (front_x, front_y)

    # ── Réception des inputs (binaires) ───────────────────────────────────
    def set_inputs(self, throttle, brake, lean):
        self.throttle = 1.0 if throttle else 0.0
        self.brake = 1.0 if brake else 0.0
        self.lean = float(lean)  # -1, 0, +1

    # ── Reset au checkpoint ───────────────────────────────────────────────
    def reset_to(self, pos):
        self.x, self.y = pos
        self.vx = self.vy = 0.0
        self.angle = 0.0
        self.angular_vel = 0.0
        self.crashed = False

    # ── Intégration une frame ─────────────────────────────────────────────
    def step(self, dt, terrain):
        # Forces linéaires
        ax, ay = 0.0, config.GRAVITY

        if self.on_ground and self.throttle > 0:
            cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
            ax += cos_a * config.THROTTLE_FORCE * self.throttle
            ay += sin_a * config.THROTTLE_FORCE * self.throttle

        # Drag
        ax -= self.vx * config.AIR_DRAG
        ay -= self.vy * config.AIR_DRAG

        self.vx += ax * dt
        self.vy += ay * dt

        # Brake — réduction directe de la vitesse quand au sol
        if self.on_ground and self.brake > 0:
            decel = config.BRAKE_FORCE * dt
            speed = math.hypot(self.vx, self.vy)
            if speed > decel:
                self.vx -= (self.vx / speed) * decel
                self.vy -= (self.vy / speed) * decel
            else:
                self.vx = self.vy = 0.0

        # Couple : input lean
        self.angular_vel += self.lean * config.LEAN_TORQUE * dt
        # Damping rotation
        self.angular_vel -= self.angular_vel * config.ANGULAR_DRAG * dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.angular_vel * dt

        # Collisions roues / sol
        self._resolve_collisions(dt, terrain)

        # Crash check
        norm = self._normalized_angle()
        if abs(math.degrees(norm)) > config.CRASH_ANGLE_DEG:
            self.crashed = True

    def _normalized_angle(self):
        # Ramène l'angle dans [-pi, pi]
        a = (self.angle + math.pi) % (2 * math.pi) - math.pi
        return a

    def _resolve_collisions(self, dt, terrain):
        rear, front = self.wheel_positions()
        on_ground_any = False
        for wheel_pos, sign in ((rear, -1.0), (front, +1.0)):
            wx, wy = wheel_pos
            ground_y = terrain.height_at(wx)
            if ground_y is None:
                continue
            penetration = (wy + config.WHEEL_RADIUS) - ground_y
            if penetration > 0:
                on_ground_any = True
                # Correction position : remonter le centre de masse
                # (en supposant que la pénétration s'applique au châssis)
                self.y -= penetration * 0.5
                # Impulsion normale sur la vitesse linéaire
                if self.vy > 0:
                    self.vy = -self.vy * 0.1  # rebond très amorti
                # Friction tangentielle
                self.vx *= config.GROUND_FRICTION
                # Couple : la roue qui touche tire la moto vers la pente locale
                slope = terrain.slope_at(wx)
                target_angle = math.atan(slope)
                # tendance à s'aligner sur la pente (proportionnel à l'écart)
                err = self._angle_diff(target_angle, self.angle)
                self.angular_vel += err * 8.0 * dt * sign * 0.5
        self.on_ground = on_ground_any

    @staticmethod
    def _angle_diff(target, current):
        d = (target - current + math.pi) % (2 * math.pi) - math.pi
        return d
```

- [ ] **Step 10.2 — Commit**

```bash
git add games/motodash/bike.py
git commit -m "feat(motodash): rigid-body bike physics"
```

---

### Task 11: Terrain — `terrain.py`

**Files:**
- Create: `games/motodash/terrain.py`

- [ ] **Step 11.1 — Write `games/motodash/terrain.py`**

```python
import bisect
import pygame

import config


class Terrain:
    """Polyligne sol triée par x. Fournit hauteur, pente et rendu."""

    def __init__(self, points, finish_x, checkpoints):
        self.points = list(points)  # [(x, y), ...] trié par x
        self.xs = [p[0] for p in self.points]
        self.finish_x = finish_x
        self.checkpoints = list(checkpoints)

    def _segment_at(self, x):
        """Retourne (x1, y1, x2, y2) du segment qui contient x, ou None."""
        if x < self.xs[0] or x > self.xs[-1]:
            return None
        i = bisect.bisect_right(self.xs, x) - 1
        if i < 0:
            i = 0
        if i + 1 >= len(self.points):
            return None
        x1, y1 = self.points[i]
        x2, y2 = self.points[i + 1]
        return x1, y1, x2, y2

    def height_at(self, x):
        seg = self._segment_at(x)
        if seg is None:
            return None
        x1, y1, x2, y2 = seg
        if x2 == x1:
            return y1
        t = (x - x1) / (x2 - x1)
        return y1 + t * (y2 - y1)

    def slope_at(self, x):
        """Pente dy/dx au point x (positif = descend)."""
        seg = self._segment_at(x)
        if seg is None:
            return 0.0
        x1, y1, x2, y2 = seg
        if x2 == x1:
            return 0.0
        return (y2 - y1) / (x2 - x1)

    def render(self, surface, cam_x, cam_y):
        """Dessine la polyligne + remplissage marron en dessous."""
        sw, sh = surface.get_size()
        # Filtre les points dans la fenêtre visible (avec marges)
        x_min = cam_x - 50
        x_max = cam_x + sw + 50
        screen_pts = []
        for px, py in self.points:
            if x_max < px:
                # encore un point pour fermer la silhouette à droite
                screen_pts.append((px - cam_x, py - cam_y))
                break
            if px < x_min and screen_pts:
                continue
            screen_pts.append((px - cam_x, py - cam_y))

        if len(screen_pts) < 2:
            return

        # Polygone rempli (sol)
        fill = list(screen_pts) + [(screen_pts[-1][0], sh + 40), (screen_pts[0][0], sh + 40)]
        pygame.draw.polygon(surface, config.TERRAIN_COLOR, fill)
        # Ligne de surface
        pygame.draw.lines(surface, config.TERRAIN_LINE, False, screen_pts, 2)

        # Drapeau d'arrivée
        fx = self.finish_x - cam_x
        if -20 <= fx <= sw + 20:
            fy_ground = self.height_at(self.finish_x) or 0
            top = fy_ground - cam_y - 50
            bot = fy_ground - cam_y
            pygame.draw.line(surface, (240, 240, 240), (fx, bot), (fx, top), 2)
            pygame.draw.polygon(
                surface, (220, 60, 60),
                [(fx, top), (fx + 18, top + 6), (fx, top + 12)],
            )
```

- [ ] **Step 11.2 — Commit**

```bash
git add games/motodash/terrain.py
git commit -m "feat(motodash): terrain polyline + collision queries + rendering"
```

---

### Task 12: Game scene — `scene_game.py`

**Files:**
- Create: `games/motodash/scene_game.py`

- [ ] **Step 12.1 — Write `games/motodash/scene_game.py`**

```python
import math
import pygame

import config
from bike import Bike
from terrain import Terrain
import scores
import levels


class GameScene:
    """Une partie sur un niveau donné. Retourne un dict résultat ou None si on quitte."""

    def __init__(self, screen, level_id):
        self.screen = screen
        self.level = levels.get(level_id)
        self.terrain = Terrain(
            self.level["terrain"],
            self.level["finish_x"],
            self.level["checkpoints"],
        )
        self.bike = Bike(self.level["start"])
        self.last_checkpoint = self.level["start"]
        self.passed_checkpoints = set()
        self.elapsed = 0.0
        self.finished = False
        self.crash_timer = 0.0
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)
        # Inputs
        self.input_throttle = False
        self.input_brake = False
        self.input_lean = 0
        self.want_reset = False
        self.want_quit = False

    # ── Inputs ────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.input_throttle = True
            elif event.key == pygame.K_DOWN:
                self.input_brake = True
            elif event.key == pygame.K_LEFT:
                self.input_lean = -1
            elif event.key == pygame.K_RIGHT:
                self.input_lean = 1
            elif event.key == pygame.K_r:
                self.want_reset = True
            elif event.key == pygame.K_ESCAPE:
                self.want_quit = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self.input_throttle = False
            elif event.key == pygame.K_DOWN:
                self.input_brake = False
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.input_lean = 0
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.BTN_THROTTLE:
                self.input_throttle = True
            elif event.button == config.BTN_BRAKE:
                self.input_brake = True
            elif event.button == config.BTN_RESET:
                self.want_reset = True
            elif event.button == config.BTN_LEFT:
                self.input_lean = -1
            elif event.button == config.BTN_RIGHT:
                self.input_lean = 1
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == config.BTN_THROTTLE:
                self.input_throttle = False
            elif event.button == config.BTN_BRAKE:
                self.input_brake = False
            elif event.button in (config.BTN_LEFT, config.BTN_RIGHT):
                self.input_lean = 0
        elif event.type == pygame.JOYHATMOTION:
            x, _ = event.value
            if x < 0:
                self.input_lean = -1
            elif x > 0:
                self.input_lean = 1
            else:
                self.input_lean = 0
        elif event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if event.value < -config.AXIS_DEAD:
                self.input_lean = -1
            elif event.value > config.AXIS_DEAD:
                self.input_lean = 1
            elif abs(event.value) < config.AXIS_DEAD * 0.5:
                self.input_lean = 0

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, dt):
        if self.want_quit:
            return {"quit": True}

        if self.want_reset:
            self.want_reset = False
            self.bike.reset_to(self.last_checkpoint)

        if self.finished:
            return None

        # Crash → courte pause puis téléport au dernier checkpoint
        if self.bike.crashed:
            self.crash_timer += dt
            if self.crash_timer >= 0.6:
                self.bike.reset_to(self.last_checkpoint)
                self.crash_timer = 0.0
        else:
            self.bike.set_inputs(self.input_throttle, self.input_brake, self.input_lean)
            self.bike.step(dt, self.terrain)

        self.elapsed += dt

        # Checkpoints
        for cp_x in self.terrain.checkpoints:
            if cp_x in self.passed_checkpoints:
                continue
            if self.bike.x >= cp_x:
                self.passed_checkpoints.add(cp_x)
                ground_y = self.terrain.height_at(cp_x) or self.bike.y
                self.last_checkpoint = (cp_x, ground_y - 30)

        # Fin
        if self.bike.x >= self.terrain.finish_x:
            self.finished = True
            medal = scores.medal_for_time(self.level, self.elapsed)
            return {
                "finished": True,
                "level_id": self.level["id"],
                "time": self.elapsed,
                "medal": medal,
            }

        # Caméra : suit la moto avec lookahead
        target_x = self.bike.x + max(-80, min(80, self.bike.vx * 0.3)) - self.screen.get_width() / 2
        target_y = self.bike.y - self.screen.get_height() / 2
        self.cam_x += (target_x - self.cam_x) * min(1.0, 8.0 * dt)
        self.cam_y += (target_y - self.cam_y) * min(1.0, 8.0 * dt)

        return None

    # ── Render ────────────────────────────────────────────────────────────
    def render(self):
        self.screen.fill(config.BG_COLOR)
        self.terrain.render(self.screen, self.cam_x, self.cam_y)
        self._render_bike()
        self._render_hud()

    def _render_bike(self):
        cx = self.bike.x - self.cam_x
        cy = self.bike.y - self.cam_y
        cos_a, sin_a = math.cos(self.bike.angle), math.sin(self.bike.angle)
        half = config.WHEELBASE / 2.0
        rear  = (cx - cos_a * half, cy - sin_a * half)
        front = (cx + cos_a * half, cy + sin_a * half)
        # Châssis (segment épais)
        pygame.draw.line(self.screen, config.BIKE_BODY, rear, front, 5)
        # Roues
        pygame.draw.circle(self.screen, config.BIKE_WHEEL, (int(rear[0]),  int(rear[1])),  int(config.WHEEL_RADIUS))
        pygame.draw.circle(self.screen, config.BIKE_WHEEL, (int(front[0]), int(front[1])), int(config.WHEEL_RADIUS))
        # Pilote (stick figure simple) — tête au-dessus du châssis,
        # perpendiculaire à l'axe de la moto.
        head_x = cx - sin_a * 14
        head_y = cy - cos_a * 14
        pygame.draw.circle(self.screen, config.BIKE_RIDER, (int(head_x), int(head_y)), 4)

    def _render_hud(self):
        # Chrono en haut
        mins = int(self.elapsed // 60)
        secs = self.elapsed - mins * 60
        time_str = f"{mins:02d}:{secs:05.2f}"
        surf = self.font.render(time_str, True, config.TEXT_COLOR)
        bg = pygame.Surface((surf.get_width() + 16, surf.get_height() + 8), pygame.SRCALPHA)
        bg.fill(config.HUD_BG)
        self.screen.blit(bg, (8, 8))
        self.screen.blit(surf, (16, 12))
        # Indicateur crash
        if self.bike.crashed:
            msg = self.font.render("CRASH ! reset...", True, (255, 80, 80))
            self.screen.blit(msg, ((self.screen.get_width() - msg.get_width()) // 2, 60))
        # Hint
        hint = self.font_small.render(
            "↑ accel · ↓ frein · ←→ pencher · R reset · Échap menu",
            True, (220, 220, 220),
        )
        self.screen.blit(hint, ((self.screen.get_width() - hint.get_width()) // 2,
                                self.screen.get_height() - hint.get_height() - 6))
```

- [ ] **Step 12.2 — Commit**

```bash
git add games/motodash/scene_game.py
git commit -m "feat(motodash): playable game scene (input, physics, render, HUD)"
```

---

### Task 13: Result scene — `scene_result.py`

**Files:**
- Create: `games/motodash/scene_result.py`

- [ ] **Step 13.1 — Write `games/motodash/scene_result.py`**

```python
import pygame

import config


class ResultScene:
    """Affiche le résultat d'une partie. Renvoie 'retry', 'menu' ou 'quit'."""

    def __init__(self, screen, level, time_seconds, medal, is_new_best):
        self.screen = screen
        self.level = level
        self.time = time_seconds
        self.medal = medal
        self.is_new_best = is_new_best
        self.font_big = pygame.font.SysFont("Arial", 28, bold=True)
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.choice = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_r):
                self.choice = "retry"
            elif event.key == pygame.K_ESCAPE:
                self.choice = "menu"
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.BTN_THROTTLE:
                self.choice = "retry"
            elif event.button == config.BTN_BRAKE:
                self.choice = "menu"

    def update(self, dt):
        if self.choice:
            return {"choice": self.choice}
        return None

    def render(self):
        self.screen.fill((20, 25, 35))
        w, h = self.screen.get_size()

        title = self.font_big.render(self.level["name"], True, config.TEXT_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, 30))

        mins = int(self.time // 60)
        secs = self.time - mins * 60
        time_str = f"{mins:02d}:{secs:05.2f}"
        time_surf = self.font_big.render(time_str, True, config.TEXT_COLOR)
        self.screen.blit(time_surf, ((w - time_surf.get_width()) // 2, 80))

        if self.medal:
            color = config.MEDAL_COLORS[self.medal]
            label = self.medal.upper()
            medal_surf = self.font_big.render(label, True, color)
            self.screen.blit(medal_surf, ((w - medal_surf.get_width()) // 2, 130))
            pygame.draw.circle(self.screen, color, (w // 2, 200), 24)
        else:
            label = self.font.render("Pas de médaille", True, (180, 180, 180))
            self.screen.blit(label, ((w - label.get_width()) // 2, 140))

        if self.is_new_best:
            best = self.font.render("Nouveau meilleur temps !", True, (120, 255, 140))
            self.screen.blit(best, ((w - best.get_width()) // 2, 230))

        hint = self.font_small.render(
            "Entrée/A : recommencer    Échap/B : menu",
            True, (200, 200, 200),
        )
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - 24))
```

- [ ] **Step 13.2 — Commit**

```bash
git add games/motodash/scene_result.py
git commit -m "feat(motodash): result scene (time, medal, retry/menu)"
```

---

### Task 14: Main entry — `main.py`

**Why:** Wires init, splash, and the scene state machine: `select → game → result → select` (or `game` directly on retry). At this point with only `easy` defined, the menu is minimal but the loop is complete.

**Files:**
- Create: `games/motodash/main.py`

- [ ] **Step 14.1 — Write `games/motodash/main.py`**

```python
import sys
import pygame

import config
import scores as scores_io
import levels


def _ensure_pygame():
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if not pygame.joystick.get_init():
        pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        try:
            pygame.joystick.Joystick(i).init()
        except Exception:
            pass


def _make_screen():
    surf = pygame.display.get_surface()
    if surf is None or surf.get_size() != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
        surf = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Motodash")
    return surf


def _splash(screen):
    font = pygame.font.SysFont("Arial", 36, bold=True)
    sub = pygame.font.SysFont("Arial", 14)
    title = font.render("MOTODASH", True, (250, 220, 90))
    s = sub.render("BETA — Trials 2D", True, (200, 200, 200))
    for _ in range(60):  # ~1s à 60 fps
        screen.fill((15, 18, 24))
        w, h = screen.get_size()
        screen.blit(title, ((w - title.get_width()) // 2, h // 2 - 30))
        screen.blit(s, ((w - s.get_width()) // 2, h // 2 + 10))
        pygame.display.flip()
        pygame.time.delay(16)


def _run_game(screen, level_id, scores_state):
    from scene_game import GameScene
    from scene_result import ResultScene

    while True:
        scene = GameScene(screen, level_id)
        clock = pygame.time.Clock()
        result = None
        while result is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                scene.handle_event(event)
            result = scene.update(dt)
            scene.render()
            pygame.display.flip()

        if result.get("quit"):
            return "menu"
        if not result.get("finished"):
            return "menu"

        # Save best time
        is_new_best = scores_io.record_time(
            scores_state, result["level_id"], result["time"], result["medal"],
        )
        if is_new_best:
            scores_io.save(scores_state)

        level = levels.get(level_id)
        rscene = ResultScene(
            screen, level, result["time"], result["medal"], is_new_best,
        )
        rresult = None
        while rresult is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                rscene.handle_event(event)
            rresult = rscene.update(dt)
            rscene.render()
            pygame.display.flip()
        if rresult["choice"] == "retry":
            continue
        return "menu"


def main():
    _ensure_pygame()
    screen = _make_screen()
    _splash(screen)
    scores_state = scores_io.load()

    # Tant qu'on n'a pas de scene_select, on lance directement easy.
    # Remplacé par la boucle menu en Task 15.
    state = _run_game(screen, "easy", scores_state)
    return


if __name__ == "__main__":
    main()
    sys.exit(0)
```

- [ ] **Step 14.2 — Run motodash from PC, on `easy` level**

```bash
cd /home/clement/Documents/projets/POC/pokedex
python main.py
# In launcher: press F4 to reveal beta, navigate to Motodash, hit Enter
```

Expected:
- Splash screen appears for ~1 second.
- Game starts on level easy.
- Arrow keys move the bike. Up = throttle, left/right = lean, R = reset.
- The bike rolls along the terrain, falls correctly, can crash by leaning past 110°.
- Reaching `finish_x = 1800` shows the result screen with time and medal.
- Enter retries, Échap returns. (Right now Échap exits motodash entirely since there's no select screen.)

If the physics feel completely wrong (instantly tips over, no gravity, bike floats), tune values in `config.py` (most likely culprits: `THROTTLE_FORCE`, `LEAN_TORQUE`, `SUSPENSION_K`). Don't aim for perfect — aim for "playable enough to validate the loop".

- [ ] **Step 14.3 — Commit**

```bash
git add games/motodash/main.py
git commit -m "feat(motodash): main entry — splash + game loop on easy level"
```

---

### Task 15: Level select scene — `scene_select.py`

**Files:**
- Create: `games/motodash/scene_select.py`
- Modify: `games/motodash/main.py`

- [ ] **Step 15.1 — Write `games/motodash/scene_select.py`**

```python
import pygame

import config
import levels
import scores as scores_io


class SelectScene:
    """Menu de sélection de niveau. Renvoie un level_id ou 'quit'."""

    def __init__(self, screen, scores_state):
        self.screen = screen
        self.scores_state = scores_state
        self.selected = 0
        self.font_big = pygame.font.SysFont("Arial", 22, bold=True)
        self.font = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 11)
        self._axis_moved = False
        self.choice = None

    def handle_event(self, event):
        n = len(levels.LEVELS)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % n
            elif event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_n):
                self.choice = levels.LEVELS[self.selected]["id"]
            elif event.key == pygame.K_ESCAPE:
                self.choice = "quit"
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button in (config.BTN_THROTTLE,):  # A
                self.choice = levels.LEVELS[self.selected]["id"]
            elif event.button == config.BTN_BRAKE:  # B
                self.choice = "quit"
            elif event.button == config.BTN_LEFT:
                self.selected = (self.selected - 1) % n
            elif event.button == config.BTN_RIGHT:
                self.selected = (self.selected + 1) % n
        elif event.type == pygame.JOYHATMOTION:
            x, _ = event.value
            if x < 0:
                self.selected = (self.selected - 1) % n
            elif x > 0:
                self.selected = (self.selected + 1) % n
        elif event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if event.value < -0.7 and not self._axis_moved:
                self.selected = (self.selected - 1) % n
                self._axis_moved = True
            elif event.value > 0.7 and not self._axis_moved:
                self.selected = (self.selected + 1) % n
                self._axis_moved = True
            elif abs(event.value) < 0.3:
                self._axis_moved = False

    def update(self, dt):
        if self.choice:
            return {"choice": self.choice}
        return None

    def render(self):
        self.screen.fill((22, 26, 36))
        w, h = self.screen.get_size()
        title = self.font_big.render("MOTODASH — Sélection du niveau", True, config.TEXT_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, 24))

        n = len(levels.LEVELS)
        tile_w, tile_h = 130, 160
        gap = 16
        total_w = n * tile_w + (n - 1) * gap
        x0 = (w - total_w) // 2
        y0 = 80

        for i, level in enumerate(levels.LEVELS):
            x = x0 + i * (tile_w + gap)
            rect = pygame.Rect(x, y0, tile_w, tile_h)
            sel = i == self.selected
            color = (50, 60, 75) if sel else (35, 40, 50)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            border_color = (220, 220, 220) if sel else (90, 90, 100)
            pygame.draw.rect(self.screen, border_color, rect, 2 if sel else 1, border_radius=8)

            name = self.font.render(level["name"], True, config.TEXT_COLOR)
            self.screen.blit(name, (x + (tile_w - name.get_width()) // 2, y0 + 14))

            best = self.scores_state.get("best_times", {}).get(level["id"])
            if best:
                mins = int(best["time"] // 60)
                secs = best["time"] - mins * 60
                time_str = f"{mins:02d}:{secs:05.2f}"
                t = self.font.render(time_str, True, (220, 220, 220))
                self.screen.blit(t, (x + (tile_w - t.get_width()) // 2, y0 + 44))
                medal = best.get("medal")
                if medal:
                    mcolor = config.MEDAL_COLORS[medal]
                    pygame.draw.circle(self.screen, mcolor, (x + tile_w // 2, y0 + 90), 18)
            else:
                dash = self.font.render("—", True, (140, 140, 140))
                self.screen.blit(dash, (x + (tile_w - dash.get_width()) // 2, y0 + 60))

            # Targets
            targets = self.font_small.render(
                f"or {level['gold']:.0f}s · arg {level['silver']:.0f}s · br {level['bronze']:.0f}s",
                True, (170, 170, 170),
            )
            self.screen.blit(targets, (x + (tile_w - targets.get_width()) // 2, y0 + tile_h - 20))

        hint = self.font_small.render(
            "←→ choisir · A/Entrée jouer · B/Échap quitter",
            True, (200, 200, 200),
        )
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - 24))
```

- [ ] **Step 15.2 — Wire the select scene into `main.py`**

In `games/motodash/main.py`, replace the `main()` function body's last lines:

```python
def main():
    _ensure_pygame()
    screen = _make_screen()
    _splash(screen)
    scores_state = scores_io.load()

    while True:
        from scene_select import SelectScene
        select = SelectScene(screen, scores_state)
        clock = pygame.time.Clock()
        result = None
        while result is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                select.handle_event(event)
            result = select.update(dt)
            select.render()
            pygame.display.flip()

        if result["choice"] == "quit":
            return
        _run_game(screen, result["choice"], scores_state)
```

- [ ] **Step 15.3 — Run motodash, verify select → game → result → select loop**

```bash
python main.py
# F4 to reveal beta, launch Motodash
```

Expected: select screen shows 1 level (easy), Enter starts it, finishing returns to select. Échap from select quits motodash and returns to launcher.

- [ ] **Step 15.4 — Commit**

```bash
git add games/motodash/main.py games/motodash/scene_select.py
git commit -m "feat(motodash): level select scene + full state machine"
```

---

### Task 16: Add medium and hard levels

**Files:**
- Modify: `games/motodash/levels.py`

- [ ] **Step 16.1 — Append medium and hard to `LEVELS`**

In `games/motodash/levels.py`, replace the `LEVELS` list with:

```python
LEVELS = [
    {
        "id": "easy",
        "name": "Premiers tours",
        "terrain": [
            (-200, 240),
            (0, 240),
            (200, 240),
            (300, 230),
            (400, 240),
            (500, 240),
            (650, 220),
            (800, 240),
            (950, 250),
            (1100, 235),
            (1250, 245),
            (1400, 240),
            (1550, 220),
            (1700, 240),
            (1850, 240),
            (2050, 240),
        ],
        "start": (50, 200),
        "finish_x": 1800,
        "checkpoints": [600, 1200],
        "gold":   25.0,
        "silver": 35.0,
        "bronze": 50.0,
    },
    {
        "id": "medium",
        "name": "Collines",
        "terrain": [
            (-200, 240),
            (0, 240),
            (150, 230),
            (300, 260),
            (450, 200),    # bosse plus marquée
            (600, 250),
            (750, 220),
            (900, 270),
            (1050, 200),
            (1200, 240),
            (1400, 210),   # rampe
            (1550, 260),
            (1700, 230),
            (1900, 240),
            (2100, 240),
        ],
        "start": (50, 200),
        "finish_x": 1850,
        "checkpoints": [500, 1000, 1500],
        "gold":   35.0,
        "silver": 50.0,
        "bronze": 70.0,
    },
    {
        "id": "hard",
        "name": "Falaise",
        "terrain": [
            (-200, 240),
            (0, 240),
            (200, 220),
            (350, 260),
            (500, 180),    # gros saut
            (650, 280),
            (800, 200),
            (950, 290),    # creux
            (1100, 180),   # remontée
            (1250, 250),
            (1400, 190),
            (1600, 260),
            (1800, 220),
            (2000, 240),
            (2200, 240),
        ],
        "start": (50, 200),
        "finish_x": 1950,
        "checkpoints": [400, 900, 1400],
        "gold":   45.0,
        "silver": 65.0,
        "bronze": 90.0,
    },
]
```

- [ ] **Step 16.2 — Run motodash, verify select shows 3 levels and each plays through**

```bash
python main.py
# F4, Motodash, navigate left/right between 3 tiles, finish each at least once
```

- [ ] **Step 16.3 — Commit**

```bash
git add games/motodash/levels.py
git commit -m "feat(motodash): add medium and hard levels"
```

---

### Task 17: Procedural cover image + CLAUDE.md doc

**Files:**
- Create: `games/motodash/cover.png`
- Create: `games/motodash/CLAUDE.md`

- [ ] **Step 17.1 — Generate `cover.png` procedurally**

Run from project root:

```bash
cd /home/clement/Documents/projets/POC/pokedex
python -c "
import pygame, math
pygame.init()
W, H = 480, 320
surf = pygame.Surface((W, H))
# Sky gradient
for y in range(H):
    t = y / H
    r = int(135 + (255 - 135) * t * 0.4)
    g = int(180 + (220 - 180) * t * 0.4)
    b = int(220 + (180 - 220) * t * 0.4)
    pygame.draw.line(surf, (r, g, b), (0, y), (W, y))
# Hills
pts = [(0, 230)]
for x in range(0, W + 20, 20):
    pts.append((x, int(220 + 30 * math.sin(x * 0.04))))
pts.append((W, H)); pts.append((0, H))
pygame.draw.polygon(surf, (95, 75, 55), pts)
# Bike silhouette
pygame.draw.circle(surf, (25, 25, 25), (220, 200), 18)
pygame.draw.circle(surf, (25, 25, 25), (280, 200), 18)
pygame.draw.line(surf, (200, 50, 40), (220, 200), (280, 200), 8)
pygame.draw.circle(surf, (235, 200, 165), (250, 165), 10)
# Title
font = pygame.font.SysFont('Arial', 60, bold=True)
title = font.render('MOTODASH', True, (250, 220, 90))
surf.blit(title, ((W - title.get_width()) // 2, 50))
sub = pygame.font.SysFont('Arial', 18).render('BETA – Trials 2D', True, (40, 40, 40))
surf.blit(sub, ((W - sub.get_width()) // 2, 110))
pygame.image.save(surf, 'games/motodash/cover.png')
print('cover.png generated')
"
```

Expected: prints `cover.png generated`. Verify file exists at `games/motodash/cover.png`.

- [ ] **Step 17.2 — Write `games/motodash/CLAUDE.md`**

```markdown
# Motodash

Trials 2D solo (BETA). Pilote une moto sur 3 niveaux fixes, chrono + médailles or/argent/bronze.

## Structure

```
main.py            – Splash, init pygame, state machine select → game → result
config.py          – Constantes (écran, physique, contrôles, médailles)
levels.py          – 3 niveaux fixes (terrain polyligne, départ, arrivée, checkpoints, temps cibles)
scores.py          – I/O JSON ~/.config/pokedex/motodash.json
bike.py            – Corps rigide + intégration Euler semi-implicite
terrain.py         – Polyligne sol, hauteur/pente par x, rendu polygone
scene_select.py    – Menu : 3 tuiles, meilleur temps + médaille par niveau
scene_game.py      – Boucle de jeu : input → physique → rendu, HUD chrono
scene_result.py    – Écran fin : temps, médaille, retry/menu
```

## Physique

- Moto = un seul corps rigide. Roues = positions dérivées de (pos, angle).
- Intégration Euler semi-implicite à 60 FPS.
- Collisions par roue contre la polyligne du terrain (binary search sur les x).
- Crash si l'inclinaison dépasse ±110° → reset au dernier checkpoint passé après 0.6s.

## Contrôles

- J1 : A=accélérer · B=frein · D-pad/hat=pencher · X=reset · combo SELECT+START 3s=quitter
- Clavier : ↑=accélérer · ↓=frein · ←→=pencher · R=reset · Échap=quitter
```

- [ ] **Step 17.3 — Run launcher one last time, verify motodash tile shows the cover image**

```bash
python main.py
# F4 to reveal beta. Motodash tile should show the generated cover.
```

- [ ] **Step 17.4 — Commit**

```bash
git add games/motodash/cover.png games/motodash/CLAUDE.md
git commit -m "feat(motodash): cover art + CLAUDE.md"
```

---

## Final Validation

- [ ] **Run full launcher loop, default mode (no F4)**
  - Only 5 stable games visible.
  - Each launches and returns to launcher.

- [ ] **Run launcher with F4 toggled**
  - 7 games visible, DOOM and Motodash have BETA badges.
  - Motodash launches, all 3 levels play, medals are awarded correctly, best times persist across runs (re-launch → check select shows times).

- [ ] **Smoke-test corrupt scores file**
  ```bash
  echo "garbage" > ~/.config/pokedex/motodash.json
  python main.py
  # F4, Motodash → should still load (logs warning, fresh state)
  ```

If all pass, the work is done.
