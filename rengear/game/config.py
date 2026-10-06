"""Tunable constants, palette and content tables for RENGEAR.

Everything here is data: adding a car means adding an entry to :data:`CARS`;
adding a track means adding a builder to :mod:`rengear.game.tracks` and a
theme entry to :data:`TRACKS`.
"""

from __future__ import annotations

from typing import Dict, Tuple

from rengear.engine.platform import Key

TITLE = "RENGEAR  ·  RL PROJECTS"

# -- rendering --------------------------------------------------------------
LOGICAL_W = 512
LOGICAL_H = 288
FPS = 60

# -- pseudo-3D road geometry (the "trick") ----------------------------------
ROAD_WIDTH = 2000.0          # half-width of the road in world units
LANES = 3
SEGMENT_LENGTH = 200.0       # world units per road segment
RUMBLE_LENGTH = 3            # segments per rumble stripe
DRAW_DISTANCE = 260          # segments drawn ahead
CAMERA_HEIGHT = 1000.0
FIELD_OF_VIEW = 100.0        # degrees
FOG_DENSITY = 4.0
CENTRIFUGAL = 0.30           # how hard curves push the car out
OFF_ROAD_MAX = 0.30          # top-speed fraction while off-road
OFF_ROAD_DECEL = -9000.0     # must out-pull acceleration off-road

# -- car physics ------------------------------------------------------------
MAX_SPEED = 12000.0          # world units per second
ACCEL = 3200.0
BRAKING = -9000.0
DECEL = -2400.0
STEER_RATE = 2.0             # full left↔right sweep per second at top speed
NITRO_MULT = 1.35
NITRO_DRAIN = 0.42           # per second while held
NITRO_RECHARGE = 0.06        # per second while not held

LAPS = 3
RACE_CARS = 4                # player + rivals
COUNTDOWN = 3.0
GEARS = 6                    # automatic gearbox, purely for feel / HUD

# -- palette ----------------------------------------------------------------
WHITE = (238, 240, 248)
HUD_CYAN = (120, 240, 255)
HUD_GOLD = (255, 224, 130)
HUD_RED = (255, 110, 96)

# -- cars -------------------------------------------------------------------
#: ``grip`` scales steering, ``power`` scales acceleration, ``top`` scales
#: top speed.  ``color``/``accent`` drive the procedural body sprite.
CARS: Dict[str, Dict[str, object]] = {
    "spark": {
        "name": "SPARK",
        "blurb": "balanced · easy",
        "color": (226, 62, 74), "accent": (255, 210, 120),
        "power": 1.00, "top": 0.94, "grip": 1.08, "nitro": 1.20,
    },
    "comet": {
        "name": "COMET",
        "blurb": "fast · light",
        "color": (72, 176, 240), "accent": (235, 240, 250),
        "power": 0.92, "top": 1.00, "grip": 0.98, "nitro": 1.00,
    },
    "vulcan": {
        "name": "VULCAN",
        "blurb": "top speed · heavy",
        "color": (150, 96, 220), "accent": (255, 180, 90),
        "power": 0.86, "top": 1.08, "grip": 0.90, "nitro": 0.85,
    },
    "dune": {
        "name": "DUNE",
        "blurb": "grip · off-road",
        "color": (214, 168, 66), "accent": (60, 70, 90),
        "power": 1.02, "top": 0.90, "grip": 1.16, "nitro": 0.95,
    },
}
CAR_ORDER = ["spark", "comet", "vulcan", "dune"]

