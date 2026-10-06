"""Cars: the player's physics and the rival AI.

A car exists in **track space**: ``z`` is the absolute distance travelled along
the (looped) track, ``offset`` is its lane position in road-width units
(``0`` is the centre line, ``±1`` the road edges) and ``speed`` is in world
units per second.  The road renderer turns that back into pixels.

This keeps gameplay and rendering completely decoupled: the AI knows nothing
about the projection and the renderer knows nothing about the AI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import config as C
from .road import camera_depth, increase, limit, overlap, Track

Color = Tuple[int, int, int]

#: distance from the camera to the player's car along the track
PLAYER_Z = C.CAMERA_HEIGHT * camera_depth()

#: collision half-widths, in road-width units
PLAYER_W = 0.34
CAR_W = 0.36

#: how close (world units) a rival must be *ahead of the player's car* to count
#: as a bump — roughly one car length, not the whole camera-to-car distance
CAR_GAP = PLAYER_Z * 0.62


@dataclass
class Controls:
    accelerate: bool = False
    brake: bool = False
    left: bool = False
    right: bool = False
    nitro: bool = False


@dataclass
class Car:
    name: str
    color: Color
    accent: Color
    power: float = 1.0
    top: float = 1.0
    grip: float = 1.0
    nitro_factor: float = 1.0

    z: float = 0.0
    offset: float = 0.0
    speed: float = 0.0
    lap: int = 0
    finished: bool = False
    finish_time: float = 0.0
    place: int = 1
    is_player: bool = False

    @property
    def max_speed(self) -> float:
        return C.MAX_SPEED * self.top

    @property
    def speed_pct(self) -> float:
        return self.speed / self.max_speed if self.max_speed else 0.0

    @property
    def gear(self) -> int:
        """Current gear of the automatic box (1..GEARS)."""
        return max(1, min(C.GEARS, int(self.speed_pct * C.GEARS) + 1))

    @property
    def rpm(self) -> float:
        """Position within the current gear (0 at the shift, 1 at the limiter)."""
        return max(0.0, min(1.0, self.speed_pct * C.GEARS - (self.gear - 1)))

    def reset(self, z: float, offset: float) -> None:
        self.z = z
        self.offset = offset
        self.speed = 0.0
        self.lap = 0
        self.finished = False
        self.finish_time = 0.0
        self.place = 1


# ---------------------------------------------------------------------------
# player
# ---------------------------------------------------------------------------

@dataclass
class Player(Car):
    is_player: bool = True
    nitro: float = 1.0
    bump_timer: float = 0.0
    crash_timer: float = 0.0
    steer_visual: float = 0.0
    lap_time: float = 0.0
    lap_times: List[float] = field(default_factory=list)
    best_lap: float = 0.0

    def reset(self, z: float, offset: float) -> None:
        super().reset(z, offset)
        self.nitro = 1.0
        self.bump_timer = 0.0
        self.crash_timer = 0.0
        self.steer_visual = 0.0
        self.lap_time = 0.0
        self.lap_times = []
        self.best_lap = 0.0

    # -- per-frame ---------------------------------------------------------
    def update(self, dt: float, track: Track, controls: Controls) -> dict:
        events = {"bump": False, "crash": False, "wrapped": False}
        if self.finished:
            controls = Controls(brake=True)

        length = track.length
        prev_z = self.z
        seg = track.find_segment(self.z + PLAYER_Z)
        speed_pct = self.speed / self.max_speed if self.max_speed else 0.0

        # steering: at top speed you can cross the road in ~1 s
        dx = dt * C.STEER_RATE * speed_pct * self.grip
        if controls.left:
            self.offset -= dx
            self.steer_visual = max(-1.0, self.steer_visual - dt * 8)
        elif controls.right:
            self.offset += dx
            self.steer_visual = min(1.0, self.steer_visual + dt * 8)
        else:
            self.steer_visual *= max(0.0, 1.0 - dt * 8)

        # centrifugal force pushes you out of the curve
        self.offset -= dx * speed_pct * seg.curve * C.CENTRIFUGAL

        # engine (lower gears pull harder, like a real box)
        if controls.accelerate:
            gear_punch = 1.0 + 0.4 * (1.0 - (self.gear - 1) / max(1, C.GEARS - 1))
            self.speed += C.ACCEL * self.power * gear_punch * dt
        elif controls.brake:
            self.speed += C.BRAKING * dt
        else:
            self.speed += C.DECEL * dt

        # nitro boost
        if (controls.nitro and self.nitro > 0.0
                and self.speed > self.max_speed * 0.2):
            self.speed += C.ACCEL * 1.6 * self.nitro_factor * dt
            self.nitro = max(0.0, self.nitro - C.NITRO_DRAIN * dt)
        else:
            self.nitro = min(1.0, self.nitro + C.NITRO_RECHARGE * dt)

        # going off-road caps you at a crawl
        off_road = abs(self.offset) > 1.0
        if off_road:
            limit_speed = self.max_speed * C.OFF_ROAD_MAX
            if self.speed > limit_speed:
                self.speed = max(limit_speed, self.speed + C.OFF_ROAD_DECEL * dt)

        # top speed: nitro can briefly exceed it, otherwise it is capped
        cap = self.max_speed * (C.NITRO_MULT if (controls.nitro and self.nitro > 0) else 1.0)
        self.speed = limit(self.speed, 0.0, cap)

        # advance
        self.z += self.speed * dt
        if self.z >= length and prev_z < length:
            events["wrapped"] = True
        while self.z >= length:
            self.z -= length
            self.lap += 1
        while self.z < 0:
            self.z += length

        self.offset = limit(self.offset, -3.0, 3.0)
        self.lap_time += dt
        if self.bump_timer > 0:
            self.bump_timer -= dt
        if self.crash_timer > 0:
            self.crash_timer -= dt
        return events

    # -- helpers -----------------------------------------------------------
    def slow_to(self, speed: float) -> None:
        self.speed = min(self.speed, speed)

    def hit_wall(self, speed: float) -> None:
        self.slow_to(speed * 0.35)
        self.bump_timer = 0.18

    def collide_with(self, other: Car, length: float) -> bool:
        """Handle a bump with ``other``.

        The player's car does not sit at the camera position: it is
        ``PLAYER_Z`` world units ahead of it, exactly like the rendered sprite.
        Collisions must therefore compare the rival against ``self.z +
        PLAYER_Z`` — otherwise a rival being *overtaken* (behind the car but
        ahead of the camera) is mistaken for one in front and the player is
        yanked backwards.

        On contact the faster car is simply slowed below the other; there is no
        positional teleport, so the faster car falls in behind naturally.
        """
        gap = CAR_GAP
        player_car = self.z + PLAYER_Z
        forward = (other.z - player_car) % length   # 0..gap means just ahead
        if forward > gap:
            return False
        if not overlap(self.offset, PLAYER_W, other.offset, CAR_W, 0.85):
            return False
        if self.speed > other.speed:
            self.slow_to(other.speed * 0.9)
            self.bump_timer = 0.2
            self.crash_timer = 0.35
            return True
        return False


# ---------------------------------------------------------------------------
# rivals
# ---------------------------------------------------------------------------

@dataclass
class Rival(Car):
    skill: float = 1.0
    aggression: float = 1.0
    wobble: float = 0.0
    target_offset: float = 0.0
    _t: float = 0.0

    def update(self, dt: float, track: Track, player: Optional[Player] = None,
               cars: Optional[List[Car]] = None) -> None:
        length = track.length
        if self.finished:
            # coast gently to a stop after the chequered flag
            self.speed = max(0.0, self.speed + C.DECEL * 2.0 * dt)
            self.z += self.speed * dt
            while self.z >= length:
                self.z -= length
            return
        self._t += dt
        seg = track.find_segment(self.z + PLAYER_Z)

        # slow into curves based on skill
        curve = seg.curve
        target = self.max_speed * self.skill
        target *= 1.0 - min(0.30, abs(curve) * 0.045 * (2.0 - self.skill))
        if self.speed < target:
            self.speed += C.ACCEL * 0.85 * dt
        else:
            self.speed += C.DECEL * 0.6 * dt
        self.speed = limit(self.speed, 0.0, self.max_speed)

        # wander a little and hug the inside of a curve
        self.wobble += dt * (0.7 + self.aggression * 0.4)
        drift = (-curve * 0.06 * self.aggression) + (self.wobble % 2.0 - 1.0) * 0.15
        self.offset += drift * dt
        if player is not None:
            # try to stay on the road, and lean away from a nearby player
            if abs(self.offset) > 0.85:
                self.offset += (-0.5 if self.offset > 0 else 0.5) * dt
            dz = player.z - self.z
            if -PLAYER_Z * 0.8 < dz < PLAYER_Z * 0.8 and abs(player.offset - self.offset) < 0.5:
                self.offset += (0.4 if player.offset > self.offset else -0.4) * dt
        self.offset = limit(self.offset, -1.1, 1.1)

        self.z += self.speed * dt
        while self.z >= length:
            self.z -= length
            self.lap += 1
