"""Generic, game-agnostic engine layer.

Nothing in ``rengear.engine`` knows about RENGEAR's content (tracks, cars,
scenes…).  The game layer builds on top of these primitives.  This split is
what makes the project modular: the engine can be reused for other games and
the game can be extended without touching the engine.

Inside the engine there is a second split: ``rengear.engine.platform`` is the
only code that touches the OS (window, events, keys, audio, fonts, files), and
the rest of the engine is pure.  That is what keeps a future port cheap.
"""

from __future__ import annotations

__all__ = ["engine"]
