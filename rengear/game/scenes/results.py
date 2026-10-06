"""Race results / standings."""

from __future__ import annotations

import pygame

from rengear.engine.platform import EventType
from rengear.engine.scene import Scene
from rengear.engine.sprites import vertical_gradient
from rengear.engine.ui import draw_panel, draw_text

from ..config import TRACKS
from .race import fmt_time


class ResultsScene(Scene):
    def __init__(self, app, track: str = "coast", cars=None, players=None,
                 total: float = 0.0, best_lap=None) -> None:
        super().__init__(app)
        self.track_key = track
        self.cars = list(cars or [])
        self.players = list(players or [c for c in self.cars if c.is_player])
        self.total = total
        self.best_lap = best_lap
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (6, 8, 20), (24, 14, 38))
        self.standings = self._rank()
        self.t = 0.0

    def _rank(self):
        finished = sorted((c for c in self.cars if c.finished),
                          key=lambda c: c.finish_time)
        running = sorted((c for c in self.cars if not c.finished),
                         key=lambda c: (c.lap, c.z), reverse=True)
        order = finished + running
        for i, car in enumerate(order):
            car.place = i + 1
        return order

    def on_enter(self) -> None:
        self.app.audio.stop_engine()
        self.app.audio.start_music()

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        inp = self.app.input
        if (event.key in inp.bindings.get("confirm", ())
                or event.key in inp.bindings.get("cancel", ())):
            self.app.audio.play("confirm")
            self.app.switch_scene("title")

    def update(self, dt: float) -> None:
        self.t += dt

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        w, h = surface.get_size()
        theme = TRACKS[self.track_key]
        draw_text(surface, self.app.fonts, "RESULTS", (w // 2, 16), size=32,
                  color=(120, 240, 255), center=True, bold=True)
        draw_text(surface, self.app.fonts, theme["name"], (w // 2, 42), size=16,
                  color=(255, 224, 130), center=True)

        winner = self.standings[0] if self.standings else None
        banner = "FINISH!" if winner and winner.is_player else "BETTER LUCK NEXT TIME"
        draw_text(surface, self.app.fonts, banner, (w // 2, 62),
                  size=15, color=(255, 224, 130), center=True, bold=True)

        rows = len(self.standings)
        panel = pygame.Rect(w // 2 - 170, 78, 340, 26 + rows * 24)
        draw_panel(surface, panel, border=(120, 200, 230))

        for i, car in enumerate(self.standings):
            y = panel.y + 12 + i * 24
            color = (255, 240, 170) if car.is_player else (165, 180, 200)
            bold = car.is_player
            drew = "\u25cf" if car.is_player else " "
            draw_text(surface, self.app.fonts, f"{drew} {car.place}  {car.name}",
                      (panel.x + 16, y), size=16, color=color, bold=bold)
            time_text = fmt_time(car.finish_time) if car.finished else "DNF"
            draw_text(surface, self.app.fonts, time_text,
                      (panel.right - 16, y), size=15, color=color, bold=bold,
                      right=True)

        # one summary line per human player
        sy = panel.bottom + 10
        for i, p in enumerate(self.players):
            total = p.finish_time if p.finished else 0.0
            best = p.best_lap
            label = p.name
            draw_text(surface, self.app.fonts,
                      f"{label}   TOTAL {fmt_time(total) if p.finished else '--'}   "
                      f"BEST {fmt_time(best) if best else '--'}",
                      (w // 2, sy + i * 15), size=12,
                      color=(190, 205, 225), center=True)

        draw_text(surface, self.app.fonts, "ENTER: continue",
                  (w // 2, h - 16), size=13, color=(170, 185, 210), center=True)
