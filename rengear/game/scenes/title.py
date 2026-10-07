"""Title screen."""

from __future__ import annotations

import math
import random

import pygame

from rengear.engine.platform import EventType
from rengear.engine.scene import Scene
from rengear.engine.sprites import vertical_gradient
from rengear.engine.ui import draw_text

from .. import art
from ..config import CARS, TITLE


class TitleScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.t = 0.0
        self.index = 0
        self.entries = self._build_entries()
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (6, 8, 20), (26, 14, 40))
        rng = random.Random(11)
        self.stars = [(rng.uniform(0, w), rng.uniform(0, h * 0.7),
                       rng.choice((60, 90, 130)), rng.choice((1, 1, 2)))
                      for _ in range(120)]
        self.car_key = app.get_setting("car", "spark")
        self.car = CARS.get(self.car_key, CARS["spark"])

    def _build_entries(self):
        sound = "ON" if self.app.audio.enabled else "OFF"
        fps = "ON" if getattr(self.app, "show_fps", False) else "OFF"
        return [
            ("one", "1 PLAYER"),
            ("two", "2 PLAYERS  (split screen)"),
            ("sound", f"SOUND: {sound}"),
            ("fps", f"SHOW FPS: {fps}"),
            ("quit", "QUIT"),
        ]

    def on_enter(self) -> None:
        self.entries = self._build_entries()
        self.index = min(self.index, len(self.entries) - 1)
        self.app.audio.start_music()
        self.app.audio.stop_engine()

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        down = self.app.input.bindings.get("brake", ()) + \
            self.app.input.bindings.get("right", ())
        up = self.app.input.bindings.get("accelerate", ()) + \
            self.app.input.bindings.get("left", ())
        confirm = self.app.input.bindings.get("confirm", ())
        if event.key in down:
            self.index = (self.index + 1) % len(self.entries)
            self.app.audio.play("select")
        elif event.key in up:
            self.index = (self.index - 1) % len(self.entries)
            self.app.audio.play("select")
        elif event.key in confirm:
            self._activate(self.entries[self.index][0])

    def _activate(self, action: str) -> None:
        if action == "sound":
            self.app.audio.set_enabled(not self.app.audio.enabled)
            self.app.set_setting("sound", self.app.audio.enabled)
            self.entries = self._build_entries()
            self.app.audio.play("confirm")
            return
        if action == "fps":
            self.app.show_fps = not getattr(self.app, "show_fps", False)
            self.app.set_setting("show_fps", self.app.show_fps)
            self.entries = self._build_entries()
            self.app.audio.play("confirm")
            return
        self.app.audio.play("confirm")
        if action == "one":
            self.app.switch_scene("choose", players=1)
        elif action == "two":
            self.app.switch_scene("choose", players=2)
        elif action == "quit":
            self.app.quit()

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        w, h = surface.get_size()
        for sx, sy, color, r in self.stars:
            x = (sx - self.t * 8) % w
            y = (sy - self.t * 4) % (h * 0.7)
            pygame.draw.circle(surface, color, (int(x), int(y)), r)

        # a stylised strip of road receding to the horizon
        horizon = int(h * 0.66)
        pygame.draw.rect(surface, (18, 18, 26), (0, horizon, w, h - horizon))
        for i in range(14):
            t = i / 13
            y = horizon + int((h - horizon) * (t ** 1.7))
            half = int(18 + 300 * (t ** 1.7))
            dark = (40, 40, 52) if i % 2 == 0 else (48, 48, 62)
            pygame.draw.polygon(surface, dark, [
                (w // 2 - half, y), (w // 2 + half, y),
                (w // 2 + half + 26, y + 40), (w // 2 - half - 26, y + 40)])

        # chosen car, bobbing
        bob = math.sin(self.t * 3.0) * 3.0
        car = art.car_rear(self.car["color"], self.car["accent"], 124, 80)
        surface.blit(car, (w // 2 - 62, h - 92 + bob))

        draw_text(surface, self.app.fonts, "RENGEAR", (w // 2, 22), size=54,
                  color=(120, 240, 255), center=True, bold=True)
        draw_text(surface, self.app.fonts, "the trick of the tracks",
                  (w // 2, 54), size=17, color=(200, 170, 220), center=True)

        start = 70
        for i, (action, label) in enumerate(self.entries):
            selected = i == self.index
            color = (255, 240, 170) if selected else (140, 155, 180)
            text = f"\u00bb {label}" if selected else label
            draw_text(surface, self.app.fonts, text, (w // 2, start + i * 22),
                      size=20, color=color, center=True, bold=selected)

        draw_text(surface, self.app.fonts,
                  "arrows / WASD: steer & select   Z/SPACE: nitro   ENTER: start",
                  (w // 2, 180), size=13, color=(120, 140, 170), center=True)
        draw_text(surface, self.app.fonts, TITLE, (8, h - 14),
                  size=11, color=(90, 105, 130))
