"""Surface helpers used to build procedural, original artwork at runtime."""

from __future__ import annotations

import random
from typing import Tuple

import pygame

Color = Tuple[int, int, int]


def new_surface(w: int, h: int, color: Color | None = None,
                alpha: int = 255) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if color is not None:
        surf.fill((*color, alpha))
    return surf


def tint(surface: pygame.Surface, color: Color, amount: float = 0.5) -> pygame.Surface:
    out = surface.copy()
    layer = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    layer.fill((*color, int(255 * amount)))
    out.blit(layer, (0, 0))
    return out


def vertical_gradient(w: int, h: int, top: Color, bottom: Color) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        color = (int(top[0] + (bottom[0] - top[0]) * t),
                 int(top[1] + (bottom[1] - top[1]) * t),
                 int(top[2] + (bottom[2] - top[2]) * t))
        pygame.draw.line(surf, color, (0, y), (w, y))
    return surf


def speckle(surface: pygame.Surface, color: Color, count: int = 40, rng=None,
            size: int = 1) -> None:
    rng = rng or random
    for _ in range(count):
        x = rng.randrange(surface.get_width())
        y = rng.randrange(surface.get_height())
        pygame.draw.rect(surface, color, (x, y, size, size))


def glow(radius: int, color: Color, alpha: int = 180) -> pygame.Surface:
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = int(alpha * (1 - r / radius) ** 1.6)
        pygame.draw.circle(surf, (*color, a), (radius, radius), r)
    return surf


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))
