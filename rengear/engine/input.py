"""Action-based input, decoupled from any keyboard library.

Gameplay code never touches raw key constants: it asks for semantic actions
(``left``, ``accelerate``, ``nitro``...).  Keys are logical
:class:`~rengear.engine.platform.Key` values, so the same bindings work on
SDL, a console pad or a browser backend.  Several key sets can be active at
once (arrows *and* WASD by default).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

from .platform import Backend, Key

DEFAULT_PROFILE: Dict[str, List[Key]] = {
    "left": [Key.LEFT, Key.A],
    "right": [Key.RIGHT, Key.D],
    "accelerate": [Key.UP, Key.W],
    "brake": [Key.DOWN, Key.S],
    "nitro": [Key.Z, Key.SPACE],
    "pause": [Key.RETURN, Key.ESCAPE, Key.P],
    "confirm": [Key.RETURN, Key.Z, Key.SPACE],
    "cancel": [Key.ESCAPE, Key.X],
    "restart": [Key.R],
}


class InputMap:
    def __init__(self, backend: Optional[Backend] = None,
                 profile: Dict[str, Iterable[Key]] | None = None) -> None:
        self.backend = backend
        self.bindings: Dict[str, List[Key]] = {}
        self.held_keys: Set[Key] = set()
        self._prev_keys: Set[Key] = set()
        self.load(profile or DEFAULT_PROFILE)

    def load(self, profile: Dict[str, Iterable[Key]]) -> None:
        self.bindings = {action: list(keys) for action, keys in profile.items()}

    def bind(self, action: str, *keys: Key) -> None:
        self.bindings[action] = list(keys)

    # -- frame lifecycle --------------------------------------------------
    def begin_frame(self) -> None:
        self._prev_keys = self.held_keys
        if self.backend is None:
            return
        self.held_keys = set(self.backend.pressed_keys())

    def end_frame(self) -> None:
        pass

    # -- queries ----------------------------------------------------------
    def held(self, action: str) -> bool:
        return any(k in self.held_keys for k in self.bindings.get(action, ()))

    def pressed(self, action: str) -> bool:
        keys = self.bindings.get(action, ())
        return any(k in self.held_keys and k not in self._prev_keys for k in keys)

    def released(self, action: str) -> bool:
        keys = self.bindings.get(action, ())
        return any(k not in self.held_keys and k in self._prev_keys for k in keys)

    def axis(self, negative: str = "left", positive: str = "right") -> float:
        return (1.0 if self.held(positive) else 0.0) - (1.0 if self.held(negative) else 0.0)

    def held_profile(self, profile: Dict[str, Iterable], action: str) -> bool:
        """Like :meth:`held` but against an arbitrary profile.

        Used for local multiplayer, where each player has their own key set.

        ```python
        if input.held_profile(P2_KEYS, "accelerate"):
            ...
        ```
        """
        return any(k in self.held_keys for k in profile.get(action, ()))
