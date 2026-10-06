"""Render one frame of RENGEAR to a PNG without a display.

Handy for previewing the road trick, a palette or a track script::

    python -m tools.render_frame --track night --out /tmp/rengear.png
    python -m tools.render_frame --track dunes --z 40000 --speed 0.9
"""

from __future__ import annotations

import argparse
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from rengear.engine.app import App  # noqa: E402
from rengear.game import app_config, register_content  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="render a RENGEAR frame to PNG")
    parser.add_argument("--track", default="coast")
    parser.add_argument("--car", default="spark")
    parser.add_argument("--p2", default=None,
                        help="player 2 car; enables split-screen when set")
    parser.add_argument("--out", default="rengear_frame.png")
    parser.add_argument("--z", type=float, default=0.0,
                        help="position along the track in world units")
    parser.add_argument("--offset", type=float, default=0.0,
                        help="lane offset (-1..1 is on the road)")
    parser.add_argument("--speed", type=float, default=0.8,
                        help="speed as a fraction of top speed")
    parser.add_argument("--steer", type=float, default=0.0,
                        help="steering visual, -1 (left) .. 1 (right)")
    args = parser.parse_args()

    app = App(app_config())
    register_content(app)
    app.scenes.switch("race", transition=False, car=args.car, track=args.track,
                      car2=args.p2)
    race = app.scenes.current
    race.countdown = 0.0
    race.state = "racing"
    race.player.z = args.z % race.track.length
    race.player.offset = args.offset
    race.player.speed = race.player.max_speed * args.speed
    race.player.steer_visual = args.steer
    if args.p2 is not None and len(race.players) > 1:
        p2 = race.players[1]
        p2.z = (args.z + 1800.0) % race.track.length
        p2.offset = -args.offset
        p2.speed = p2.max_speed * args.speed
    race.elapsed = 1.0

    app.canvas.fill((8, 8, 14))
    race.draw(app.canvas)
    pygame.image.save(app.canvas, args.out)
    print(f"wrote {args.out} ({args.track}, z={int(args.z)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
