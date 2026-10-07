"""The pseudo-3D road: construction, projection and rendering.

This module is the "trick of the tracks" that powers games like *OutRun* and
*Top Gear*.  The key idea:

* The track is a **straight list of segments** in memory.  Two numbers per
  segment create every illusion:
  - ``curve`` bends the road left/right, and
  - the segment's world ``y`` makes hills.
* Nothing ever actually rotates.  Each frame the segments ahead are projected
  onto the screen with a single perspective divide (``scale = depth / z``) and
  drawn back-to-front as flat trapezoids.  Curves are faked by accumulating a
  horizontal offset (``x += dx; dx += curve``); hills simply change each
  projected ``y``.
* Because ``p2`` of one segment is the ``p1`` of the next, the road is a
  continuous ribbon while staying trivially editable — a track is just a list
  of "enter / hold / leave" piece descriptors (see :mod:`rengear.game.tracks`).

Everything in this file is pure geometry plus pygame drawing; it knows nothing
about cars or scenes.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple

import pygame

from . import config as C


# ---------------------------------------------------------------------------
# math helpers
# ---------------------------------------------------------------------------

def ease_in(a: float, b: float, p: float) -> float:
    return a + (b - a) * p ** 2


def ease_out(a: float, b: float, p: float) -> float:
    return a + (b - a) * (1 - (1 - p) ** 2)


def ease_in_out(a: float, b: float, p: float) -> float:
    return a + (b - a) * (-math.cos(p * math.pi) / 2 + 0.5)


def interpolate(a: float, b: float, p: float) -> float:
    return a + (b - a) * p


def percent_remaining(n: float, total: float) -> float:
    return (n % total) / total


def increase(start: float, amount: float, max_value: float) -> float:
    result = start + amount
    while result >= max_value:
        result -= max_value
    while result < 0:
        result += max_value
    return result


def overlap(x1: float, w1: float, x2: float, w2: float, percent: float = 1.0) -> bool:
    half = percent / 2
    min1, max1 = x1 - w1 * half, x1 + w1 * half
    min2, max2 = x2 - w2 * half, x2 + w2 * half
    return not (max1 < min2 or min1 > max2)


def limit(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

class Point:
    """A road point in world, camera and screen space."""

    __slots__ = ("world_x", "world_y", "world_z",
                 "cam_x", "cam_y", "cam_z",
                 "scr_x", "scr_y", "scr_w")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.world_x = x
        self.world_y = y
        self.world_z = z
        self.cam_x = self.cam_y = self.cam_z = 0.0
        self.scr_x = self.scr_y = self.scr_w = 0.0


class Segment:
    __slots__ = ("index", "p1", "p2", "curve", "sprites", "fog", "looped")

    def __init__(self, index: int, p1: Point, p2: Point, curve: float) -> None:
        self.index = index
        self.p1 = p1
        self.p2 = p2
        self.curve = curve
        self.sprites: List[dict] = []
        self.fog = 0.0
        self.looped = False


class Track:
    """A closed loop of road segments with a visual theme and scenery."""

    def __init__(self, key: str, theme: dict) -> None:
        self.key = key
        self.theme = theme
        self.segments: List[Segment] = []

    # -- construction -----------------------------------------------------
    def _last_y(self) -> float:
        return self.segments[-1].p2.world_y if self.segments else 0.0

    def add_segment(self, curve: float, y: float) -> None:
        n = len(self.segments)
        p1 = Point(0, self._last_y(), n * C.SEGMENT_LENGTH)
        p2 = Point(0, y, (n + 1) * C.SEGMENT_LENGTH)
        self.segments.append(Segment(n, p1, p2, curve))

    def add_road(self, enter: int, hold: int, leave: int,
                 curve: float, y: float) -> None:
        start_y = self._last_y()
        end_y = start_y + y * C.SEGMENT_LENGTH
        total = enter + hold + leave
        for n in range(enter):
            self.add_segment(ease_in(0, curve, n / enter),
                             ease_in_out(start_y, end_y, n / total))
        for n in range(hold):
            self.add_segment(curve,
                             ease_in_out(start_y, end_y, (enter + n) / total))
        for n in range(leave):
            self.add_segment(ease_in_out(curve, 0, n / leave),
                             ease_in_out(start_y, end_y, (enter + hold + n) / total))

    def add_straight(self, num: int) -> None:
        self.add_road(num, num, num, 0.0, 0.0)

    def add_scenery(self, prop_names: Sequence[str],
                    rng: random.Random, density: float = 0.55) -> None:
        """Seed roadside props onto random segments on both sides."""
        for seg in self.segments:
            if rng.random() > density:
                continue
            for side in (-1, 1):
                if rng.random() > 0.62:
                    continue
                seg.sprites.append({
                    "name": rng.choice(prop_names),
                    "offset": side * rng.uniform(1.15, 2.1),
                    "scale": rng.uniform(0.75, 1.35),
                })

    # -- queries ----------------------------------------------------------
    @property
    def length(self) -> float:
        return len(self.segments) * C.SEGMENT_LENGTH

    def find_segment(self, z: float) -> Segment:
        return self.segments[int(z // C.SEGMENT_LENGTH) % len(self.segments)]

    def height_at(self, z: float) -> float:
        seg = self.find_segment(z)
        p = percent_remaining(z, C.SEGMENT_LENGTH)
        return interpolate(seg.p1.world_y, seg.p2.world_y, p)

    def curve_at(self, z: float) -> float:
        return self.find_segment(z).curve


def build_track(key: str) -> Track:
    """Build a :class:`Track` from the piece script registered for ``key``."""
    from .tracks import TRACK_SCRIPTS

    theme = C.TRACKS[key]
    track = Track(key, theme)
    rng = random.Random(hash(key) & 0xFFFF)
    TRACK_SCRIPTS[key](track)
    track.add_scenery(theme["props"], rng, density=0.42)

    # bottom out the loop: end at the height it began at, so the seam is flat
    track.add_road(40, 40, 40, 0.0, -track._last_y() / C.SEGMENT_LENGTH)
    track.segments[-1].p2.world_y = track.segments[0].p1.world_y
    return track


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------

def camera_depth(fov: float = C.FIELD_OF_VIEW) -> float:
    return 1.0 / math.tan((fov / 2.0) * math.pi / 180.0)


def project(point: Point, cam_x: float, cam_y: float, cam_z: float,
            depth: float, width: int, height: int, road_width: float) -> None:
    point.cam_x = point.world_x - cam_x
    point.cam_y = point.world_y - cam_y
    point.cam_z = point.world_z - cam_z
    scale = depth / max(point.cam_z, 0.01)
    point.scr_x = width / 2 + scale * point.cam_x * width / 2
    point.scr_y = height / 2 - scale * point.cam_y * height / 2
    point.scr_w = scale * road_width * width / 2


# ---------------------------------------------------------------------------
# renderer
# ---------------------------------------------------------------------------

class RoadRenderer:
    """Projects and paints a :class:`Track` for one frame."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.depth = camera_depth()
        self.player_z = C.CAMERA_HEIGHT * self.depth
        self.visible: List[Segment] = []
        self._fog_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self._scale_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._theme: dict = {}
        self._fog_color = (200, 200, 200)

    # -- fog --------------------------------------------------------------
    def _fog(self, color) -> pygame.Surface:
        surf = self._fog_cache.get(color)
        if surf is None:
            surf = pygame.Surface((self.width, self.height))
            surf.fill(color)
            self._fog_cache[color] = surf
        return surf

    # -- main -------------------------------------------------------------
    def render(self, surface: pygame.Surface, track: Track,
               player_x: float, position: float, player_y: float,
               ) -> List[Segment]:
        """Draw the road and return the segments drawn (near → far)."""
        width, height = self.width, self.height
        depth = self.depth
        theme = track.theme
        self._theme = theme
        self._fog_color = theme["sky"][1]
        road_w = C.ROAD_WIDTH
        base = track.find_segment(position)
        base_percent = percent_remaining(position, C.SEGMENT_LENGTH)
        track_length = track.length

        maxy = height
        x = 0.0
        dx = -(base.curve * base_percent)
        visible: List[Segment] = []

        cam_y = player_y + C.CAMERA_HEIGHT

        for n in range(C.DRAW_DISTANCE):
            seg = track.segments[(base.index + n) % len(track.segments)]
            seg.looped = seg.index < base.index
            # fog amount: 0 near → 1 far
            seg.fog = 1.0 - math.exp(-((n / C.DRAW_DISTANCE) ** 2) * C.FOG_DENSITY)

            cam_z = position - (track_length if seg.looped else 0)

            project(seg.p1, player_x * road_w - x, cam_y, cam_z,
                    depth, width, height, road_w)
            project(seg.p2, player_x * road_w - x - dx, cam_y, cam_z,
                    depth, width, height, road_w)

            x += dx
            dx += seg.curve

            # back-face / hill clipping
            if (seg.p1.cam_z <= depth
                    or seg.p2.scr_y >= seg.p1.scr_y
                    or seg.p2.scr_y >= maxy):
                continue

            self._render_segment(surface, seg)
            maxy = seg.p2.scr_y
            visible.append(seg)

        self.visible = visible
        return visible

    # -- one segment ------------------------------------------------------
    def _render_segment(self, surface: pygame.Surface, seg: Segment) -> None:
        theme = self._theme
        light = (seg.index // C.RUMBLE_LENGTH) % 2 == 0
        ground = theme["ground"][0 if light else 1]
        road = theme["road"][0 if light else 1]
        rumble = theme["rumble"][0 if light else 1]
        lane = theme["lane"]

        p1, p2 = seg.p1, seg.p2
        x1, y1, w1 = p1.scr_x, p1.scr_y, p1.scr_w
        x2, y2, w2 = p2.scr_x, p2.scr_y, p2.scr_w
        if y2 > y1:      # guard against tiny inversions
            y1, y2 = y2, y1

        width = self.width
        lanes = C.LANES
        r1 = w1 / max(6, 2 * lanes)
        r2 = w2 / max(6, 2 * lanes)
        l1 = w1 / max(12, 4 * lanes)
        l2 = w2 / max(12, 4 * lanes)

        band = pygame.Rect(0, int(y2), width, max(1, int(y1 - y2)))
        surface.fill(ground, band)

        # rumble strips
        pygame.draw.polygon(surface, rumble, [
            (x1 - w1 - r1, y1), (x1 - w1, y1), (x2 - w2, y2), (x2 - w2 - r2, y2)])
        pygame.draw.polygon(surface, rumble, [
            (x1 + w1 + r1, y1), (x1 + w1, y1), (x2 + w2, y2), (x2 + w2 + r2, y2)])

        # road surface
        pygame.draw.polygon(surface, road, [
            (x1 - w1, y1), (x1 + w1, y1), (x2 + w2, y2), (x2 - w2, y2)])

        # lane markers
        if lane:
            lane_w1 = w1 * 2 / lanes
            lane_w2 = w2 * 2 / lanes
            lx1 = x1 - w1 + lane_w1
            lx2 = x2 - w2 + lane_w2
            for _ in range(1, lanes):
                pygame.draw.polygon(surface, lane, [
                    (lx1 - l1 / 2, y1), (lx1 + l1 / 2, y1),
                    (lx2 + l2 / 2, y2), (lx2 - l2 / 2, y2)])
                lx1 += lane_w1
                lx2 += lane_w2

        # fog band
        if seg.fog > 0.02:
            alpha = int(240 * min(1.0, seg.fog))
            fog_surf = self._fog(self._fog_color)
            fog_surf.set_alpha(alpha)
            surface.blit(fog_surf, band.topleft, area=band)

    # -- sprites ----------------------------------------------------------
    def _scaled(self, image: pygame.Surface, dest_w: int) -> pygame.Surface:
        # Bucket the width so the cache holds far fewer distinct sizes (and is
        # warmed up front by `warm`): the race then never scales on the fly.
        dest_w = (dest_w // 4) * 4
        if dest_w < 4:
            dest_w = 4
        key = (id(image), dest_w)
        surf = self._scale_cache.get(key)
        if surf is None:
            dest_h = max(1, int(dest_w * image.get_height() / image.get_width()))
            surf = pygame.transform.scale(image, (dest_w, dest_h))
            if len(self._scale_cache) > 8192:
                self._scale_cache.clear()
            self._scale_cache[key] = surf
        return surf

    def warm(self, image: pygame.Surface, max_w: int = 256, step: int = 8) -> None:
        """Pre-scale a prop across the sizes it can appear at, so the race
        loads its details once instead of generating them in real time."""
        w = step
        while w <= max_w:
            self._scaled(image, w)
            w += step

    def render_on_segment(self, surface: pygame.Surface, image: pygame.Surface,
                          seg: Segment, percent: float, offset: float,
                          world_width: float, angle: float = 0.0):
        """Draw a sprite anchored to an already-projected segment.

        This is what makes roadside props and rival cars follow the road: the
        segment's projected ``scr_x`` already contains the accumulated curve
        offset and its ``scr_y`` the hill height, so a sprite placed relative to
        it bends and rises exactly with the tarmac.

        ``percent`` (0..1) interpolates along the segment; ``offset`` is in
        road-width units (``0`` centre, ``±1`` the road edges).
        """
        p1, p2 = seg.p1, seg.p2
        scr_x = interpolate(p1.scr_x, p2.scr_x, percent)
        scr_y = interpolate(p1.scr_y, p2.scr_y, percent)
        scr_w = interpolate(p1.scr_w, p2.scr_w, percent)
        if scr_w <= 1.0:
            return None
        # scale_px == (depth / cz) * width/2, recovered from the road width
        scale_px = scr_w / C.ROAD_WIDTH
        sx = scr_x + offset * scr_w
        dest_w = int(scale_px * world_width)
        if dest_w < 3 or dest_w > self.width * 4:
            return None
        img = self._scaled(image, dest_w)
        if angle:
            img = pygame.transform.rotate(img, angle)
        rect = img.get_rect(midbottom=(int(sx), int(scr_y)))
        surface.blit(img, rect)
        return rect
