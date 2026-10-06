"""The platform contract — RENGEAR's OS boundary.

This module is the *only* place the engine names the abstract platform API.
It never imports a concrete backend.  Everything a platform must supply is
described here; concrete backends live in sibling modules
(``pygame_backend`` today, a future console/web backend later) and implement
it.

The rule that keeps the core portable:

    ``rengear/engine/*`` (app, scenes, input, ui, audio, save) never touches
    the OS.  ``rengear/engine/platform/*`` does.

Game code talks in terms of :class:`Key` and :class:`Event`, never in terms of
a windowing library's constants.  A backend translates them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List, Optional, Protocol, Sequence, Tuple


class EventType(Enum):
    """Window/input events, decoupled from any library's numeric codes."""

    QUIT = auto()
    KEYDOWN = auto()
    KEYUP = auto()
    RESIZE = auto()
    MOUSEBUTTONDOWN = auto()
    MOUSEUP = auto()
    MOUSEMOTION = auto()
    OTHER = auto()


class Key(Enum):
    """Logical keys the game binds.

    Bindings, input maps and scenes use these names.  A backend maps each one
    to whatever the host platform calls it (SDL scancode, gamepad button, …).
    """

    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    A = auto()
    D = auto()
    W = auto()
    S = auto()
    Z = auto()
    X = auto()
    C = auto()
    V = auto()
    J = auto()
    K = auto()
    L = auto()
    P = auto()
    M = auto()
    Q = auto()
    R = auto()
    SPACE = auto()
    RETURN = auto()
    ESCAPE = auto()
    TAB = auto()


@dataclass
class Event:
    """A platform-neutral event.

    ``raw`` keeps the backend's original object for the rare cases that need
    it, but game code should only read the fields above.
    """

    type: EventType
    key: Optional[Key] = None
    size: Optional[Tuple[int, int]] = None
    pos: Optional[Tuple[int, int]] = None
    button: Optional[int] = None
    raw: Any = None


class SoundHandle(Protocol):
    """Opaque playable sound returned by a backend."""

    def play(self, loops: int = 0):  # pragma: no cover - protocol
        ...

    def stop(self) -> None:  # pragma: no cover - protocol
        ...

    def set_volume(self, value: float) -> None:  # pragma: no cover - protocol
        ...


@dataclass
class WindowConfig:
    """Everything a backend needs to open a window / framebuffer."""

    title: str = "RENGEAR"
    window_size: Tuple[int, int] = (1024, 576)
    render_size: Tuple[int, int] = (512, 288)
    fps: int = 60
    resizable: bool = True


class Backend:
    """The platform vtable.

    A backend subclasses this and overrides every method.  The engine only
    ever calls through this interface, so swapping pygame for an SDL3/web/
    console backend is a matter of implementing this class — the core does not
    change.
    """

    #: short identifier, e.g. ``"pygame"``
    name: str = "base"

    # -- lifecycle --------------------------------------------------------
    def init(self, config: WindowConfig) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError

    # -- window -----------------------------------------------------------
    def set_caption(self, title: str) -> None:
        raise NotImplementedError

    def resize(self, size: Tuple[int, int]) -> None:
        raise NotImplementedError

    def new_surface(self, width: int, height: int, alpha: bool = True):
        """Create an off-screen drawing target (a canvas or layer)."""
        raise NotImplementedError

    def overlay(self, size: Tuple[int, int], rgba: Sequence[int]):
        """Create a filled translucent surface for fades/overlays."""
        raise NotImplementedError

    def present(self, canvas) -> None:
        """Scale ``canvas`` to the window and flip buffers."""
        raise NotImplementedError

    # -- events & timing --------------------------------------------------
    def poll_events(self) -> List[Event]:
        raise NotImplementedError

    def tick(self, fps: int) -> float:
        """Block to the frame rate and return the elapsed seconds."""
        raise NotImplementedError

    # -- input ------------------------------------------------------------
    def pressed_keys(self) -> frozenset:
        """Return the set of :class:`Key` held this frame."""
        raise NotImplementedError

    # -- fonts ------------------------------------------------------------
    def load_font(self, size: int, bold: bool = False):
        raise NotImplementedError

    # -- audio ------------------------------------------------------------
    def audio_ready(self) -> bool:
        return False

    def make_sound(self, buffer: bytes) -> Optional[SoundHandle]:
        return None

    # -- files ------------------------------------------------------------
    def user_data_dir(self, app_name: str) -> str:
        """Per-user writable directory for saves and settings."""
        raise NotImplementedError
