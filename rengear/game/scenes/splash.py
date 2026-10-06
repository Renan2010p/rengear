"""Boot splash — the RL PROJECTS studio card.

It fades the studio in and out, then the engine, then the game, and moves on
to the title.  Any key skips it.
"""

from __future__ import annotations

from rengear.engine.platform import EventType
from rengear.engine.scene import Scene
from rengear.engine.sprites import vertical_gradient
from rengear.engine.ui import draw_text

from ... import rlprojects

#: title, subtitle, colour, size
LINES = [
    (rlprojects.STUDIO, "presents a pseudo-3D arcade racer", (235, 235, 245), 56),
    (rlprojects.ENGINE, "powered by the engine layer", (150, 190, 230), 30),
    ("RENGEAR", "the trick of the tracks", (120, 240, 255), 48),
]

FADE_SPEED = 600.0
HOLD_TIME = 0.9


class SplashScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (2, 3, 8), (12, 10, 24))
        self.line = 0
        self.phase = 0            # 0 fade in, 1 hold, 2 fade out
        self.timer = 0.0
        self.alpha = 0.0
        self.done = False
        self._advanced = False

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type in (EventType.KEYDOWN, EventType.MOUSEBUTTONDOWN):
            self.done = True

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.phase == 0:
            self.alpha += FADE_SPEED * dt
            if self.alpha >= 255.0:
                self.alpha = 255.0
                self.phase = 1
                self.timer = 0.0
        elif self.phase == 1:
            if self.timer >= HOLD_TIME:
                self.phase = 2
        else:
            self.alpha -= FADE_SPEED * dt
            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.timer = 0.0
                if self.line + 1 < len(LINES):
                    self.line += 1
                    self.phase = 0
                else:
                    self.done = True
        if self.done and not self._advanced:
            self._advanced = True
            self.app.switch_scene("title")

    def draw(self, surface) -> None:
        surface.blit(self.bg, (0, 0))
        w, h = surface.get_size()
        title, sub, color, size = LINES[self.line]
        a = int(self.alpha)
        tint = tuple(min(255, c * a // 255) for c in color)
        sub_c = tuple(min(255, c * a // 255) for c in (150, 165, 190))
        draw_text(surface, self.app.fonts, title, (w // 2, h // 2 - 14),
                  size=size, color=tint, center=True, bold=True)
        draw_text(surface, self.app.fonts, sub, (w // 2, h // 2 + 26),
                  size=17, color=sub_c, center=True)
        footer = tuple(min(255, c * a // 255) for c in (110, 125, 150))
        draw_text(surface, self.app.fonts, rlprojects.stage_line(),
                  (w // 2, h - 34), size=12, color=footer, center=True)
        draw_text(surface, self.app.fonts, rlprojects.COPYRIGHT,
                  (w // 2, h - 18), size=11, color=footer, center=True)
