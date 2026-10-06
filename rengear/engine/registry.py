"""A tiny content registry used to keep the game data-driven.

Everything that is "content" (tracks, cars, scenes) is registered under a
``kind``/``name`` pair.  Systems resolve content by name at runtime, which
means new content can be added purely by registering it -- no core file needs
to change.  This is the backbone of the modding story.
"""

from __future__ import annotations

from typing import Any, Dict


class Registry:
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    # -- registration -----------------------------------------------------
    def register(self, kind: str, name: str, obj: Any = None):
        """Register ``obj`` under ``kind/name``.

        Can be used directly or as a decorator::

            @registry.register("scene", "title")
            def make_title(app): ...
        """
        def _store(value: Any) -> Any:
            bucket = self._data.setdefault(kind, {})
            if name in bucket:
                raise KeyError(f"duplicate {kind}:{name}")
            bucket[name] = value
            return value

        if obj is not None:
            return _store(obj)
        return _store

    # -- lookup -----------------------------------------------------------
    def get(self, kind: str, name: str) -> Any:
        try:
            return self._data[kind][name]
        except KeyError as exc:  # pragma: no cover - developer feedback
            known = ", ".join(sorted(self._data.get(kind, {}))) or "<none>"
            raise KeyError(f"{kind}:{name!r} not registered (known: {known})") from exc

    def has(self, kind: str, name: str) -> bool:
        return name in self._data.get(kind, {})

    def names(self, kind: str):
        return sorted(self._data.get(kind, {}))


#: The single global registry used by the game.  A fresh one is created for the
#: test-suite via :func:`make_registry`.
REGISTRY = Registry()


def make_registry() -> Registry:
    return Registry()
