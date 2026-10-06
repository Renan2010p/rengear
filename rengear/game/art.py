"""Procedural, original artwork built at runtime.

Every sprite here is drawn from geometric primitives — no image files, no
ripped assets — which is both a legal guarantee (see docs/LEGAL.md) and a
modding convenience: change a colour tuple and the whole car changes.
"""

from __future__ import annotations

import math
import random
from typing import Dict, Tuple

import pygame

from ..engine.sprites import new_surface

Color = Tuple[int, int, int]

#: tiny cache so a car/prop is only painted once per (kind, size, colours)
_CACHE: Dict[tuple, pygame.Surface] = {}


def _shade(color: Color, amount: int) -> Color:
    return tuple(max(0, min(255, c + amount)) for c in color)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# cars
# ---------------------------------------------------------------------------

def car_rear(color: Color, accent: Color, w: int = 96, h: int = 62) -> pygame.Surface:
    """A rear view of a formula-style car (the one you drive)."""
    key = ("rear", w, h, color, accent)
    if key in _CACHE:
        return _CACHE[key]
    s = new_surface(w, h)
    dark = _shade(color, -60)
    light = _shade(color, 60)

    # rear wing
    pygame.draw.rect(s, dark, (w * 0.08, h * 0.10, w * 0.84, h * 0.14))
    pygame.draw.rect(s, accent, (w * 0.08, h * 0.10, w * 0.84, h * 0.05))
    pygame.draw.rect(s, dark, (w * 0.16, h * 0.22, w * 0.06, h * 0.16))
    pygame.draw.rect(s, dark, (w * 0.78, h * 0.22, w * 0.06, h * 0.16))

    # body
    body = pygame.Rect(w * 0.14, h * 0.32, w * 0.72, h * 0.40)
    pygame.draw.rect(s, color, body, border_radius=6)
    pygame.draw.rect(s, light, (body.x, body.y, body.w, h * 0.08), border_radius=4)
    pygame.draw.rect(s, dark, (body.x, body.bottom - h * 0.08, body.w, h * 0.08),
                     border_radius=4)

    # cockpit / engine cover
    pygame.draw.polygon(s, (28, 32, 44), [
        (w * 0.34, h * 0.34), (w * 0.66, h * 0.34),
        (w * 0.60, h * 0.52), (w * 0.40, h * 0.52)])

    # tail lights
    pygame.draw.rect(s, (255, 70, 60), (w * 0.18, h * 0.52, w * 0.14, h * 0.10),
                     border_radius=2)
    pygame.draw.rect(s, (255, 70, 60), (w * 0.68, h * 0.52, w * 0.14, h * 0.10),
                     border_radius=2)

    # exhausts
    pygame.draw.rect(s, (40, 42, 52), (w * 0.44, h * 0.60, w * 0.05, h * 0.06))
    pygame.draw.rect(s, (40, 42, 52), (w * 0.51, h * 0.60, w * 0.05, h * 0.06))

    # rear tyres
    pygame.draw.rect(s, (20, 20, 26), (0.02 * w, h * 0.50, w * 0.20, h * 0.42),
                     border_radius=4)
    pygame.draw.rect(s, (20, 20, 26), (w * 0.78, h * 0.50, w * 0.20, h * 0.42),
                     border_radius=4)
    pygame.draw.rect(s, accent, (0.04 * w, h * 0.62, w * 0.16, h * 0.06))
    pygame.draw.rect(s, accent, (w * 0.80, h * 0.62, w * 0.16, h * 0.06))

    _CACHE[key] = s
    return s


