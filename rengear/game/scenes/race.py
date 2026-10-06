"""The race scene: solo against rivals, or two players in split screen.

Each human player has their own car, their own camera and their own dashboard.
In split-screen mode the frame is divided vertically and every view is rendered
independently (road, props, other cars, HUD) into its own small surface before
being composited.  Nothing about the road renderer or the car physics changes —
only *who* is the camera for a given view.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional

import pygame

from rengear.engine.platform import EventType
from rengear.engine.scene import Scene
from rengear.engine.sprites import vertical_gradient
from rengear.engine.ui import draw_bar, draw_gauge, draw_text

from .. import art
from .. import config as C
from ..car import PLAYER_Z, Controls, Player, Rival
from ..road import RoadRenderer, build_track

#: sprite widths, in world units
PROP_WORLD = 780.0
CAR_WORLD = 560.0
PLAYER_IMG_W = 138
PLAYER_IMG_H = 90


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes = int(seconds // 60)
    rest = seconds - minutes * 60
    return f"{minutes}:{rest:05.2f}"


def build_backdrop(size, theme):
    """Sky gradient plus a far hill silhouette for one viewport."""
    w, h = size
    sky = vertical_gradient(w, h, theme["sky"][0], theme["sky"][1])
    rng = random.Random(29)
    hills = pygame.Surface((w, 80), pygame.SRCALPHA)
    base = tuple(max(0, c - 26) for c in theme["sky"][1])
    far = tuple(max(0, c - 12) for c in theme["sky"][1])
    x = -20
    while x < w + 40:
        peak = rng.randint(22, 64)
        spread = rng.randint(40, 90)
        col = far if rng.random() < 0.5 else base
        pygame.draw.polygon(hills, col, [
            (x, 80), (x + spread / 2, 80 - peak), (x + spread, 80)])
        x += int(spread * 0.6)
    return sky, hills


@dataclass
class _View:
    """One player's window onto the track."""

    player: Player
    profile: dict
    label: str
    size: tuple
    surface: object
    renderer: RoadRenderer
    sky: object
    hills: object
    bg_x: float = 0.0
    bg_y: float = 0.0
    scale: float = 1.0

    @property
    def w(self) -> int:
        return self.size[0]

    @property
    def h(self) -> int:
        return self.size[1]