# -- tracks -----------------------------------------------------------------
#: Each theme paints sky, ground, road, rumble and lane colours plus a set of
#: roadside props.  ``sky`` is (top, horizon); ``ground`` is (light, dark).
TRACKS: Dict[str, Dict[str, object]] = {
    "coast": {
        "name": "NARA COAST",
        "note": "green hills by the sea",
        "sky": ((70, 150, 220), (176, 214, 236)),
        "ground": ((72, 140, 78), (52, 112, 62)),
        "road": ((92, 94, 102), (82, 84, 92)),
        "rumble": ((228, 232, 240), (208, 60, 60)),
        "lane": (236, 238, 244),
        "props": ["tree", "tree", "sign", "rock", "palm"],
    },
    "dusk": {
        "name": "DUSK CANYON",
        "note": "sunset mesas",
        "sky": ((56, 40, 92), (240, 138, 92)),
        "ground": ((136, 84, 62), (98, 58, 46)),
        "road": ((96, 84, 88), (84, 74, 80)),
        "rumble": ((250, 214, 180), (188, 70, 60)),
        "lane": (250, 226, 194),
        "props": ["rock", "cactus", "rock", "sign", "rock"],
    },
    "pine": {
        "name": "PINE PASS",
        "note": "mountain forest",
        "sky": ((120, 168, 196), (206, 226, 232)),
        "ground": ((44, 86, 58), (30, 62, 44)),
        "road": ((88, 90, 96), (78, 80, 86)),
        "rumble": ((226, 230, 236), (70, 110, 90)),
        "lane": (230, 234, 240),
        "props": ["pine", "pine", "rock", "pine", "sign"],
    },
    "dunes": {
        "name": "CRIMSON DUNES",
        "note": "open desert",
        "sky": ((238, 196, 140), (250, 226, 186)),
        "ground": ((224, 176, 106), (196, 146, 86)),
        "road": ((104, 98, 96), (92, 86, 84)),
        "rumble": ((248, 244, 234), (196, 96, 60)),
        "lane": (250, 246, 236),
        "props": ["cactus", "rock", "sign", "rock", "cactus"],
    },
    "night": {
        "name": "MIDNIGHT CITY",
        "note": "neon downtown",
        "sky": ((8, 10, 30), (34, 22, 62)),
        "ground": ((26, 28, 46), (18, 20, 34)),
        "road": ((58, 60, 74), (48, 50, 62)),
        "rumble": ((120, 220, 255), (240, 80, 200)),
        "lane": (150, 240, 255),
        "props": ["lamp", "sign", "lamp", "billboard", "lamp"],
    },
    "polar": {
        "name": "POLAR RIDGE",
        "note": "frozen pass",
        "sky": ((150, 186, 220), (224, 236, 246)),
        "ground": ((226, 234, 244), (196, 212, 230)),
        "road": ((104, 110, 122), (92, 98, 110)),
        "rumble": ((250, 252, 255), (90, 130, 190)),
        "lane": (250, 252, 255),
        "props": ["pine", "rock", "sign", "pine", "rock"],
    },
}
TRACK_ORDER = ["coast", "dusk", "pine", "dunes", "night", "polar"]

# -- local multiplayer key profiles -----------------------------------------
#: single player (arrows *and* WASD, nitro on Z/Space)
P1_KEYS = {
    "left": [Key.LEFT, Key.A], "right": [Key.RIGHT, Key.D],
    "accelerate": [Key.UP, Key.W], "brake": [Key.DOWN, Key.S],
    "nitro": [Key.Z, Key.SPACE],
}
#: in split screen player 1 keeps the arrows and player 2 gets WASD
P1_COOP_KEYS = {
    "left": [Key.LEFT], "right": [Key.RIGHT],
    "accelerate": [Key.UP], "brake": [Key.DOWN],
    "nitro": [Key.Z],
}
P2_COOP_KEYS = {
    "left": [Key.A], "right": [Key.D],
    "accelerate": [Key.W], "brake": [Key.S],
    "nitro": [Key.C],
}

# -- rival AI ---------------------------------------------------------------
#: (speed fraction, grip, aggression, name, colour, accent)
RIVALS = [
    ("BLITZ", (232, 96, 64), (255, 224, 150), 0.965, 1.00, 1.00),
    ("VIPER", (86, 200, 128), (235, 245, 240), 0.955, 1.02, 0.95),
    ("ONYX", (58, 60, 78), (180, 190, 210), 0.975, 0.96, 1.05),
]