def car_top(color: Color, accent: Color, w: int = 92, h: int = 140) -> pygame.Surface:
    """A top-down view used on the car-select screen."""
    key = ("top", w, h, color, accent)
    if key in _CACHE:
        return _CACHE[key]
    s = new_surface(w, h)
    dark = _shade(color, -60)
    light = _shade(color, 55)
    tyre = (22, 22, 28)

    # front wing
    pygame.draw.rect(s, dark, (6, 6, w - 12, 9), border_radius=3)
    pygame.draw.rect(s, accent, (6, 6, w - 12, 3))

    # nose + body
    pygame.draw.polygon(s, color, [
        (w * 0.50, 12), (w * 0.62, h * 0.30),
        (w * 0.62, h * 0.74), (w * 0.38, h * 0.74), (w * 0.38, h * 0.30)])
    pygame.draw.rect(s, color, (w * 0.34, h * 0.28, w * 0.32, h * 0.50),
                     border_radius=8)

    # side pods
    pygame.draw.rect(s, dark, (w * 0.16, h * 0.44, w * 0.18, h * 0.26),
                     border_radius=5)
    pygame.draw.rect(s, dark, (w * 0.66, h * 0.44, w * 0.18, h * 0.26),
                     border_radius=5)

    # rear wing
    pygame.draw.rect(s, dark, (w * 0.08, h - 20, w * 0.84, 12), border_radius=3)
    pygame.draw.rect(s, accent, (w * 0.08, h - 20, w * 0.84, 4))

    # wheels
    pygame.draw.rect(s, tyre, (2, int(h * 0.22), 14, 26), border_radius=4)
    pygame.draw.rect(s, tyre, (w - 16, int(h * 0.22), 14, 26), border_radius=4)
    pygame.draw.rect(s, tyre, (0, int(h * 0.60), 18, 32), border_radius=5)
    pygame.draw.rect(s, tyre, (w - 18, int(h * 0.60), 18, 32), border_radius=5)

    # cockpit + helmet
    pygame.draw.ellipse(s, (28, 32, 44), (w * 0.40, h * 0.34, w * 0.20, h * 0.20))
    pygame.draw.circle(s, accent, (w // 2, int(h * 0.43)), int(w * 0.07))
    pygame.draw.line(s, light, (w * 0.50, 16), (w * 0.50, h * 0.34), 2)

    _CACHE[key] = s
    return s


def car_front(color: Color, accent: Color, w: int = 132, h: int = 96) -> pygame.Surface:
    """A 3/4 front view used on the car-select screen."""
    key = ("front", w, h, color, accent)
    if key in _CACHE:
        return _CACHE[key]
    s = new_surface(w, h)
    dark = _shade(color, -60)
    light = _shade(color, 55)

    # front wing
    pygame.draw.rect(s, dark, (w * 0.06, h * 0.72, w * 0.88, h * 0.10),
                     border_radius=4)
    pygame.draw.rect(s, accent, (w * 0.06, h * 0.72, w * 0.88, h * 0.04))

    # nose
    pygame.draw.polygon(s, color, [
        (w * 0.50, h * 0.16), (w * 0.72, h * 0.50),
        (w * 0.78, h * 0.78), (w * 0.22, h * 0.78), (w * 0.28, h * 0.50)])
    pygame.draw.polygon(s, light, [
        (w * 0.50, h * 0.16), (w * 0.58, h * 0.44), (w * 0.42, h * 0.44)])

    # cockpit
    pygame.draw.ellipse(s, (26, 30, 42), (w * 0.36, h * 0.30, w * 0.28, h * 0.22))
    # helmet
    pygame.draw.circle(s, accent, (int(w * 0.50), int(h * 0.38)), int(h * 0.08))

    # side pods
    pygame.draw.rect(s, dark, (w * 0.16, h * 0.56, w * 0.16, h * 0.22),
                     border_radius=4)
    pygame.draw.rect(s, dark, (w * 0.68, h * 0.56, w * 0.16, h * 0.22),
                     border_radius=4)

    # front wheels
    pygame.draw.rect(s, (22, 22, 28), (w * 0.02, h * 0.58, w * 0.18, h * 0.34),
                     border_radius=5)
    pygame.draw.rect(s, (22, 22, 28), (w * 0.80, h * 0.58, w * 0.18, h * 0.34),
                     border_radius=5)

    _CACHE[key] = s
    return s


# ---------------------------------------------------------------------------
# roadside props
# ---------------------------------------------------------------------------

def tree(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(72, 104)
    pygame.draw.rect(s, (86, 62, 44), (32, 62, 8, 42))
    for cx, cy, r, col in ((36, 40, 30, (58, 132, 66)),
                           (24, 52, 22, (48, 114, 58)),
                           (48, 54, 22, (68, 148, 76)),
                           (36, 28, 22, (80, 162, 86))):
        pygame.draw.circle(s, col, (cx, cy), r)
    return s


def pine(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(64, 120)
    pygame.draw.rect(s, (74, 54, 40), (28, 92, 8, 28))
    for i, (cy, half) in enumerate(((24, 16), (46, 22), (70, 28))):
        col = (34, 84, 54) if i % 2 else (44, 104, 66)
        pygame.draw.polygon(s, col, [
            (32, cy - 14), (32 - half, cy + 22), (32 + half, cy + 22)])
    return s


def palm(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(72, 120)
    pygame.draw.rect(s, (120, 92, 58), (34, 40, 7, 78))
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        ex, ey = 37 + math.cos(a) * 32, 42 + math.sin(a) * 16
        pygame.draw.line(s, (60, 140, 72), (37, 42), (ex, ey), 4)
    pygame.draw.circle(s, (48, 120, 62), (37, 42), 7)
    return s


def cactus(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(56, 104)
    col = (62, 132, 82)
    pygame.draw.rect(s, col, (24, 24, 10, 76), border_radius=5)
    pygame.draw.rect(s, col, (10, 48, 10, 30), border_radius=5)
    pygame.draw.rect(s, col, (36, 40, 10, 38), border_radius=5)
    pygame.draw.rect(s, col, (10, 48, 24, 9), border_radius=4)
    pygame.draw.rect(s, col, (24, 40, 22, 9), border_radius=4)
    pygame.draw.line(s, (86, 160, 104), (27, 30), (27, 96), 2)
    return s


def rock(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(72, 56)
    pygame.draw.polygon(s, (122, 118, 112), [
        (8, 52), (18, 22), (40, 12), (62, 30), (66, 52)])
    pygame.draw.polygon(s, (152, 148, 142), [
        (18, 22), (40, 12), (46, 28), (28, 34)])
    pygame.draw.polygon(s, (92, 88, 84), [(46, 28), (62, 30), (66, 52), (44, 52)])
    return s


def sign(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(56, 96)
    pygame.draw.rect(s, (110, 110, 118), (26, 44, 6, 52))
    board = pygame.Rect(4, 10, 48, 40)
    pygame.draw.rect(s, (226, 226, 232), board, border_radius=5)
    pygame.draw.rect(s, (60, 60, 70), board, width=3, border_radius=5)
    pygame.draw.polygon(s, (240, 200, 60), [(20, 18), (36, 30), (20, 42)])
    pygame.draw.polygon(s, (240, 200, 60), [(36, 18), (20, 30), (36, 42)])
    return s


def lamp(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(48, 128)
    pygame.draw.rect(s, (70, 74, 88), (22, 30, 5, 98))
    pygame.draw.line(s, (70, 74, 88), (24, 32), (12, 18), 4)
    pygame.draw.circle(s, (255, 232, 150), (12, 18), 6)
    return s


def billboard(rng: random.Random | None = None) -> pygame.Surface:
    s = new_surface(112, 112)
    pygame.draw.rect(s, (80, 84, 96), (26, 60, 8, 52))
    pygame.draw.rect(s, (80, 84, 96), (78, 60, 8, 52))
    board = pygame.Rect(4, 8, 104, 56)
    pygame.draw.rect(s, (24, 26, 40), board, border_radius=6)
    pygame.draw.rect(s, (120, 240, 255), board, width=3, border_radius=6)
    pygame.draw.polygon(s, (255, 90, 200), [(30, 20), (52, 44), (18, 44)])
    pygame.draw.circle(s, (255, 224, 130), (76, 34), 12)
    return s


PROP_FACTORIES = {
    "tree": tree,
    "pine": pine,
    "palm": palm,
    "cactus": cactus,
    "rock": rock,
    "sign": sign,
    "lamp": lamp,
    "billboard": billboard,
}


def prop(name: str) -> pygame.Surface:
    factory = PROP_FACTORIES.get(name)
    if factory is None:
        return rock()
    key = ("prop", name)
    surf = _CACHE.get(key)
    if surf is None:
        surf = factory()
        _CACHE[key] = surf
    return surf


# ---------------------------------------------------------------------------
# effects
# ---------------------------------------------------------------------------

def nitro_flame(w: int = 40, h: int = 60, phase: float = 0.0) -> pygame.Surface:
    s = new_surface(w, h)
    flick = 0.5 + 0.5 * math.sin(phase * 12.0)
    for i, (col, scale) in enumerate((
            ((80, 140, 255), 1.0),
            ((120, 220, 255), 0.7),
            ((235, 250, 255), 0.4))):
        hh = int(h * scale * (0.8 + 0.2 * flick))
        ww = int(w * scale)
        pygame.draw.polygon(s, col, [
            (w // 2 - ww // 2, 0), (w // 2 + ww // 2, 0),
            (w // 2, hh)])
    return s


def checker(w: int, h: int, cell: int = 8) -> pygame.Surface:
    s = new_surface(w, h)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                pygame.draw.rect(s, (245, 245, 248), (x, y, cell, cell))
            else:
                pygame.draw.rect(s, (24, 24, 30), (x, y, cell, cell))
    return s
