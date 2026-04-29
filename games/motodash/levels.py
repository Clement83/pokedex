"""Niveaux Motodash : 5 biomes × 3 niveaux = 15 parcours.

Chaque biome a son générateur procédural de terrain + hazards :
- grass   : collines roulantes, rondins, mares de boue
- desert  : longues dunes, sables mouvants (mort), cactus
- canyon  : drops verticaux, mesas, river de mort au fond, chutes de pierres, updrafts
- ice     : longs plats, crevasses (mort), plaques de verglas
- volcano : pics chaotiques, lave (mort), geysers, braises tombantes

La difficulté monte : grass tuto → volcano boss final.
3 niveaux par biome scalent en longueur + densité de hazards.
"""

import math
import random


# ── Définition des niveaux (légère, terrain et hazards générés à la demande) ───

LEVELS_DEF = [
    # GRASS (tuto, 25-45 s)
    {"id": "grass_1",  "name": "Pré vert",   "biome": "grass",   "length":  6000, "seed": 11, "density": 0.8},
    {"id": "grass_2",  "name": "Collines",   "biome": "grass",   "length":  8000, "seed": 12, "density": 1.0},
    {"id": "grass_3",  "name": "Vallon",     "biome": "grass",   "length": 10000, "seed": 13, "density": 1.2},
    # DESERT (facile+, 30-55 s)
    {"id": "desert_1", "name": "Oasis",      "biome": "desert",  "length":  7500, "seed": 21, "density": 0.9},
    {"id": "desert_2", "name": "Mirage",     "biome": "desert",  "length": 10000, "seed": 22, "density": 1.1},
    {"id": "desert_3", "name": "Dunes",      "biome": "desert",  "length": 12500, "seed": 23, "density": 1.3},
    # CANYON (medium, 35-65 s)
    {"id": "canyon_1", "name": "Falaise",    "biome": "canyon",  "length":  9000, "seed": 31, "density": 0.9},
    {"id": "canyon_2", "name": "Méandres",   "biome": "canyon",  "length": 12000, "seed": 32, "density": 1.1},
    {"id": "canyon_3", "name": "Rampage",    "biome": "canyon",  "length": 15000, "seed": 33, "density": 1.4},
    # ICE (hard, 40-75 s)
    {"id": "ice_1",    "name": "Banquise",   "biome": "ice",     "length": 10500, "seed": 41, "density": 1.0},
    {"id": "ice_2",    "name": "Glacier",    "biome": "ice",     "length": 13500, "seed": 42, "density": 1.2},
    {"id": "ice_3",    "name": "Crevasses",  "biome": "ice",     "length": 16500, "seed": 43, "density": 1.5},
    # VOLCANO (extreme, 50-90 s)
    {"id": "volcano_1","name": "Cratère",    "biome": "volcano", "length": 12000, "seed": 51, "density": 1.0},
    {"id": "volcano_2","name": "Coulée",     "biome": "volcano", "length": 15000, "seed": 52, "density": 1.3},
    {"id": "volcano_3","name": "Inferno",    "biome": "volcano", "length": 18000, "seed": 53, "density": 1.6},
]


# ── Générateurs de terrain par biome ─────────────────────────────────────────

BASE_Y = 240  # niveau de référence du sol


def _gen_grass(length, seed, density):
    """Collines roulantes paisibles. Hazards : mares de boue (slow_zone, jamais crash)."""
    rng = random.Random(seed)
    pts = [(-200, BASE_Y), (0, BASE_Y)]
    hazards = []
    x = 0
    base = BASE_Y
    while x < length:
        roll = rng.random()
        if roll < 0.55:
            # Colline roulante (sinusoïde)
            amp = rng.randint(8, 22)
            wavelen = rng.randint(120, 200)
            steps = rng.randint(4, 6)
            for i in range(1, steps + 1):
                x += wavelen // steps
                t = i / steps
                y = base - amp * math.sin(t * math.pi)
                pts.append((x, y))
        elif roll < 0.80:
            # Long plat avec mare de boue optionnelle (slow_zone uniquement)
            flat_len = rng.randint(220, 320)
            x_start = x
            x = x_start + flat_len
            pts.append((x, base))
            if rng.random() < 0.6 * density:
                mx = x_start + rng.randint(40, max(50, flat_len - 80))
                mw = rng.randint(40, 90)
                hazards.append({"kind": "slow_zone", "rect": (mx, base, mw, 6), "mult": 0.55})
        else:
            # Double bosse
            for offsets in ((30, -14), (60, 0), (90, -10), (120, 0)):
                ox, dy = offsets
                pts.append((x + ox, base + dy))
            x += 130
    pts.append((length, base))
    pts.append((length + 200, base))
    return pts, hazards