class RaceScene(Scene):
    def __init__(self, app, car: str = "spark", track: str = "coast",
                 car2: Optional[str] = None) -> None:
        super().__init__(app)
        self.track_key = track
        self.track = build_track(track)
        self.car_key = car
        self.car2_key = car2
        self.split = car2 is not None

        w, h = app.render_size
        self.view_size = (w // 2, h) if self.split else (w, h)
        theme = self.track.theme
        self.sky, self.hills = build_backdrop(self.view_size, theme)

        self.state = "countdown"
        self.countdown = C.COUNTDOWN
        self._last_beep = 99
        self.elapsed = 0.0
        self.race_time = 0.0
        self.finish_timer = 0.0
        self._results_sent = False
        self.toast = ""
        self.toast_timer = 0.0
        self._place_sound = None
        self._engine_on = False
        self._prev_laps: dict = {}

        self._build_cars()
        self._build_views()
        self.best = dict(app.get_setting("best", {}) or {})
        self.best_lap = self.best.get(track)

    # ------------------------------------------------------------------
    # setup
    # ------------------------------------------------------------------
    def _make_player(self, car_key: str, label: str) -> Player:
        car = C.CARS[car_key]
        name = car["name"] if not self.split else f"{label} {car['name']}"
        player = Player(name=name, color=car["color"], accent=car["accent"],
                        power=car["power"], top=car["top"], grip=car["grip"],
                        nitro_factor=car["nitro"], is_player=True)
        return player

    def _build_cars(self) -> None:
        if self.split:
            p1 = self._make_player(self.car_key, "P1")
            p2 = self._make_player(self.car2_key or self.car_key, "P2")
            p1.reset(0.0, -0.4)
            p2.reset(0.0, 0.4)
            self.players = [p1, p2]
            self.rivals: List[Rival] = []
        else:
            p = self._make_player(self.car_key, "")
            p.reset(0.0, -0.25)
            self.players = [p]
            self.rivals = []
            spacing = PLAYER_Z * 2.0
            for i, (name, color, accent, skill, grip, aggro) in enumerate(C.RIVALS):
                rival = Rival(name=name, color=color, accent=accent,
                              power=0.9, top=skill, grip=grip)
                rival.skill = skill
                rival.aggression = aggro
                rival.reset((i + 1) * spacing, (-1) ** i * (0.35 + 0.15 * i))
                self.rivals.append(rival)
        self.cars = self.players + self.rivals

    def _build_views(self) -> None:
        app = self.app
        profiles = ([C.P1_COOP_KEYS, C.P2_COOP_KEYS] if self.split
                    else [C.P1_KEYS])
        labels = ["P1", "P2"] if self.split else [""]
        self.views: List[_View] = []
        for player, profile, label in zip(self.players, profiles, labels):
            self.views.append(_View(
                player=player, profile=profile, label=label,
                size=self.view_size,
                surface=app.backend.new_surface(*self.view_size, alpha=False),
                renderer=RoadRenderer(*self.view_size),
                sky=self.sky, hills=self.hills,
                scale=self.view_size[0] / 512.0,
            ))

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    @property
    def player(self) -> Player:
        """The first (or only) human player — convenience for tools/tests."""
        return self.players[0]

    def on_enter(self) -> None:
        self.app.audio.stop_music()
        self.app.audio.start_engine()
        self._engine_on = True

    def on_exit(self) -> None:
        self.app.audio.stop_engine()
        self._engine_on = False

    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        inp = self.app.input
        if event.key in inp.bindings.get("pause", ()):
            self.app.scenes.switch("pause", race=self)
        elif event.key in inp.bindings.get("restart", ()):
            self.app.switch_scene("race", car=self.car_key, track=self.track_key,
                                  car2=self.car2_key)
        elif event.key in inp.bindings.get("cancel", ()):
            self.app.scenes.switch("pause", race=self)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _player_y(self, player: Player) -> float:
        return self.track.height_at(player.z + PLAYER_Z)

    def _controls(self, profile: dict) -> Controls:
        inp = self.app.input
        left = inp.held_profile(profile, "left")
        right = inp.held_profile(profile, "right")
        return Controls(
            accelerate=inp.held_profile(profile, "accelerate"),
            brake=inp.held_profile(profile, "brake"),
            left=left and not right,
            right=right and not left,
            nitro=inp.held_profile(profile, "nitro"),
        )

    def _start_engine_sound(self) -> None:
        if not self._engine_on:
            self.app.audio.start_engine()
            self._engine_on = True

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.state == "countdown":
            self._update_countdown(dt)
            for view in self.views:
                self._update_camera_bg(view, dt)
            return

        self.elapsed += dt
        self.race_time += dt

        for view in self.views:
            player = view.player
            prev_lap = player.lap
            controls = self._controls(view.profile)
            events = player.update(dt, self.track, controls)
            if events["bump"]:
                self.app.audio.play("bump")
            if player.lap > prev_lap:
                self._complete_lap(player, view)

        for rival in self.rivals:
            rival.update(dt, self.track, self.players[0], self.cars)

        self._resolve_collisions()

        # clamp at the very edge of the world and scrub speed on impact
        for player in self.players:
            if abs(player.offset) > 2.9:
                player.offset = math.copysign(2.9, player.offset)
                if player.speed > player.max_speed * 0.4:
                    player.hit_wall(player.max_speed)
                    self.app.audio.play("crash")

        self._update_places()
        self._update_engine_sound()
        for view in self.views:
            self._update_camera_bg(view, dt)

        if self.toast_timer > 0:
            self.toast_timer -= dt

        self._check_finish(dt)

    def _resolve_collisions(self) -> None:
        length = self.track.length
        if self.split:
            p1, p2 = self.players
            if p1.collide_with(p2, length) or p2.collide_with(p1, length):
                self.app.audio.play("crash")
        else:
            player = self.players[0]
            for rival in self.rivals:
                if player.collide_with(rival, length):
                    self.app.audio.play("crash")
                    break

    def _update_countdown(self, dt: float) -> None:
        self.countdown -= dt
        cue = int(math.ceil(self.countdown))
        if cue < self._last_beep and cue >= 1:
            self._last_beep = cue
            self.app.audio.play("count")
        if self.countdown <= 0:
            self.state = "racing"
            self.elapsed = 0.0
            self.race_time = 0.0
            self.app.audio.play("go")
            self._toast("GO!")

    def _complete_lap(self, player: Player, view: _View) -> None:
        lap_time = player.lap_time
        player.lap_times.append(lap_time)
        player.lap_time = 0.0
        if player.best_lap == 0.0 or lap_time < player.best_lap:
            player.best_lap = lap_time
        if self.best_lap is None or lap_time < self.best_lap:
            self.best_lap = lap_time
            self.best[self.track_key] = self.best_lap
            self.app.set_setting("best", self.best)
            self.app.audio.play("record")
        self.app.audio.play("lap")
        if not self.split:
            lap_done = player.lap
            if lap_done >= C.LAPS - 1:
                self._toast("FINAL LAP")
            else:
                self._toast(f"LAP {lap_done + 1}")

    def _update_places(self) -> None:
        length = self.track.length
        finished = sorted((c for c in self.cars if c.finished),
                          key=lambda c: c.finish_time)
        running = sorted((c for c in self.cars if not c.finished),
                         key=lambda c: c.lap * length + c.z, reverse=True)
        for i, c in enumerate(finished + running):
            c.place = i + 1

    def _update_engine_sound(self) -> None:
        if not self.app.audio.ok:
            return
        pct = max(p.speed / p.max_speed if p.max_speed else 0.0
                  for p in self.players)
        self.app.audio.set_engine(0.05 + pct * 0.4 + 0.1)

    def _update_camera_bg(self, view: _View, dt: float) -> None:
        player = view.player
        seg = self.track.find_segment(player.z + PLAYER_Z)
        pct = player.speed / player.max_speed if player.max_speed else 0.0
        view.bg_x = (view.bg_x - seg.curve * pct * 40.0 * dt) % view.w
        target = max(-26.0, min(26.0, -self._player_y(player) * 0.004))
        view.bg_y += (target - view.bg_y) * min(1.0, dt * 4.0)

    def _check_finish(self, dt: float) -> None:
        for p in self.players:
            if not p.finished and p.lap >= C.LAPS:
                p.finished = True
                p.finish_time = self.race_time
                self.app.audio.play("finish")
        for rival in self.rivals:
            if not rival.finished and rival.lap >= C.LAPS:
                rival.finished = True
                rival.finish_time = self.race_time

        if not any(p.finished for p in self.players):
            return
        self.finish_timer += dt
        all_players = all(p.finished for p in self.players)
        all_rivals = all(r.finished for r in self.rivals)
        if self._results_sent:
            return
        cap = 30.0 if self.split else 12.0
        if ((all_players and all_rivals and self.finish_timer > 1.5)
                or self.finish_timer > cap):
            self._results_sent = True
            self.app.switch_scene("results", transition=True,
                                  track=self.track_key, cars=self.cars,
                                  players=self.players)

    def _toast(self, text: str) -> None:
        self.toast = text
        self.toast_timer = 1.6

    # ------------------------------------------------------------------
    # draw
    # ------------------------------------------------------------------
    def snapshot(self) -> pygame.Surface:
        surf = self.app.backend.new_surface(*self.app.render_size, alpha=False)
        self.draw(surf)
        return surf

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        for i, view in enumerate(self.views):
            self._draw_view(view)
            surface.blit(view.surface,
                         (0 if not self.split else i * (w // 2), 0))
        if self.split:
            pygame.draw.line(surface, (240, 240, 248), (w // 2, 0), (w // 2, h), 2)

    # -- one player's view ------------------------------------------------
    def _draw_view(self, view: _View) -> None:
        surface = view.surface
        player = view.player
        vw, vh = view.w, view.h

        surface.blit(view.sky, (0, 0))
        hill_y = int(vh * 0.40 + view.bg_y)
        surface.blit(view.hills, (int(view.bg_x) - vw, hill_y))
        surface.blit(view.hills, (int(view.bg_x), hill_y))

        visible = view.renderer.render(surface, self.track, player.offset,
                                       player.z, self._player_y(player))
        self._draw_finish(surface, visible)
        self._draw_props(surface, visible, view.renderer)
        self._draw_other_cars(surface, visible, player, view.renderer)
        self._draw_own_car(view)
        self._draw_hud(view)

    def _draw_props(self, surface, visible, renderer) -> None:
        for seg in reversed(visible):
            if seg.fog > 0.85 or not seg.sprites:
                continue
            for sp in seg.sprites:
                if sp["name"] not in art.PROP_FACTORIES:
                    continue
                img = art.prop(sp["name"])
                renderer.render_on_segment(
                    surface, img, seg, 0.0, sp["offset"], PROP_WORLD * sp["scale"])

    def _draw_other_cars(self, surface, visible, cam: Player, renderer) -> None:
        length = self.track.length
        starts = [seg.p1.world_z + (length if seg.looped else 0)
                  for seg in visible]
        drawable = []
        for car in self.cars:
            if car is cam:
                continue
            dz = (car.z - cam.z) % length
            if dz <= PLAYER_Z * 0.9 or dz > length * 0.5:
                continue
            car_z = cam.z + dz
            for i, seg in enumerate(visible):
                start = starts[i]
                if start <= car_z < start + C.SEGMENT_LENGTH:
                    percent = (car_z - start) / C.SEGMENT_LENGTH
                    drawable.append((dz, car, seg, percent))
                    break
        drawable.sort(key=lambda item: item[0], reverse=True)
        for _dz, car, seg, percent in drawable:
            img = art.car_rear(car.color, car.accent, 96, 62)
            angle = max(-12.0, min(12.0, -seg.curve * 1.8))
            renderer.render_on_segment(
                surface, img, seg, percent, car.offset, CAR_WORLD, angle)

    def _draw_own_car(self, view: _View) -> None:
        surface = view.surface
        player = view.player
        s = view.scale
        iw = max(48, int(PLAYER_IMG_W * s))
        ih = max(32, int(PLAYER_IMG_H * s))
        img = art.car_rear(player.color, player.accent, iw, ih)
        pct = player.speed / player.max_speed if player.max_speed else 0.0
        bob = math.sin(self.elapsed * 26.0) * pct * 1.6
        steer = player.steer_visual
        angle = -steer * 10.0
        if abs(angle) > 0.5:
            img = pygame.transform.rotozoom(img, angle, 1.0)
        x = view.w // 2 + int((steer * 10 + player.offset * 14) * (0.6 + 0.4 * s))
        ground_y = view.h + int(16 * s) + int(bob)

        nitro = (self.app.input.held_profile(view.profile, "nitro")
                 and player.nitro > 0.0 and self.state == "racing")
        if nitro:
            flame = art.nitro_flame(iw - 40, int(46 * s) + 10, self.elapsed)
            surface.blit(flame, (x - flame.get_width() // 2,
                                 ground_y - ih + 34))
        if player.bump_timer > 0:
            x += random.randint(-2, 2)
            ground_y += random.randint(-2, 2)
        surface.blit(img, img.get_rect(midbottom=(x, ground_y)))

    def _draw_finish(self, surface, visible) -> None:
        for seg in visible:
            if seg.index > 1:
                continue
            p1, p2 = seg.p1, seg.p2
            cols = 14
            for i in range(cols):
                t0, t1 = i / cols, (i + 1) / cols
                color = (240, 240, 244) if i % 2 == 0 else (22, 22, 28)
                pygame.draw.polygon(surface, color, [
                    (p1.scr_x - p1.scr_w + 2 * p1.scr_w * t0, p1.scr_y),
                    (p1.scr_x - p1.scr_w + 2 * p1.scr_w * t1, p1.scr_y),
                    (p2.scr_x - p2.scr_w + 2 * p2.scr_w * t1, p2.scr_y),
                    (p2.scr_x - p2.scr_w + 2 * p2.scr_w * t0, p2.scr_y)])

    # -- HUD --------------------------------------------------------------
    def _draw_hud(self, view: _View) -> None:
        surface = view.surface
        fonts = self.app.fonts
        player = view.player
        w, h = view.w, view.h

        if not self.split:
            self._draw_hud_solo(surface, player, w, h)
        else:
            self._draw_hud_split(surface, view)

        if self.state == "countdown":
            cue = max(1, int(math.ceil(self.countdown)))
            draw_text(surface, fonts, str(cue), (w // 2, h // 2 - 20),
                      size=64 if self.split else 92, color=C.HUD_GOLD,
                      center=True, bold=True)
        if self.toast_timer > 0 and not self.split:
            draw_text(surface, fonts, self.toast, (w // 2, 70), size=30,
                      color=C.HUD_GOLD, center=True, bold=True)

    def _draw_hud_solo(self, surface, player: Player, w, h) -> None:
        fonts = self.app.fonts
        top = pygame.Surface((w, 26), pygame.SRCALPHA)
        top.fill((8, 10, 18, 205))
        surface.blit(top, (0, 0))
        pygame.draw.line(surface, (90, 200, 220), (0, 26), (w, 26), 1)

        lap = min(player.lap + 1, C.LAPS)
        draw_text(surface, fonts, f"LAP {lap}/{C.LAPS}", (12, 4), size=18,
                  color=C.HUD_GOLD, bold=True)
        draw_text(surface, fonts, fmt_time(self.race_time), (w // 2, 3), size=18,
                  color=C.WHITE, center=True, bold=True)
        draw_text(surface, fonts, f"POS {player.place}/{len(self.cars)}",
                  (w - 12, 4), size=18, color=C.HUD_CYAN, bold=True, right=True)
        draw_text(surface, fonts,
                  f"BEST {fmt_time(self.best_lap) if self.best_lap else '--:--'}",
                  (w - 12, 31), size=12, color=(180, 210, 230), right=True)
        draw_text(surface, fonts, "NITRO", (w - 116, 47), size=11,
                  color=(150, 200, 230))
        draw_bar(surface, w - 116, 59, 104, 7, player.nitro,
                 (110, 200, 255), segments=4)

        for i, car in enumerate(sorted(self.cars, key=lambda c: c.place)):
            y = 32 + i * 12
            col = C.HUD_GOLD if car is player else (150, 165, 190)
            prefix = "\u25b8 " if car is player else "  "
            draw_text(surface, fonts, f"{prefix}{car.place} {car.name}", (12, y),
                      size=11, color=col)

        pct = player.speed / player.max_speed if player.max_speed else 0.0
        sx, sy = 66, h - 42
        draw_gauge(surface, (sx, sy), 38, pct, rim=(90, 200, 220),
                   needle=(255, 90, 80))
        draw_text(surface, fonts, str(int(player.speed / C.MAX_SPEED * 300)),
                  (sx, sy - 3), size=22, color=C.WHITE, center=True, bold=True)
        draw_text(surface, fonts, "km/h", (sx, sy + 16), size=10,
                  color=(160, 190, 210), center=True)

        tx, ty = w - 66, h - 42
        draw_gauge(surface, (tx, ty), 34, player.rpm, rim=(255, 200, 90),
                   needle=(120, 240, 255), redline=0.82)
        draw_text(surface, fonts, str(player.gear), (tx, ty - 4), size=22,
                  color=C.HUD_GOLD, center=True, bold=True)
        draw_text(surface, fonts, "GEAR", (tx, ty + 15), size=10,
                  color=(200, 180, 130), center=True)

    def _draw_hud_split(self, surface, view: _View) -> None:
        fonts = self.app.fonts
        player = view.player
        w, h = view.w, view.h

        top = pygame.Surface((w, 20), pygame.SRCALPHA)
        top.fill((8, 10, 18, 210))
        surface.blit(top, (0, 0))
        pygame.draw.line(surface, (90, 200, 220), (0, 20), (w, 20), 1)

        lap = min(player.lap + 1, C.LAPS)
        draw_text(surface, fonts, f"{view.label}  LAP {lap}/{C.LAPS}", (6, 3),
                  size=12, color=C.HUD_GOLD, bold=True)
        draw_text(surface, fonts, fmt_time(self.race_time), (w // 2, 3),
                  size=12, color=C.WHITE, center=True, bold=True)
        draw_text(surface, fonts, f"P{player.place}", (w - 6, 3), size=12,
                  color=C.HUD_CYAN, bold=True, right=True)

        # nitro bar right under the bar
        draw_bar(surface, w - 66, 23, 60, 5, player.nitro, (110, 200, 255),
                 segments=3)

        pct = player.speed / player.max_speed if player.max_speed else 0.0
        sx, sy = 32, h - 30
        draw_gauge(surface, (sx, sy), 24, pct, rim=(90, 200, 220),
                   needle=(255, 90, 80), ticks=8)
        draw_text(surface, fonts, str(int(player.speed / C.MAX_SPEED * 300)),
                  (sx, sy - 2), size=14, color=C.WHITE, center=True, bold=True)

        tx, ty = w - 32, h - 30
        draw_gauge(surface, (tx, ty), 22, player.rpm, rim=(255, 200, 90),
                   needle=(120, 240, 255), redline=0.82, ticks=8)
        draw_text(surface, fonts, str(player.gear), (tx, ty - 2), size=14,
                  color=C.HUD_GOLD, center=True, bold=True)
