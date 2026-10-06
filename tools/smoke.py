"""Headless smoke test: drive a whole race with an autopilot.

Useful in CI and on machines without a display::

    python -m tools.smoke
    python -m tools.smoke --track night --car vulcan
    python -m tools.smoke --split --car comet --p2 dune
"""

from __future__ import annotations

import argparse
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from rengear.engine.app import App  # noqa: E402
from rengear.game import app_config, register_content  # noqa: E402


def make_autopilot(race):
    """Throttle flat out, burn nitro, and hold a lane (P1 left, P2 right)."""
    def held_profile(profile, action: str) -> bool:
        target = None
        for view in race.views:
            if view.profile is profile:
                target = view.player
                break
        player = target if target is not None else race.players[0]
        lane = -0.4 if player is race.players[0] else 0.4
        if action == "accelerate":
            return not player.finished
        if action == "nitro":
            return player.nitro > 0.35 and not player.finished
        if action == "left":
            return player.offset > lane + 0.06
        if action == "right":
            return player.offset < lane - 0.06
        return False
    return held_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="RENGEAR headless race smoke test")
    parser.add_argument("--track", default="coast")
    parser.add_argument("--car", default="comet")
    parser.add_argument("--p2", default="dune", help="player 2 car when --split")
    parser.add_argument("--split", action="store_true", help="two-player split screen")
    parser.add_argument("--frames", type=int, default=40000)
    args = parser.parse_args()

    app = App(app_config())
    register_content(app)
    app.scenes.switch("race", transition=False, car=args.car, track=args.track,
                      car2=(args.p2 if args.split else None))
    race = app.scenes.current
    race.countdown = 0.0
    race.state = "racing"
    app.input.held_profile = make_autopilot(race)

    finished = None
    for frame in range(args.frames):
        app.scenes.update(1.0 / 60.0)
        if app.scenes.current.__class__.__name__ == "ResultsScene":
            finished = frame
            break

    mode = "2P split" if args.split else "1P"
    print(f"track={args.track} car={args.car} mode={mode}")
    if finished is None:
        print(f"  did not finish in {args.frames} frames")
        return 1
    print(f"  finished in {finished} frames ({finished / 60.0:.1f}s)")
    for car in sorted(race.cars, key=lambda c: c.place):
        tag = "  <- you" if car.is_player else ""
        time_text = f"{car.finish_time:7.2f}s" if car.finished else "    DNF"
        print(f"  {car.place}. {car.name:<10} {time_text}{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