def _gen_desert(length, seed, density):
    """Longues dunes ondulées + creux. Hazard naturel : sables mouvants au fond du creux (kill_zone)."""
    rng = random.Random(seed)
    pts = [(-200, BASE_Y), (0, BASE_Y)]
    hazards = []
    x = 0
    base = BASE_Y
    while x < length:
        roll = rng.random()
        if roll < 0.5:
            # Dune sinusoïdale longue
            amp = rng.randint(15, 32)
            wavelen = rng.randint(200, 320)
            steps = rng.randint(6, 9)
            for i in range(1, steps + 1):
                x += wavelen // steps
                t = i / steps
                y = base - amp * math.sin(t * math.pi)
                pts.append((x, y))
        elif roll < 0.85:
            # Plat très long (signature desert) — sans obstacle crashant, juste du désert ouvert
            flat_len = rng.randint(260, 480)
            x += flat_len
            pts.append((x, base))
        else:
            # Creux à sables mouvants : kicker (signal + tremplin) puis pit profond.
            # Quicksand fatale couvrant tout l'intérieur — il faut sauter par-dessus.
            run_in = rng.randint(30, 50)
            x += run_in
            pts.append((x, base))
            ramp_w = rng.randint(45, 65)
            ramp_h = rng.randint(24, 36)
            x += ramp_w
            pts.append((x, base - ramp_h))  # sommet du kicker = bord du pit
            x_left = x
            pit_w = rng.randint(80, 120)
            depth = rng.randint(40, 65)
            pts.append((x + 6, base + depth))
            pts.append((x + pit_w - 6, base + depth))
            x += pit_w
            pts.append((x, base))
            hazards.append({"kind": "kill_zone", "subkind": "quicksand",
                            "rect": (x_left + 8, base + 4, pit_w - 14, depth + 6)})
    pts.append((length, base))
    pts.append((length + 200, base))
    return pts, hazards


