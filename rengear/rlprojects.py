"""RL PROJECTS — studio identity and the RENGEAR development roadmap.

This module is the single source of truth for the studio branding and for the
development stages the game follows.  Import from here instead of hard-coding
names.
"""

from __future__ import annotations

# -- studio -----------------------------------------------------------------
STUDIO = "RL PROJECTS"
COPYRIGHT = "Copyright (C) 2026 Renan Lucas Vieira Hilário"

#: engine that powers the current build
ENGINE = "Rengear engine"

# -- roadmap ----------------------------------------------------------------
#: The stage the code in this repository currently represents.
STAGE = 1

STAGES = {
    1: {
        "name": "Prototype",
        "tech": "Python + pygame",
        "goal": "Fast iteration on the pseudo-3D road, game feel and tracks.",
    },
    2: {
        "name": "Rewrite",
        "tech": "Zig + Neko engine",
        "goal": "Port the game so it shares the studio's engine.",
    },
    3: {
        "name": "Release",
        "tech": "all platforms",
        "goal": "Ship everywhere: Linux, Windows, macOS, web and consoles.",
    },
}


def stage_line() -> str:
    """Short human-readable description of the current stage."""
    info = STAGES[STAGE]
    return f"{info['tech']} · stage {STAGE}/{len(STAGES)}"
