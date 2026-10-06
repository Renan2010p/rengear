"""JSON persistence: a save directory and simple key/value files."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class SaveManager:
    def __init__(self, directory: str) -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def path(self, name: str) -> str:
        return os.path.join(self.directory, name)

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            with open(self.path(name), "r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, dict) else None
        except (OSError, ValueError):
            return None

    def save(self, data: Dict[str, Any], name: str) -> bool:
        try:
            with open(self.path(name), "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, sort_keys=True)
            return True
        except OSError:  # pragma: no cover - disk errors
            return False