def _gen_canyon(length, seed, density):
    """Drops verticaux + mesas + cassures profondes. Hauteurs scalent avec la densité (Rampage = imposant).
    Hazards : river au fond (mort), chutes de pierres, updrafts. Cassures non-mortelles."""
    rng = random.Random(seed)
    pts = [(-200, BASE_Y), (0, BASE_Y)]
    hazards = []
    # River de mort en bas du canyon : seul un vrai vol plané vers le vide tue
    Y_RIVER = 420
    hazards.append({"kind": "kill_floor", "y": Y_RIVER})
    # Bandeau visuel pour la rivière (rect au fond, sous la zone de jeu)
    hazards.append({
        "kind": "kill_zone", "subkind": "river",
        "rect": (-200, Y_RIVER, length + 400, 60),
    })
    # Échelle verticale par densité : canyon_1 (0.9) → 1.15, canyon_3 (1.4) → 1.4
    h_scale = 0.7 + density * 0.5
    x = 0
    base = BASE_Y
    while x < length:
        roll = rng.random()
        if roll < 0.35:
            # Mesa : montée raide → plateau plat → chute raide
            climb = int(rng.uniform(60, 130) * h_scale)
            climb_len = rng.randint(80, 140)
            plateau_len = rng.randint(180, 320)
            drop_len = rng.randint(80, 140)
            base_top = base - climb
            for i in range(1, 5):
                x += climb_len // 4
                pts.append((x, base - climb * i / 4))
            mesa_start = x
            x += plateau_len
            pts.append((x, base_top))
            # Chutes de pierres sur le plateau
            if rng.random() < 0.55 * density:
                rx = mesa_start + rng.randint(30, max(35, plateau_len - 30))
                hazards.append({
                    "kind": "falling_rock", "x": rx,
                    "period": rng.uniform(2.6, 3.6),
                    "phase": rng.uniform(0.0, 2.0),
                    "fall_duration": 1.5,
                    "top_y": base_top - 80,
                    "ground_y": base_top + 6,
                })
            # Drop
            for i in range(1, 5):
                x += drop_len // 4
                pts.append((x, base_top + climb * i / 4))
        elif roll < 0.60:
            # Gap (vide) — la moto saute par-dessus le canyon
            run_in = rng.randint(40, 90)
            x += run_in
            pts.append((x, base))
            ramp = rng.randint(30, 50)
            x += ramp
            pts.append((x, base - 18))  # tremplin
            gap_w = rng.randint(140, 240)
            land_dy = rng.randint(-30, 40)  # variabilité d'atterrissage
            x_landing = x + gap_w
            # Clamp pour rester au-dessus de la rivière (kill_floor à 420)
            base = max(BASE_Y - 60, min(BASE_Y + 50, base + land_dy))
            pts.append((x_landing, base))
            x = x_landing
            # Updraft optionnel dans le gap (aide ou perturbe)
            if rng.random() < 0.4 * density:
                hazards.append({
                    "kind": "updraft",
                    "rect": (x_landing - gap_w + 30, base - 130, gap_w - 60, 130),
                    "force": rng.uniform(160.0, 280.0),
                })
        elif roll < 0.85:
            # Cassure spectaculaire : montée vers pic → drop vertical → fond non-mortel → remontée
            run_in = rng.randint(30, 60)
            x += run_in
            pts.append((x, base))
            ramp_w = rng.randint(70, 110)
            ramp_h = int(rng.uniform(70, 120) * h_scale)
            for i in range(1, 5):
                x += ramp_w // 4
                pts.append((x, base - ramp_h * i / 4))
            x_left = x
            gap_w = rng.randint(110, 170)
            crack_depth = int(rng.uniform(60, 110) * h_scale)
            # Drop quasi-vertical depuis le pic
            pts.append((x + 8, base + crack_depth))
            pts.append((x + gap_w - 8, base + crack_depth))
            x += gap_w
            pts.append((x, base))  # remontée à la base de l'autre côté
            # Pas de kill_zone : la cassure est visible et impressionnante mais
            # survivable (seul kill_floor à y=420 reste mortel si on coule au fond)
        else:
            # Vallon descendant + remontée (modéré, sans plonger dans la rivière)
            for offsets in ((50, 18), (100, 30), (150, 30), (200, 18), (260, 0)):
                ox, dy = offsets
                pts.append((x + ox, base + dy))
            x += 280
    pts.append((length, base))
    pts.append((length + 200, base))
    return pts, hazards


def _gen_ice(length, seed, density):
    """Plats étendus + crevasses (mort) + plaques de verglas. Climbs raides occasionnels."""
    rng = random.Random(seed)
    pts = [(-200, BASE_Y), (0, BASE_Y)]
    hazards = []
    x = 0
    base = BASE_Y
    while x < length:
        roll = rng.random()
        if roll < 0.45:
            # Long plat avec verglas et possibilité de crevasse
            flat_len = rng.randint(220, 380)
            x_start = x
            x += flat_len
            pts.append((x, base))
            # Plaque de verglas (secondary hazard)
            if rng.random() < 0.55 * density:
                ipx = x_start + rng.randint(30, max(35, flat_len - 80))
                ipw = rng.randint(60, 130)
                hazards.append({"kind": "ice_patch",
                                "rect": (ipx, base - 1, ipw, 8)})
        elif roll < 0.75:
            # Crevasse : congère ascendante (signal visuel + tremplin naturel) puis le gap
            run_in = rng.randint(30, 60)
            x += run_in
            pts.append((x, base))
            ramp_w = rng.randint(40, 60)
            ramp_h = rng.randint(20, 32)
            x += ramp_w
            pts.append((x, base - ramp_h))  # sommet de la congère = bord du gap
            x_left = x
            gap_w = rng.randint(100, 180)
            depth = rng.randint(70, 120)
            # Drop quasi-vertical depuis la congère
            pts.append((x + 6, base + depth))
            pts.append((x + gap_w - 6, base + depth))
            x += gap_w
            pts.append((x, base))  # remontée à la base de l'autre côté
            hazards.append({
                "kind": "kill_zone", "subkind": "crevasse",
                "rect": (x_left + 8, base + depth - 6, gap_w - 14, max(20, depth)),
            })
        else:
            # Climb raide + descente glacée
            for offsets in ((60, -30), (120, -55), (180, -75), (240, -75), (320, -55), (400, -30), (470, 0)):
                ox, dy = offsets
                pts.append((x + ox, base + dy))
            x += 470
    pts.append((length, base))
    pts.append((length + 200, base))
    return pts, hazards


