"""Headless unit tests for the road trick, tracks, cars and content.

Run with::

    python -m tests.test_engine

No window or sound card is needed: only geometry and rules are exercised.
"""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from rengear.engine.registry import make_registry  # noqa: E402
from rengear.game import config as C  # noqa: E402
from rengear.game.car import PLAYER_Z, Controls, Player, Rival  # noqa: E402
from rengear.game.road import (Point, RoadRenderer, build_track, camera_depth,  # noqa: E402
                               ease_in, ease_in_out, ease_out, increase,
                               overlap, percent_remaining, project)
from rengear.game.scenes import register_scenes  # noqa: E402

DT = 1.0 / 60.0


class TestMath(unittest.TestCase):
    def test_easing_endpoints(self):
        for fn in (ease_in, ease_out, ease_in_out):
            self.assertAlmostEqual(fn(0.0, 1.0, 0.0), 0.0, places=6)
            self.assertAlmostEqual(fn(0.0, 1.0, 1.0), 1.0, places=6)

    def test_ease_in_out_midpoint(self):
        self.assertAlmostEqual(ease_in_out(0.0, 10.0, 0.5), 5.0, places=6)

    def test_increase_wraps_both_ways(self):
        self.assertEqual(increase(0.0, C.SEGMENT_LENGTH + 5, C.SEGMENT_LENGTH), 5.0)
        self.assertEqual(increase(0.0, -5, C.SEGMENT_LENGTH), C.SEGMENT_LENGTH - 5)

    def test_percent_remaining(self):
        self.assertAlmostEqual(percent_remaining(C.SEGMENT_LENGTH / 2,
                                                 C.SEGMENT_LENGTH), 0.5)

    def test_overlap(self):
        self.assertTrue(overlap(0.0, 1.0, 0.4, 1.0))
        self.assertFalse(overlap(0.0, 1.0, 5.0, 1.0))

    def test_camera_depth_positive(self):
        self.assertGreater(camera_depth(), 0.0)


class TestProjection(unittest.TestCase):
    def test_projects_in_front(self):
        depth = camera_depth()
        p = Point(0.0, 0.0, 2000.0)
        project(p, 0.0, 0.0, 0.0, depth, 512, 288, C.ROAD_WIDTH)
        self.assertGreater(p.scr_w, 0.0)
        self.assertAlmostEqual(p.cam_z, 2000.0)
        self.assertAlmostEqual(p.scr_x, 256.0, places=3)

    def test_farther_is_narrower(self):
        depth = camera_depth()
        near, far = Point(0, 0, 1000), Point(0, 0, 5000)
        project(near, 0, 0, 0, depth, 512, 288, C.ROAD_WIDTH)
        project(far, 0, 0, 0, depth, 512, 288, C.ROAD_WIDTH)
        self.assertGreater(near.scr_w, far.scr_w)


class TestTrackBuild(unittest.TestCase):
    def test_every_track_builds_and_closes_its_loop(self):
        for key in C.TRACK_ORDER:
            with self.subTest(track=key):
                track = build_track(key)
                self.assertGreater(len(track.segments), 50)
                self.assertAlmostEqual(track.length % C.SEGMENT_LENGTH, 0.0)
                # p2 of one segment is p1 of the next
                for a, b in zip(track.segments, track.segments[1:]):
                    self.assertAlmostEqual(a.p2.world_y, b.p1.world_y, places=6)
                # the height wraps around to the start
                first = track.segments[0].p1.world_y
                last = track.segments[-1].p2.world_y
                self.assertAlmostEqual(first, last, places=6)

    def test_find_segment_wraps(self):
        track = build_track("coast")
        self.assertIs(track.find_segment(track.length + 10),
                      track.find_segment(10))

    def test_scenery_seeded(self):
        track = build_track("coast")
        total = sum(len(s.sprites) for s in track.segments)
        self.assertGreater(total, 0)

    def test_all_tracks_have_a_script(self):
        from rengear.game.tracks import TRACK_SCRIPTS
        for key in C.TRACK_ORDER:
            self.assertIn(key, TRACK_SCRIPTS)


