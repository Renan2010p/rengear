# Contributing to RENGEAR

Thanks for wanting to help! RENGEAR is a small, source-only arcade racer. The
best contributions are new tracks, cars, props, gameplay polish and ports.

## Getting started

```bash
git clone git@github.com:Renan2010p/rengear.git
cd rengear
python -m pip install -r requirements.txt
python main.py
```

## The one rule

Game code never touches the OS directly, and the engine never knows about
RENGEAR's content:

```
rengear/engine/   game-agnostic primitives (reusable)
rengear/game/     RENGEAR's content and rules
```

- Put OS calls (window, events, keys, audio, files) only in
  `rengear/engine/platform/`.
- Gameplay names logical `Key`/`Event` values, never `pygame.K_*`.
- New content (a track, a car, a prop) is **data**, not engine changes — see
  [docs/TRACKS.md](docs/TRACKS.md).
- The road renderer and the car physics talk in **track space**
  (`z`, `offset`, `speed`), not pixels.

Keeping this rule is what makes ports cheap; please do not break it.

## Tests and tools

```bash
python -m tests.test_engine            # unit + integration tests (headless)
python -m tools.smoke                  # drive one solo race
python -m tools.smoke --split          # drive one 2-player race
python -m tools.render_frame --track night --out frame.png
python -m tools.package                # build a release zip (needs PyInstaller)
```

All tests must pass headless. If you add gameplay rules, add a test — most
things (geometry, tracks, physics, collisions, gearbox) are pure and easy to
test without a display.

## Code style

- Python 3.10+, `from __future__ import annotations` in every module.
- Type hints and short, intention-revealing docstrings.
- Keep modules small and single-purpose (`road.py`, `car.py`, `tracks.py`…).
- Data tables live in `rengear/game/config.py`; behaviour lives in the
  systems/scenes.

## Assets

**Never** add ripped or third-party assets. Sprites are drawn procedurally in
`rengear/game/art.py` and audio is synthesised in `rengear/engine/audio.py`, so
the project stays 100% original and GPL-clean. See
[docs/LEGAL.md](docs/LEGAL.md).

## Licence

By contributing you agree that your work is released under the project's
licence, **GPL-3.0-or-later**.
