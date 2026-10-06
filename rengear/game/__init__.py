"""RENGEAR gameplay layer.

The package is split so content and rules live apart:

* ``config``  -> tunable constants, palette, cars and track themes
* ``tracks``  -> the editable track piece scripts
* ``road``    -> the pseudo-3D road trick (geometry + rendering)
* ``car``     -> player physics and rival AI
* ``art``     -> procedural, original artwork
* ``scenes``  -> game states (splash, title, choose, race, pause, results)

Adding a car or a track means editing data and registering content, never
touching the engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from rengear.engine.app import App

START_SCENE = "splash"


def app_config():
    from rengear.engine.app import AppConfig
    from .config import FPS, LOGICAL_H, LOGICAL_W, TITLE

    return AppConfig(
        title=TITLE,
        window_size=(LOGICAL_W * 2, LOGICAL_H * 2),
        render_size=(LOGICAL_W, LOGICAL_H),
        fps=FPS,
    )


def register_content(app: "App") -> None:
    """Register all built-in content (idempotent)."""
    if app.runtime.get("content_registered"):
        return
    from .scenes import register_scenes

    register_scenes(app.registry)

    # restore the persisted sound preference before the first scene runs
    sound = app.get_setting("sound", True)
    app.audio.set_enabled(bool(sound))
    app.runtime["content_registered"] = True