def _gen_volcano(length, seed, density):
    """Pics chaotiques + V-pits avec lave (mort) + geysers + braises tombantes."""
    rng = random.Random(seed)
    pts = [(-200, BASE_Y), (0, BASE_Y)]
    hazards = []
    x = 0
    base = BASE_Y
    while x < length:
        roll = rng.random()
        if roll < 0.40:
            # Cratère volcanique : montée segmentée → sommet avec lac de lave → descente segmentée
            run_in = rng.randint(30, 60)
            x += run_in
            pts.append((x, base))
            climb_w = rng.randint(100, 160)
            peak_h = rng.randint(60, 90)
            # Montée par 4 segments pour adoucir la pente
            for i in range(1, 5):
                x += climb_w // 4
                pts.append((x, base - peak_h * i / 4))
            x_left = x + 4
            crater_w = rng.randint(70, 100)
            crater_depth = rng.randint(28, 45)
            pts.append((x + 4, base - peak_h + crater_depth))  # paroi gauche
            pts.append((x + 4 + crater_w - 8, base - peak_h + crater_depth))  # fond
            x += crater_w
            pts.append((x, base - peak_h))  # bord droit du cratère
            descent_w = rng.randint(100, 160)
            # Descente par 4 segments
            for i in range(1, 5):
                x += descent_w // 4
                pts.append((x, base - peak_h + peak_h * i / 4))
            # Lac de lave dans le cratère : rect couvre tout l'intérieur (du rim au fond),
            # toute moto qui entre meurt — même si elle saute le cratère
            hazards.append({
                "kind": "kill_zone", "subkind": "lava",
                "rect": (x_left, base - peak_h, crater_w - 8, crater_depth + 6),
            })
        elif roll < 0.70:
            # Pic acéré segmenté (sommet + redescente smoothes)
            climb_w = rng.randint(80, 120)
            descent_w = rng.randint(80, 120)
            peak_h = rng.randint(40, 80)
            for i in range(1, 5):
                x += climb_w // 4
                pts.append((x, base - peak_h * i / 4))
            peak_x = x
            for i in range(1, 5):
                x += descent_w // 4
                pts.append((x, base - peak_h + peak_h * i / 4))
            # Geyser sur le pic ?
            if rng.random() < 0.45 * density:
                hazards.append({
                    "kind": "geyser", "x": peak_x,
                    "ground_y": base - peak_h,
                    "period": rng.uniform(3.5, 5.0),
                    "phase": rng.uniform(0.0, 2.5),
                    "active_duration": 0.9,
                    "height": rng.randint(70, 110),
                    "force": rng.uniform(450.0, 700.0),
                })
        else:
            # Plateau fragmenté avec petites bosses
            for offsets in ((40, -10), (80, 0), (120, -16), (170, -8), (220, 0)):
                ox, dy = offsets
                pts.append((x + ox, base + dy))
            x += 240
            # Braises tombantes (1-2)
            n_emb = rng.choice([0, 1, 1, 2]) if density >= 1.0 else rng.choice([0, 0, 1])
            for _ in range(n_emb):
                fx = x - rng.randint(40, 200)
                hazards.append({
                    "kind": "falling_rock", "x": fx,
                    "period": rng.uniform(2.2, 3.2),
                    "phase": rng.uniform(0.0, 2.0),
                    "fall_duration": 1.4,
                    "top_y": base - 100,
                    "ground_y": base + 10,
                })
    pts.append((length, base))
    pts.append((length + 200, base))
    return pts, hazards


