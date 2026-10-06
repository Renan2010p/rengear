# Changelog

All notable changes to RENGEAR are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/) and the project uses
semantic-ish versions.

## [0.1.0] — 2026-10-06

### Added

- **The pseudo-3D road trick** — segment-based projection with curves, hills,
  fog and roadside props (`rengear/game/road.py`).
- **Six tracks** with distinct palettes and scenery: Nara Coast, Dusk Canyon,
  Pine Pass, Crimson Dunes, Midnight City and Polar Ridge.
- **Four cars** (Spark, Comet, Vulcan, Dune) with power / top speed / grip /
  nitro differences.
- **Three rival AI cars** with curve braking and lane behaviour.
- **Top Gear-style dashboard** — analog speedometer and tachometer with
  needles, a six-speed automatic gearbox with a rev limiter, lap / time /
  position and nitro.
- **Cars that turn** — the player's car leans with the steering and rivals
  bank through corners; props and cars follow the road through curves.
- **Local 2-player split screen** — vertical split, each player with their own
  camera and dashboard, head to head over three laps.
- **Arcade race rules** — countdown, three laps, best-lap saving, off-road
  penalties, wall and car collisions, results screen.
- **Procedural art and audio** — zero third-party assets.
- **Reusable engine layer** with a platform seam
  (`rengear/engine/platform`).
- **Tests and tools** — headless unit/integration tests, a race smoke test, a
  frame renderer and a PyInstaller packaging script.
- **GitHub Actions** — CI (tests + smoke) and a release workflow that builds
  Windows and Linux `.zip` packages.

[0.1.0]: https://github.com/Renan2010p/rengear/releases/tag/v0.1.0