class TestCar(unittest.TestCase):
    def _player(self):
        p = Player(name="T", color=(200, 0, 0), accent=(255, 255, 0))
        p.reset(0.0, -0.25)
        return p

    def test_accelerates(self):
        track = build_track("coast")
        p = self._player()
        for _ in range(60):
            p.update(DT, track, Controls(accelerate=True))
        self.assertGreater(p.speed, 0.0)
        self.assertGreater(p.z, 0.0)

    def test_lap_increments_on_wrap(self):
        track = build_track("coast")
        p = self._player()
        p.speed = p.max_speed
        p.z = track.length - 5.0
        p.update(DT, track, Controls(accelerate=True))
        self.assertEqual(p.lap, 1)

    def test_off_road_is_slow(self):
        track = build_track("coast")
        p = self._player()
        p.speed = p.max_speed
        p.offset = 1.5
        for _ in range(150):
            p.update(DT, track, Controls(accelerate=True))
        self.assertLessEqual(p.speed, p.max_speed * C.OFF_ROAD_MAX + 1.0)

    def test_nitro_is_finite(self):
        track = build_track("coast")
        p = self._player()
        p.speed = p.max_speed * 0.5
        p.nitro = 0.2
        for _ in range(60):
            p.update(DT, track, Controls(accelerate=True, nitro=True))
        self.assertGreaterEqual(p.nitro, 0.0)
        self.assertLessEqual(p.nitro, 1.0)
        self.assertLess(p.nitro, 0.2)   # it was spent
        self.assertLessEqual(p.speed, p.max_speed * C.NITRO_MULT + 1.0)

    def test_rival_advances(self):
        track = build_track("coast")
        r = Rival(name="R", color=(0, 200, 0), accent=(255, 255, 255),
                  skill=0.95)
        r.reset(1000.0, 0.0)
        for _ in range(120):
            r.update(DT, track)
        self.assertGreater(r.z, 1000.0)

    def test_player_z_is_positive(self):
        self.assertGreater(PLAYER_Z, 0.0)

    def test_collision_ignores_a_car_being_overtaken(self):
        # A rival between the camera and the player's car is *behind* the car
        # and must not trigger a collision (this was the "teleport backwards"
        # bug). A rival just in front of the car must collide.
        track = build_track("coast")
        p = self._player()
        p.speed = p.max_speed
        r = Rival(name="R", color=(0, 0, 0), accent=(1, 1, 1), skill=0.9)
        r.speed = p.max_speed * 0.5
        r.offset = p.offset

        r.z = p.z + 100.0                       # behind the player's car
        self.assertFalse(p.collide_with(r, track.length))
        r.z = p.z + PLAYER_Z + 100.0            # just in front of the car
        self.assertTrue(p.collide_with(r, track.length))

    def test_automatic_gear_progression(self):
        p = self._player()
        seen = []
        for pct in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            p.speed = p.max_speed * pct
            seen.append(p.gear)
            self.assertGreaterEqual(p.rpm, 0.0)
            self.assertLessEqual(p.rpm, 1.0)
        self.assertEqual(seen[0], 1)
        self.assertEqual(seen[-1], C.GEARS)
        self.assertEqual(seen, sorted(seen))


