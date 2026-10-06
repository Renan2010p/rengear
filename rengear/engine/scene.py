"""Scene stack with fades.

Scenes are looked up by name in the global registry, so a new game state is
added by registering a factory -- the manager never changes.
"""

from __future__ import annotations

from typing import Callable, Optional


class Scene:
    """Base class for every game state (title, race, results, …)."""

    def __init__(self, app) -> None:
        self.app = app

    # -- lifecycle hooks --------------------------------------------------
    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        pass

    # -- convenience ------------------------------------------------------
    @property
    def render_size(self):
        return self.app.render_size


class FadeTransition:
    def __init__(self, duration: float = 0.35, color=(0, 0, 0)) -> None:
        self.duration = duration
        self.color = color
        self.time = 0.0
        self.switched = False
        self.target: Optional[Callable[[], None]] = None

    @property
    def done(self) -> bool:
        return self.time >= self.duration * 2

    def alpha(self) -> int:
        half = self.duration
        if self.time < half:
            return int(255 * (self.time / half))
        return int(255 * (1 - (self.time - half) / half))


class SceneManager:
    def __init__(self, app) -> None:
        self.app = app
        self.current: Optional[Scene] = None
        self._transition: Optional[FadeTransition] = None

    def switch(self, name: str, transition: bool = True, **kwargs) -> None:
        if self._transition is not None:
            return

        def _do() -> None:
            factory = self.app.registry.get("scene", name)
            if self.current is not None:
                self.current.on_exit()
            self.current = factory(self.app, **kwargs)
            self.current.on_enter()

        if not transition or self.current is None:
            _do()
            return
        fade = FadeTransition(0.35)
        fade.target = _do
        self._transition = fade

    def set_current(self, scene: Scene, call_enter: bool = True) -> None:
        """Swap to an existing scene instance (used for pause/resume)."""
        if self.current is not None and self.current is not scene:
            self.current.on_exit()
        self.current = scene
        if call_enter and scene is not None:
            scene.on_enter()

    # -- frame ------------------------------------------------------------
    def handle_event(self, event) -> None:
        if self.current is not None:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        if self._transition is not None:
            self._transition.time += dt
            if (not self._transition.switched
                    and self._transition.time >= self._transition.duration):
                self._transition.switched = True
                if self._transition.target:
                    self._transition.target()
            if self._transition.done:
                self._transition = None
        if self.current is not None:
            self.current.update(dt)

    def draw(self, surface) -> None:
        if self.current is not None:
            self.current.draw(surface)
        if self._transition is not None:
            overlay = self.app.backend.overlay(
                surface.get_size(),
                (*self._transition.color, self._transition.alpha()),
            )
            surface.blit(overlay, (0, 0))
