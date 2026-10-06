"""Track piece scripts — the editable definition of every circuit.

A track is just a function that appends road pieces to a :class:`Track`.  Each
piece is ``add_road(enter, hold, leave, curve, hill)`` in segment counts:

* ``curve`` > 0 bends right, < 0 bends left, 0 is straight.
* ``hill`` > 0 climbs, < 0 descends (in segment-height units).

That is the whole level format.  Tweak the numbers, hit run, drive it.
"""

from __future__ import annotations

from typing import Callable, Dict

from .road import Track


def _hills(track: Track, pattern) -> None:
    for length, curve, hill in pattern:
        track.add_road(length, length, length, curve, hill)


def coast(t: Track) -> None:
    t.add_straight(50)
    _hills(t, [
        (30, 3, 20), (30, 0, 0), (30, -3, -20),
        (40, -4, 0), (40, 4, 0),
        (30, 0, 30), (30, 5, 0), (30, 0, -30),
        (50, -5, 10), (50, 0, -10),
        (30, 2, 0), (30, -2, 0), (30, 0, 0),
        (40, 6, 20), (40, -6, -20),
    ])
    t.add_straight(70)


def dusk(t: Track) -> None:
    _hills(t, [
        (35, -3, 25), (35, 0, -15), (35, 3, 15),
        (45, 5, 0), (25, 0, 35), (45, -5, -35),
        (30, 0, 0), (30, 4, 0), (30, -4, 0),
        (35, 0, -25), (35, 3, 25),
        (55, -6, 0), (30, 0, 0), (55, 6, 0),
    ])
    t.add_straight(60)


def pine(t: Track) -> None:
    t.add_straight(40)
    _hills(t, [
        (25, 2, 35), (25, -2, -35), (25, 4, 30),
        (30, -4, -30), (30, 0, 0),
        (40, -5, 15), (40, 5, -15),
        (25, 3, 0), (25, -3, 0),
        (35, 0, 40), (35, 0, -40),
        (45, 6, 0), (45, -6, 0),
        (30, 2, 20), (30, -2, -20),
    ])
    t.add_straight(50)


def dunes(t: Track) -> None:
    t.add_straight(80)
    _hills(t, [
        (45, 0, 30), (45, 4, -30),
        (35, -4, 0), (35, 4, 0),
        (50, 0, -35), (50, 3, 35),
        (30, 6, 0), (30, -6, 0),
        (40, 0, 0), (40, -3, 25), (40, 3, -25),
    ])
    t.add_straight(60)


def night(t: Track) -> None:
    t.add_straight(40)
    _hills(t, [
        (25, 4, 0), (25, -4, 0),
        (35, 0, 20), (35, 5, -10), (35, -5, 10),
        (20, 0, 0), (20, 6, 0), (20, -6, 0),
        (40, -3, 15), (40, 3, -15),
        (30, 0, 0), (30, 4, 25), (30, -4, -25),
        (45, 0, 0),
    ])
    t.add_straight(50)


def polar(t: Track) -> None:
    t.add_straight(45)
    _hills(t, [
        (30, -4, 30), (30, 4, -30),
        (40, 0, 40), (40, 0, -40),
        (35, 5, 20), (35, -5, -20),
        (25, 0, 0), (25, 3, 35), (25, -3, -35),
        (50, -6, 0), (50, 6, 0),
    ])
    t.add_straight(55)


TRACK_SCRIPTS: Dict[str, Callable[[Track], None]] = {
    "coast": coast,
    "dusk": dusk,
    "pine": pine,
    "dunes": dunes,
    "night": night,
    "polar": polar,
}