class TestSpriteFollowsRoad(unittest.TestCase):
    def _segment(self):
        from rengear.game.road import Point, Segment
        seg = Segment(0, Point(), Point(), 2.0)
        seg.p1.scr_x, seg.p1.scr_y, seg.p1.scr_w = 300.0, 200.0, 100.0
        seg.p2.scr_x, seg.p2.scr_y, seg.p2.scr_w = 340.0, 180.0, 80.0
        return seg

    def test_prop_is_anchored_to_its_segment(self):
        renderer = RoadRenderer(C.LOGICAL_W, C.LOGICAL_H)
        surface = pygame.Surface((C.LOGICAL_W, C.LOGICAL_H))
        img = pygame.Surface((40, 60), pygame.SRCALPHA)
        rect = renderer.render_on_segment(surface, img, self._segment(),
                                          0.0, 1.5, 700.0)
        self.assertIsNotNone(rect)
        # sx = scr_x + offset * scr_w, and it sits on the road (bottom = scr_y)
        self.assertEqual(rect.centerx, int(300.0 + 1.5 * 100.0))
        self.assertEqual(rect.bottom, 200)

    def test_interpolates_along_the_segment(self):
        renderer = RoadRenderer(C.LOGICAL_W, C.LOGICAL_H)
        surface = pygame.Surface((C.LOGICAL_W, C.LOGICAL_H))
        img = pygame.Surface((40, 60), pygame.SRCALPHA)
        rect = renderer.render_on_segment(surface, img, self._segment(),
                                          0.5, 0.0, 700.0)
        self.assertIsNotNone(rect)
        self.assertEqual(rect.centerx, 320)     # midway between 300 and 340

    def test_culled_when_off_screen_or_tiny(self):
        renderer = RoadRenderer(C.LOGICAL_W, C.LOGICAL_H)
        surface = pygame.Surface((C.LOGICAL_W, C.LOGICAL_H))
        img = pygame.Surface((40, 60), pygame.SRCALPHA)
        from rengear.game.road import Point, Segment
        seg = Segment(0, Point(), Point(), 0.0)
        seg.p1.scr_x, seg.p1.scr_y, seg.p1.scr_w = 100.0, 100.0, 0.5
        seg.p2.scr_x, seg.p2.scr_y, seg.p2.scr_w = 100.0, 100.0, 0.5
        self.assertIsNone(renderer.render_on_segment(surface, img, seg,
                                                     0.0, 0.0, 700.0))

    def test_real_render_produces_visible_segments(self):
        surface = pygame.Surface((C.LOGICAL_W, C.LOGICAL_H))
        renderer = RoadRenderer(C.LOGICAL_W, C.LOGICAL_H)
        visible = renderer.render(surface, build_track("coast"), 0.0, 0.0, 0.0)
        self.assertGreater(len(visible), 10)


class TestContent(unittest.TestCase):
    def test_car_order_matches_table(self):
        self.assertEqual(sorted(C.CAR_ORDER), sorted(C.CARS))

    def test_track_order_matches_table(self):
        self.assertEqual(sorted(C.TRACK_ORDER), sorted(C.TRACKS))

    def test_rival_count(self):
        self.assertEqual(len(C.RIVALS), C.RACE_CARS - 1)

    def test_scenes_register(self):
        reg = make_registry()
        register_scenes(reg)
        for name in ("splash", "title", "choose", "race", "pause", "results"):
            self.assertTrue(reg.has("scene", name), name)


class TestSplitScreen(unittest.TestCase):
    """Integration: build a real App and drive a two-player race headless."""

    @classmethod
    def setUpClass(cls):
        from rengear.engine.app import App
        from rengear.game import app_config, register_content
        cls.app = App(app_config())
        register_content(cls.app)

    def test_two_players_two_views(self):
        app = self.app
        app.scenes.switch("race", transition=False, car="comet", track="coast",
                          car2="dune")
        race = app.scenes.current
        self.assertTrue(race.split)
        self.assertEqual(len(race.players), 2)
        self.assertEqual(len(race.views), 2)
        self.assertEqual(len(race.rivals), 0)
        self.assertIs(race.player, race.players[0])

        race.countdown = 0.0
        race.state = "racing"
        app.input.held_profile = lambda profile, action: action == "accelerate"
        for _ in range(180):
            app.scenes.update(1.0 / 60.0)
            app.canvas.fill((0, 0, 0))
            app.scenes.draw(app.canvas)
        self.assertGreater(race.players[0].z, 0.0)
        self.assertGreater(race.players[1].z, 0.0)

    def test_solo_still_has_rivals(self):
        app = self.app
        app.scenes.switch("race", transition=False, car="spark", track="pine")
        race = app.scenes.current
        self.assertFalse(race.split)
        self.assertEqual(len(race.players), 1)
        self.assertEqual(len(race.rivals), C.RACE_CARS - 1)
        self.assertEqual(len(race.views), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
