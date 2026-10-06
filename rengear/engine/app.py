"""Application shell: fixed-step game loop and shared services.

The shell is deliberately thin: window creation, the event pump, presentation
and timing all go through :mod:`rengear.engine.platform`, so the loop is the
same no matter which backend runs it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Tuple

from .audio import Audio
from .input import InputMap
from .platform import EventType, WindowConfig, create_backend
from .registry import REGISTRY, Registry
from .save import SaveManager
from .scene import SceneManager
from .ui import Fonts


@dataclass
class AppConfig:
    title: str = "RENGEAR"
    window_size: Tuple[int, int] = (1024, 576)
    render_size: Tuple[int, int] = (512, 288)
    fps: int = 60


class App:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()

        # -- platform -----------------------------------------------------
        self.backend = create_backend()
        self.backend.init(WindowConfig(
            title=self.config.title,
            window_size=self.config.window_size,
            render_size=self.config.render_size,
            fps=self.config.fps,
        ))

        self.render_size = self.config.render_size
        self.canvas = self.backend.new_surface(*self.render_size, alpha=False)
        self.running = True
        self.time = 0.0

        # -- shared services ---------------------------------------------
        self.registry: Registry = REGISTRY
        self.fonts = Fonts(self.backend)
        self.audio = Audio(self.backend)
        self.audio.init()
        self.input = InputMap(self.backend)
        self.save = SaveManager(self.backend.user_data_dir("rengear"))
        self.scenes = SceneManager(self)
        self.runtime: Dict[str, object] = {}

        # persisted user settings (sound, difficulty, best laps, …)
        self._settings_path = os.path.join(self.save.directory, "settings.json")
        self.settings: Dict[str, object] = self._load_settings()

    # -- settings ---------------------------------------------------------
    def _load_settings(self) -> Dict[str, object]:
        try:
            with open(self._settings_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        self.settings[key] = value
        try:
            with open(self._settings_path, "w", encoding="utf-8") as fh:
                json.dump(self.settings, fh, indent=2)
        except OSError:
            pass

    # -- main loop --------------------------------------------------------
    def run(self, start_scene: str = "splash") -> None:
        self.scenes.switch(start_scene, transition=False)
        accumulator = 0.0
        fixed = 1.0 / self.config.fps
        while self.running:
            frame_time = min(self.backend.tick(self.config.fps), 0.1)
            self.input.begin_frame()

            for event in self.backend.poll_events():
                if event.type == EventType.QUIT:
                    self.running = False
                elif event.type == EventType.RESIZE and event.size:
                    self.backend.resize(event.size)
                else:
                    self.scenes.handle_event(event)

            accumulator += frame_time
            steps = 0
            while accumulator >= fixed and steps < 5:
                self.scenes.update(fixed)
                accumulator -= fixed
                steps += 1
                self.time += fixed
            if steps == 5:
                accumulator = 0.0

            self.canvas.fill((8, 8, 14))
            self.scenes.draw(self.canvas)
            self.backend.present(self.canvas)
            self.input.end_frame()

        self.backend.shutdown()

    def quit(self) -> None:
        self.running = False

    # -- scene helpers ----------------------------------------------------
    def switch_scene(self, name: str, transition: bool = True, **kwargs) -> None:
        self.scenes.switch(name, transition=transition, **kwargs)


def main() -> int:
    from rengear import game

    config = game.app_config()
    app = App(config)
    game.register_content(app)
    app.run(game.START_SCENE)
    return 0