_GENERATORS = {
    "grass":   _gen_grass,
    "desert":  _gen_desert,
    "canyon":  _gen_canyon,
    "ice":     _gen_ice,
    "volcano": _gen_volcano,
}


# ── Médailles par niveau (calibrées par bot test, voir calibrate_medals.py) ──

MEDALS = {
    "grass_1":   (19.0, 24.0, 30.6),
    "grass_2":   (22.2, 28.0, 35.8),
    "grass_3":   (24.5, 30.9, 39.4),
    "desert_1":  (19.4, 24.4, 31.1),
    "desert_2":  (22.7, 28.6, 36.5),
    "desert_3":  (29.9, 37.7, 48.2),
    "canyon_1":  (55.3, 69.8, 89.0),
    "canyon_2":  (67.8, 85.5, 109.0),
    "canyon_3":  (82.9, 104.5, 133.4),
    "ice_1":     (26.7, 33.6, 42.9),
    "ice_2":     (37.7, 47.6, 60.7),
    "ice_3":     (43.2, 54.5, 69.5),
    "volcano_1": (60.5, 76.3, 97.4),
    "volcano_2": (61.1, 77.1, 98.3),
    "volcano_3": (88.6, 111.8, 142.6),
}


# ── API publique ─────────────────────────────────────────────────────────────

def _terrain_height_at(pts, x):
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        if x0 <= x <= x1 and x1 > x0:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return BASE_Y


def _safe_checkpoint_x(cp_x, terrain_pts, hazards):
    """Décale le checkpoint en arrière s'il atterrit sur un kill_zone (sol ou spawn dans le rect)."""
    for _ in range(40):
        ground_y = _terrain_height_at(terrain_pts, cp_x)
        spawn_y = ground_y - 30
        unsafe = None
        for h in hazards:
            if h.get("kind") != "kill_zone":
                continue
            rx, ry, rw, rh = h["rect"]
            if not (rx <= cp_x <= rx + rw):
                continue
            if (ry <= ground_y <= ry + rh) or (ry <= spawn_y <= ry + rh):
                unsafe = (rx, ry, rw, rh)
                break
        if unsafe is None:
            return cp_x
        cp_x = max(50, int(unsafe[0]) - 60)
    return cp_x


def _build_level(d):
    gen = _GENERATORS[d["biome"]]
    terrain, hazards = gen(d["length"], d["seed"], d["density"])
    n_cp = max(3, d["length"] // 1800)
    raw_cps = [int(d["length"] * (i + 1) / (n_cp + 1)) for i in range(n_cp)]
    cps = []
    for raw in raw_cps:
        safe = _safe_checkpoint_x(raw, terrain, hazards)
        if cps and safe <= cps[-1]:
            # Si le shift remonte avant le précédent cp, on saute (cp redondant)
            continue
        cps.append(safe)
    g, s, b = MEDALS.get(d["id"], (30.0, 45.0, 60.0))
    return {
        "id":          d["id"],
        "name":        d["name"],
        "biome":       d["biome"],
        "terrain":     terrain,
        "hazards":     hazards,
        "start":       (50, 200),
        "finish_x":    d["length"] - 200,
        "checkpoints": cps,
        "gold":        g,
        "silver":      s,
        "bronze":      b,
    }


# Lazy : on ne génère que ce qui est demandé (et on cache)
_CACHE = {}

LEVELS = []
for _d in LEVELS_DEF:
    # On expose une vue "stub" sans terrain (le menu n'en a pas besoin)
    LEVELS.append({
        "id":     _d["id"],
        "name":   _d["name"],
        "biome":  _d["biome"],
        "gold":   MEDALS.get(_d["id"], (30, 45, 60))[0],
        "silver": MEDALS.get(_d["id"], (30, 45, 60))[1],
        "bronze": MEDALS.get(_d["id"], (30, 45, 60))[2],
    })


def get(level_id):
    if level_id in _CACHE:
        return _CACHE[level_id]
    for d in LEVELS_DEF:
        if d["id"] == level_id:
            built = _build_level(d)
            _CACHE[level_id] = built
            return built
    raise KeyError(f"Unknown level: {level_id}")
