"""The pygame backend — the current concrete platform.

This is the *only* place the engine is allowed to talk to SDL/pygame for
window, events, timing, input, audio and fonts.  It implements
:class:`rengear.engine.platform.base.Backend`.

Rendering primitives (``pygame.draw``, ``Surface``) are re-exported as the
graphics backend; ``docs/PORTING.md`` maps each one to a future backend's
equivalent.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

import pygame

from .base import Backend, Event, EventType, Key, WindowConfig

# -- logical Key -> SDL key constant ------------------------------------------
_KEYMAP: Dict[Key, int] = {
    Key.LEFT: pygame.K_LEFT,
    Key.RIGHT: pygame.K_RIGHT,
    Key.UP: pygame.K_UP,
    Key.DOWN: pygame.K_DOWN,
    Key.A: pygame.K_a,
    Key.D: pygame.K_d,
    Key.W: pygame.K_w,
    Key.S: pygame.K_s,
    Key.Z: pygame.K_z,
    Key.X: pygame.K_x,
    Key.C: pygame.K_c,
    Key.V: pygame.K_v,
    Key.J: pygame.K_j,
    Key.K: pygame.K_k,
    Key.L: pygame.K_l,
    Key.P: pygame.K_p,
    Key.M: pygame.K_m,
    Key.Q: pygame.K_q,
    Key.R: pygame.K_r,
    Key.SPACE: pygame.K_SPACE,
    Key.RETURN: pygame.K_RETURN,
    Key.ESCAPE: pygame.K_ESCAPE,
    Key.TAB: pygame.K_TAB,
}
_SDL_TO_KEY = {sdl: key for key, sdl in _KEYMAP.items()}

_EVENT_TYPES = {
    pygame.QUIT: EventType.QUIT,
    pygame.KEYDOWN: EventType.KEYDOWN,
    pygame.KEYUP: EventType.KEYUP,
    pygame.VIDEORESIZE: EventType.RESIZE,
    pygame.MOUSEBUTTONDOWN: EventType.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP: EventType.MOUSEUP,
    pygame.MOUSEMOTION: EventType.MOUSEMOTION,
}


class PygameBackend(Backend):
    name = "pygame"

    def __init__(self) -> None:
        self.window = None
        self.window_size: Tuple[int, int] = (1024, 576)
        self._clock = None
        self._audio = False

    # -- lifecycle --------------------------------------------------------
    def init(self, config: WindowConfig) -> None:
        pygame.init()
        try:
            pygame.mixer.pre_init(22050, -16, 1, 256)
            pygame.mixer.init()
            self._audio = True
        except Exception:  # pragma: no cover - no audio device
            self._audio = False
        flags = pygame.RESIZABLE if config.resizable else 0
        self.window = pygame.display.set_mode(config.window_size, flags)
        self.window_size = config.window_size
        pygame.display.set_caption(config.title)
        self._clock = pygame.time.Clock()

    def shutdown(self) -> None:
        pygame.quit()

    # -- window -----------------------------------------------------------
    def set_caption(self, title: str) -> None:
        pygame.display.set_caption(title)

    def resize(self, size: Tuple[int, int]) -> None:
        flags = pygame.RESIZABLE
        if self.window is not None and self.window.get_flags() & pygame.FULLSCREEN:
            flags |= pygame.FULLSCREEN
        self.window = pygame.display.set_mode(size, flags)
        self.window_size = size

    def new_surface(self, width: int, height: int, alpha: bool = True):
        flags = pygame.SRCALPHA if alpha else 0
        return pygame.Surface((width, height), flags).convert_alpha() if alpha \
            else pygame.Surface((width, height)).convert()

    def overlay(self, size: Tuple[int, int], rgba):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(tuple(rgba))
        return surf

    def present(self, canvas) -> None:
        win_w, win_h = self.window.get_size()
        rw, rh = canvas.get_size()
        scale = max(1, min(win_w // rw, win_h // rh))
        scaled = pygame.transform.scale(canvas, (rw * scale, rh * scale))
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, ((win_w - rw * scale) // 2,
                                  (win_h - rh * scale) // 2))
        pygame.display.flip()

    # -- events & timing --------------------------------------------------
    def poll_events(self) -> List[Event]:
        out: List[Event] = []
        for ev in pygame.event.get():
            kind = _EVENT_TYPES.get(ev.type, EventType.OTHER)
            event = Event(type=kind, raw=ev)
            if kind in (EventType.KEYDOWN, EventType.KEYUP):
                event.key = _SDL_TO_KEY.get(ev.key)
            elif kind == EventType.RESIZE:
                event.size = tuple(ev.size)
            elif kind in (EventType.MOUSEBUTTONDOWN, EventType.MOUSEUP):
                event.pos = tuple(ev.pos)
                event.button = ev.button
            elif kind == EventType.MOUSEMOTION:
                event.pos = tuple(ev.pos)
            out.append(event)
        return out

    def tick(self, fps: int) -> float:
        return self._clock.tick(fps) / 1000.0

    # -- input ------------------------------------------------------------
    def pressed_keys(self) -> frozenset:
        pressed = pygame.key.get_pressed()
        return frozenset(key for key, sdl in _KEYMAP.items() if pressed[sdl])

    # -- fonts ------------------------------------------------------------
    def load_font(self, size: int, bold: bool = False):
        font = pygame.font.Font(None, size)
        font.set_bold(bold)
        return font

    # -- audio ------------------------------------------------------------
    def audio_ready(self) -> bool:
        return self._audio

    def make_sound(self, buffer: bytes):
        if not self._audio:
            return None
        try:
            return pygame.mixer.Sound(buffer=buffer)
        except Exception:  # pragma: no cover
            return None

    # -- files ------------------------------------------------------------
    def user_data_dir(self, app_name: str) -> str:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share")
        path = os.path.join(base, app_name)
        os.makedirs(path, exist_ok=True)
        return path


def create() -> PygameBackend:
    """Factory used by the platform seam."""
    return PygameBackend()
