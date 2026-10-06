"""Small immediate-mode UI toolkit (text, bars, panels, menus)."""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import pygame

from .platform import Backend

Color = Tuple[int, int, int]


class Fonts:
    """Font cache backed by the active platform (no direct OS calls)."""

    def __init__(self, backend: Optional[Backend] = None) -> None:
        self.backend = backend
        self._cache: Dict[Tuple, object] = {}

    def get(self, size: int, bold: bool = False):
        key = (size, bold)
        font = self._cache.get(key)
        if font is None:
            font = self.backend.load_font(size, bold) if self.backend else None
            self._cache[key] = font
        return font


def draw_text(surface, fonts: Fonts, text: str, pos, size=20,
              color=(235, 235, 245), center=False, bold=False,
              shadow=(0, 0, 0), right=False) -> pygame.Rect:
    font = fonts.get(size, bold)
    if shadow is not None:
        shadow_surf = font.render(text, True, shadow)
        rect = shadow_surf.get_rect()
        if center:
            rect.center = pos
        elif right:
            rect.topright = pos
        else:
            rect.topleft = pos
        surface.blit(shadow_surf, (rect.x + 2, rect.y + 2))
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = pos
    elif right:
        rect.topright = pos
    else:
        rect.topleft = pos
    surface.blit(surf, rect)
    return rect


def draw_bar(surface, x, y, w, h, ratio, fill: Color, back: Color = (30, 30, 45),
             border: Color = (12, 12, 20), segments: int = 0) -> None:
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, border, (x - 2, y - 2, w + 4, h + 4),
                     border_radius=3)
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=2)
    fw = int(w * ratio)
    if fw > 0:
        pygame.draw.rect(surface, fill, (x, y, fw, h), border_radius=2)
    if segments > 1:
        for i in range(1, segments):
            gx = x + int(w * i / segments)
            pygame.draw.line(surface, border, (gx, y), (gx, y + h))


def draw_panel(surface, rect: pygame.Rect, fill=(16, 18, 30, 235),
               border=(90, 200, 220)) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=8)
    pygame.draw.rect(panel, border, panel.get_rect(), width=2, border_radius=8)
    surface.blit(panel, rect.topleft)


def draw_gauge(surface, center, radius, ratio, rim=(90, 200, 220),
               needle=(255, 90, 80), face=(10, 12, 20), redline=None,
               ticks: int = 10) -> None:
    """An analog dial (speedometer / tachometer).

    ``ratio`` is 0..1 and sweeps the needle from lower-left, over the top, to
    lower-right.  ``redline`` (0..1) paints the top of the scale red, like a
    rev limiter.  Text is drawn by the caller so this stays reusable.
    """
    cx, cy = center
    ratio = max(0.0, min(1.0, ratio))

    def point(r: float, t: float):
        angle = math.radians(140.0 + 260.0 * t)
        return (cx + math.cos(angle) * r, cy + math.sin(angle) * r)

    pygame.draw.circle(surface, face, (cx, cy), radius)
    pygame.draw.circle(surface, rim, (cx, cy), radius, 2)

    for i in range(ticks + 1):
        t = i / ticks
        hot = redline is not None and t >= redline
        col = (255, 90, 80) if hot else (150, 170, 190)
        long = i % 5 == 0
        pygame.draw.line(surface, col, point(radius - 3, t),
                         point(radius - (11 if long else 6), t), 2 if long else 1)

    tip = point(radius - 11, ratio)
    pygame.draw.line(surface, needle, (cx, cy), tip, 3)
    pygame.draw.circle(surface, rim, (cx, cy), 4)
