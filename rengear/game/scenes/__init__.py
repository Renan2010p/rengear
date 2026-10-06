"""Scene registration — the one place that wires game states to the registry."""

from __future__ import annotations

from .choose import ChooseScene
from .pause import PauseScene
from .race import RaceScene
from .results import ResultsScene
from .splash import SplashScene
from .title import TitleScene


def register_scenes(registry) -> None:
    registry.register("scene", "splash", SplashScene)
    registry.register("scene", "title", TitleScene)
    registry.register("scene", "choose", ChooseScene)
    registry.register("scene", "race", RaceScene)
    registry.register("scene", "pause", PauseScene)
    registry.register("scene", "results", ResultsScene)
