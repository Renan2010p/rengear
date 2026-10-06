"""Pause overlay."""

from __future__ import annotations

import pygame

from rengear.engine.platform import EventType
from rengear.engine.scene import Scene
from rengear.engine.sprites import vertical_gradient
from rengear.engine.ui import draw_panel, draw_text

ENTRIES = [("resume", "RESUME"), ("restart", "RESTART"), ("quit", "QUIT TO TITLE")]


class PauseScene(Scene):
    def __init__(self, app, race=None) -> None:
        super().__init__(app)
        self.race = race
        self.index = 0
        if race is not None:
            self.bg = race.snapshot()
        else:
            self.bg = vertical_gradient(*app.render_size, (8, 10, 20), (20, 14, 30))

    def on_enter(self) -> None:
        self.app.audio.stop_engine()
        self.app.audio.stop_music()

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        inp = self.app.input
        if (event.key in inp.bindings.get("brake", ())
                or event.key in inp.bindings.get("right", ())):
            self.index = (self.index + 1) % len(ENTRIES)
            self.app.audio.play("select")
        elif (event.key in inp.bindings.get("accelerate", ())
                or event.key in inp.bindings.get("left", ())):
            self.index = (self.index - 1) % len(ENTRIES)
            self.app.audio.play("select")
        elif event.key in inp.bindings.get("confirm", ()):
            self._activate(ENTRIES[self.index][0])
        elif event.key in inp.bindings.get("cancel", ()):
            self._resume()

    def _activate(self, action: str) -> None:
        self.app.audio.play("confirm")
        if action == "resume":
            self._resume()
        elif action == "restart" and self.race is not None:
            self.app.switch_scene("race", car=self.race.car_key,
                                  track=self.race.track_key,
                                  car2=self.race.car2_key)
        elif action == "quit":
            self.app.switch_scene("title")

    def _resume(self) -> None:
        if self.race is not None:
            self.app.scenes.set_current(self.race, call_enter=True)
        else:
            self.app.switch_scene("title")

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((4, 6, 12, 200))
        surface.blit(dim, (0, 0))

        panel = pygame.Rect(w // 2 - 110, h // 2 - 78, 220, 156)
        draw_panel(surface, panel)
        draw_text(surface, self.app.fonts, "PAUSED", (w // 2, panel.y + 24),
                  size=30, color=(120, 240, 255), center=True, bold=True)
        for i, (action, label) in enumerate(ENTRIES):
            selected = i == self.index
            color = (255, 240, 170) if selected else (150, 165, 190)
            text = f"\u00bb {label}" if selected else label
            draw_text(surface, self.app.fonts, text, (w // 2, panel.y + 68 + i * 26),
                      size=19, color=color, center=True, bold=selected)
        draw_text(surface, self.app.fonts, "ESC: resume",
                  (w // 2, panel.bottom - 18), size=12, color=(120, 140, 170),
                  center=True)
