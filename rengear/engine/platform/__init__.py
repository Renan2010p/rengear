"""The platform seam.

This is the **only** module allowed to name a concrete backend.  The rest of
the engine imports :class:`Backend`, :class:`Key`, :class:`Event` and friends
from here, never from ``pygame_backend`` directly, so selecting a different
backend is a one-line change here.
"""

from __future__ import annotations

import os

from .base import (Backend, Event, EventType, Key, SoundHandle, WindowConfig)


def create_backend() -> Backend:
    """Return the concrete backend named by ``RENGEAR_BACKEND`` (default pygame)."""
    name = os.environ.get("RENGEAR_BACKEND", "pygame").lower()
    if name == "pygame":
        from .pygame_backend import create

        return create()
    raise ValueError(f"unknown backend: {name!r}")


__all__ = [
    "Backend", "Event", "EventType", "Key", "SoundHandle", "WindowConfig",
    "create_backend",
]
