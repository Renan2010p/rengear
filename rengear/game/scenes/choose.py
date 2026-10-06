"""Car and track selection (1 or 2 local players)."""

from __future__ import annotations

import pygame

from rengear.engine.platform import EventType
from rengear.engine.scene import Scene
from rengear.engine.sprites import vertical_gradient
from rengear.engine.ui import draw_bar, draw_panel, draw_text

from .. import art
from ..config import (CAR_ORDER, CARS, P1_COOP_KEYS, P2_COOP_KEYS, TRACK_ORDER,
                      TRACKS)


def _norm(value: float, low: float, high: float) -> float:
    return max(0.05, min(1.0, (value - low) / (high - low)))


class ChooseScene(Scene):
    def __init__(self, app, players: int = 1) -> None:
        super().__init__(app)
        self.players = 2 if players == 2 else 1
        saved = app.get_setting("car", "spark")
        self.car_index = CAR_ORDER.index(saved) if saved in CAR_ORDER else 0
        saved2 = app.get_setting("car2", CAR_ORDER[(self.car_index + 1) % len(CAR_ORDER)])
        self.car2_index = CAR_ORDER.index(saved2) if saved2 in CAR_ORDER else 1
        saved_t = app.get_setting("track", "coast")
        self.track_index = TRACK_ORDER.index(saved_t) if saved_t in TRACK_ORDER else 0
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (8, 10, 22), (20, 12, 32))

    @property
    def car_key(self) -> str:
        return CAR_ORDER[self.car_index]

    @property
    def car2_key(self) -> str:
        return CAR_ORDER[self.car2_index]

    @property
    def track_key(self) -> str:
        return TRACK_ORDER[self.track_index]

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        p1 = P1_COOP_KEYS
        p2 = P2_COOP_KEYS
        if self.players == 2 and event.key in p2["left"]:
            self.car2_index = (self.car2_index - 1) % len(CAR_ORDER)
            self.app.audio.play("select")
        elif self.players == 2 and event.key in p2["right"]:
            self.car2_index = (self.car2_index + 1) % len(CAR_ORDER)
            self.app.audio.play("select")
        elif event.key in p1["left"]:
            self.car_index = (self.car_index - 1) % len(CAR_ORDER)
            self.app.audio.play("select")
        elif event.key in p1["right"]:
            self.car_index = (self.car_index + 1) % len(CAR_ORDER)
            self.app.audio.play("select")
        elif event.key in p1["accelerate"]:
            self.track_index = (self.track_index - 1) % len(TRACK_ORDER)
            self.app.audio.play("select")
        elif event.key in p1["brake"]:
            self.track_index = (self.track_index + 1) % len(TRACK_ORDER)
            self.app.audio.play("select")
        elif event.key in self.app.input.bindings.get("confirm", ()):
            self._start()
        elif event.key in self.app.input.bindings.get("cancel", ()):
            self.app.audio.play("cancel")
            self.app.switch_scene("title")

    def _start(self) -> None:
        self.app.set_setting("car", self.car_key)
        self.app.set_setting("car2", self.car2_key)
        self.app.set_setting("track", self.track_key)
        self.app.audio.play("confirm")
        self.app.switch_scene("race", car=self.car_key, track=self.track_key,
                              car2=self.car2_key if self.players == 2 else None)

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        w, h = surface.get_size()
        if self.players == 2:
            self._draw_split(surface, w, h)
        else:
            self._draw_solo(surface, w, h)

    def _draw_solo(self, surface, w, h) -> None:
        draw_text(surface, self.app.fonts, "SETUP", (w // 2, 16), size=30,
                  color=(120, 240, 255), center=True, bold=True)
        draw_text(surface, self.app.fonts,
                  "left/right: car    up/down: track    ENTER: start    ESC: back",
                  (w // 2, 40), size=13, color=(150, 165, 190), center=True)
        self._car_panel(surface, pygame.Rect(16, 56, 236, 222),
                        self.car_key, "YOUR CAR")
        self._track_panel(surface, pygame.Rect(260, 56, 236, 222))

    def _draw_split(self, surface, w, h) -> None:
        draw_text(surface, self.app.fonts, "SETUP  \u00b7  2 PLAYERS", (w // 2, 12),
                  size=26, color=(120, 240, 255), center=True, bold=True)
        draw_text(surface, self.app.fonts,
                  "P1 arrows   P2 A/D   track: up/down   ENTER: start   ESC: back",
                  (w // 2, 34), size=12, color=(150, 165, 190), center=True)
        self._car_panel(surface, pygame.Rect(12, 50, 240, 184),
                        self.car_key, "PLAYER 1", accent_border=(90, 200, 220))
        self._car_panel(surface, pygame.Rect(260, 50, 240, 184),
                        self.car2_key, "PLAYER 2", accent_border=(240, 180, 110))

        track = TRACKS[self.track_key]
        draw_text(surface, self.app.fonts, f"TRACK   {track['name']}",
                  (w // 2, h - 42), size=17, color=(255, 224, 130),
                  center=True, bold=True)
        draw_text(surface, self.app.fonts, track["note"], (w // 2, h - 24),
                  size=12, color=(180, 195, 215), center=True)

    # ------------------------------------------------------------------
    def _car_panel(self, surface, rect: pygame.Rect, car_key: str, title: str,
                   accent_border=(120, 200, 230)) -> None:
        draw_panel(surface, rect, border=accent_border)
        car = CARS[car_key]
        draw_text(surface, self.app.fonts, title, (rect.centerx, rect.y + 12),
                  size=13, color=(170, 190, 210), center=True)
        draw_text(surface, self.app.fonts, car["name"],
                  (rect.centerx, rect.y + 30), size=22,
                  color=car["color"], center=True, bold=True)
        draw_text(surface, self.app.fonts, car["blurb"],
                  (rect.centerx, rect.y + 49), size=12,
                  color=(170, 185, 210), center=True)

        img = pygame.transform.smoothscale(
            art.car_top(car["color"], car["accent"]), (58, 88))
        surface.blit(img, (rect.x + 20, rect.y + 66))

        stats = [
            ("POWER", _norm(car["power"], 0.80, 1.05)),
            ("SPEED", _norm(car["top"], 0.85, 1.10)),
            ("GRIP", _norm(car["grip"], 0.85, 1.20)),
            ("NITRO", _norm(car["nitro"], 0.80, 1.25)),
        ]
        bx = rect.x + 104
        for i, (label, ratio) in enumerate(stats):
            y = rect.y + 68 + i * 26
            draw_text(surface, self.app.fonts, label, (bx, y), size=11,
                      color=(180, 195, 215))
            draw_bar(surface, bx, y + 13, 120, 7, ratio, car["accent"], segments=6)

    def _track_panel(self, surface, rect: pygame.Rect) -> None:
        draw_panel(surface, rect, border=(240, 180, 110))
        track = TRACKS[self.track_key]
        draw_text(surface, self.app.fonts, track["name"],
                  (rect.centerx, rect.y + 20), size=21,
                  color=(255, 224, 130), center=True, bold=True)
        draw_text(surface, self.app.fonts, track["note"],
                  (rect.centerx, rect.y + 40), size=13,
                  color=(180, 195, 215), center=True)

        pv = pygame.Rect(rect.x + 28, rect.y + 56, rect.w - 56, 58)
        pygame.draw.rect(surface, track["sky"][0], pv)
        pygame.draw.rect(surface, track["sky"][1], (pv.x, pv.y + 28, pv.w, 30))
        pygame.draw.rect(surface, track["ground"][0], (pv.x, pv.bottom - 14, pv.w, 14))
        pygame.draw.polygon(surface, track["road"][0], [
            (pv.centerx - 6, pv.bottom - 16), (pv.centerx + 6, pv.bottom - 16),
            (pv.centerx + 44, pv.bottom), (pv.centerx - 44, pv.bottom)])
        pygame.draw.rect(surface, (20, 22, 30), pv, width=2)

        for i, key in enumerate(TRACK_ORDER):
            selected = i == self.track_index
            color = (255, 240, 170) if selected else (150, 165, 190)
            prefix = "\u00bb " if selected else "  "
            draw_text(surface, self.app.fonts, prefix + TRACKS[key]["name"],
                      (rect.x + 20, rect.y + 126 + i * 15), size=12,
                      color=color, bold=selected)
