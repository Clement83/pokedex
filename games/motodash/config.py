SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 60

BG_COLOR      = (135, 180, 220)
SKY_TOP       = (95, 145, 200)
SKY_BOTTOM    = (215, 225, 215)
MOUNTAIN_FAR  = (110, 120, 145)
MOUNTAIN_MID  = (85, 100, 125)
HILL_NEAR     = (62, 90, 70)
CLOUD_COLOR   = (250, 250, 250, 180)

TERRAIN_GRASS = (90, 145, 60)
TERRAIN_GRASS_DARK = (60, 110, 45)
TERRAIN_DIRT  = (110, 80, 55)
TERRAIN_DIRT_DARK = (75, 55, 35)
TERRAIN_LINE  = (40, 30, 20)

BIKE_FRAME    = (185, 40, 35)
BIKE_FRAME_DARK = (115, 25, 20)
BIKE_TIRE     = (28, 28, 32)
BIKE_RIM      = (180, 180, 190)
BIKE_HUB      = (90, 90, 100)
BIKE_FORK     = (200, 200, 210)
RIDER_HELMET  = (40, 45, 60)
RIDER_VISOR   = (95, 175, 215)
RIDER_SUIT    = (35, 65, 110)
RIDER_GLOVE   = (25, 25, 28)
RIDER_SKIN    = (235, 200, 165)

TEXT_COLOR    = (245, 245, 245)
HUD_BG        = (0, 0, 0, 140)

BIOMES = {
    "grass": {
        "sky_top":      (95, 145, 200),
        "sky_bottom":   (215, 225, 215),
        "sun":          (255, 245, 200),
        "sun_inner":    (255, 230, 170),
        "cloud":        (250, 250, 250, 180),
        "mountain_far": (110, 120, 145),
        "mountain_mid": (85, 100, 125),
        "hill_near":    (62, 90, 70),
        "grass":        (90, 145, 60),
        "grass_dark":   (60, 110, 45),
        "dirt":         (110, 80, 55),
        "dirt_dark":    (75, 55, 35),
        "stone":        (105, 100, 95),
        "stone_light":  (140, 135, 125),
    },
    "desert": {
        "sky_top":      (215, 130, 60),
        "sky_bottom":   (245, 220, 175),
        "sun":          (255, 250, 220),
        "sun_inner":    (255, 235, 180),
        "cloud":        (250, 220, 175, 150),
        "mountain_far": (165, 100, 80),
        "mountain_mid": (130, 70, 55),
        "hill_near":    (200, 145, 80),
        "grass":        (210, 175, 90),
        "grass_dark":   (175, 140, 65),
        "dirt":         (200, 150, 95),
        "dirt_dark":    (150, 105, 65),
        "stone":        (115, 80, 65),
        "stone_light":  (165, 125, 95),
    },
    "canyon": {
        "sky_top":      (220, 110, 70),
        "sky_bottom":   (245, 195, 165),
        "sun":          (255, 215, 145),
        "sun_inner":    (255, 235, 180),
        "cloud":        (240, 200, 180, 130),
        "mountain_far": (115, 60, 50),
        "mountain_mid": (95, 45, 40),
        "hill_near":    (170, 85, 60),
        "grass":        (200, 110, 75),
        "grass_dark":   (155, 75, 50),
        "dirt":         (175, 90, 65),
        "dirt_dark":    (115, 55, 40),
        "stone":        (130, 90, 75),
        "stone_light":  (185, 145, 120),
    },
    "ice": {
        "sky_top":      (140, 180, 220),
        "sky_bottom":   (225, 235, 245),
        "sun":          (235, 245, 255),
        "sun_inner":    (250, 250, 255),
        "cloud":        (250, 250, 255, 200),
        "mountain_far": (175, 195, 215),
        "mountain_mid": (130, 155, 185),
        "hill_near":    (215, 225, 235),
        "grass":        (240, 245, 250),
        "grass_dark":   (190, 210, 225),
        "dirt":         (195, 215, 230),
        "dirt_dark":    (140, 175, 200),
        "stone":        (150, 170, 185),
        "stone_light":  (210, 220, 230),
    },
    "volcano": {
        "sky_top":      (60, 25, 30),
        "sky_bottom":   (185, 90, 45),
        "sun":          (255, 100, 50),
        "sun_inner":    (255, 180, 80),
        "cloud":        (90, 70, 70, 160),
        "mountain_far": (60, 45, 50),
        "mountain_mid": (45, 25, 30),
        "hill_near":    (70, 45, 45),
        "grass":        (225, 95, 30),
        "grass_dark":   (160, 60, 30),
        "dirt":         (55, 40, 42),
        "dirt_dark":    (30, 22, 25),
        "stone":        (75, 60, 60),
        "stone_light":  (115, 95, 95),
    },
}

GRAVITY        = 250.0
THROTTLE_FORCE = 750.0
BRAKE_FORCE    = 1400.0
LEAN_TORQUE    = 14.0
AIR_DRAG       = 0.5
ANGULAR_DRAG   = 1.6
WHEEL_RADIUS   = 8.0
WHEELBASE      = 28.0
GROUND_FRICTION = 0.993
CRASH_ANGLE_DEG = 110.0

AXIS_DEAD = 0.4

BTN_THROTTLE = 1
BTN_BRAKE    = 0
BTN_RESET    = 2
BTN_LEFT     = 10
BTN_RIGHT    = 11
BTN_SELECT   = 12
BTN_START    = 17

BIOME_EFFECTS = {
    "grass":   {"particles": ["butterfly"],          "sky_pulse": False, "shake": 0.0},
    "desert":  {"particles": ["dust"],               "sky_pulse": False, "shake": 0.0},
    "canyon":  {"particles": ["dust"],               "sky_pulse": False, "shake": 0.0},
    "ice":     {"particles": ["snow"],               "sky_pulse": False, "shake": 0.0},
    "volcano": {"particles": ["ember", "ash"],       "sky_pulse": True,  "shake": 0.15},
}

MEDAL_GOLD   = "gold"
MEDAL_SILVER = "silver"
MEDAL_BRONZE = "bronze"
MEDAL_NONE   = None
MEDAL_COLORS = {
    MEDAL_GOLD:   (235, 195, 55),
    MEDAL_SILVER: (190, 190, 200),
    MEDAL_BRONZE: (180, 110, 60),
}
