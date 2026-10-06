# Architecture

RENGEAR is split into two layers that never leak into each other:

```
rengear/engine/   game-agnostic primitives (reusable)
rengear/game/     RENGEAR's content and rules (built on the engine)
```

The engine knows nothing about cars, tracks or the road renderer. The game
knows nothing about SDL details. That is what makes the project modular: you
can add gameplay without touching the engine, and reuse the engine for another
game.

## The platform seam

Inside the engine there is a second, equally strict split:

```
rengear/engine/platform/   the OS boundary (window, events, keys, audio,
                           fonts, files)
rengear/engine/*.py        game-agnostic core (app, scenes, input, ui, save)
```

`platform/base.py` defines the contract (`Backend`, `Event`, `EventType`,
`Key`, `WindowConfig`); `platform/pygame_backend.py` implements it;
`platform/__init__.py` is the **only** file that names a concrete backend.
Selecting `RENGEAR_BACKEND` swaps it.

Gameplay names logical `Key`/`Event` values — never `pygame.K_*` — so swapping
pygame for an SDL3, console or web backend is a matter of implementing
`Backend`; the rules do not change.

## The trick of the tracks

`rengear/game/road.py` is the heart of the game. A track is a **flat list of
segments**, and each segment stores two numbers that create every illusion:

```
Segment(curve, y)   # curve: how hard the road bends; y: world height (hills)
```

### Building the road

A track script (see `rengear/game/tracks.py`) appends pieces with

```python
track.add_road(enter, hold, leave, curve, hill)
```

`enter`/`hold`/`leave` are segment counts and the curve/hill are eased in and
out, exactly like the classic OutRun road generator. Because `p2` of one
segment is the `p1` of the next, the result is a continuous ribbon while the
track stays trivially editable.

### Projecting the road

Each frame the segments from the player's position up to `DRAW_DISTANCE` are
projected with a single perspective divide:

```
scale  = camera_depth / (world_z - camera_z)
scr_x  = width/2  + scale * (world_x - camera_x) * width/2
scr_y  = height/2 - scale * (world_y - camera_y) * height/2
scr_w  = scale * road_width * width/2
```

Curves are faked by accumulating an offset (`x += dx; dx += curve`) and hills
come for free from the projected `y`. Segments are painted back-to-front; the
`maxy` clip hides segments behind a hill crest (`p2.scr_y >= maxy`).

### Painting a segment

Each segment paints, in order: a grass band, two rumble strips, the road
polygon, the dashed lane markers and a fog band. Colours alternate every
`RUMBLE_LENGTH` segments so the road appears to move even on a straight.

### Sprites

Roadside props and rival cars are drawn **anchored to their road segment**
(`RoadRenderer.render_on_segment`).  Because the segment's projected `scr_x`
already contains the accumulated curve offset and its `scr_y` the hill height,
the sprites bend and rise exactly with the tarmac:

```
sx     = scr_x + offset * scr_w          # offset in road-width units
dest_w = (scr_w / road_width) * world_width
```

Cars are interpolated along their segment (`percent`) and given a small
rotation based on the local curve, so they lean through corners.  The player's
own car is a fixed sprite near the bottom of the screen that turns with the
steering input, as in the arcade originals.

## Track space

Gameplay lives in **track space**, completely decoupled from pixels:

- `z` — absolute distance travelled along the (looped) track.
- `offset` — lane position in road-width units (`0` centre, `±1` road edges).
- `speed` — world units per second.

The player and the rivals are the same `Car` shape (`rengear/game/car.py`);
the rival AI simply decides a target speed and a lane and calls the same
integration. The renderer turns track space into pixels and knows nothing
about AI, and the AI knows nothing about projection.

## Frame flow

```
App.run()
  └─ fixed timestep (1/60)
       ├─ backend.tick(fps)                     # platform: frame timing
       ├─ InputMap.begin_frame()                # platform: backend.pressed_keys()
       ├─ for event in backend.poll_events()
       │    └─ SceneManager.handle_event(event) # platform-neutral Event
       ├─ SceneManager.update(dt)
       │    └─ RaceScene.update(dt)             # player, rivals, laps, HUD state
       ├─ SceneManager.draw(canvas)
       │    └─ RaceScene.draw()
       │         ├─ sky + parallax backdrop
       │         ├─ RoadRenderer.render()       # the trick
       │         ├─ finish line, props, rivals, player
       │         └─ HUD
       └─ backend.present(canvas)               # platform: integer-scale + flip
```

## Split screen

Local multiplayer is a **vertical** split: the frame is halved and each human
player owns one :class:`_View` holding their car, a `RoadRenderer` sized to the
viewport, their backdrop and their key profile. `RaceScene.draw` renders each
view independently into its own surface and blits the two halves side by side,
then draws a divider.

Because the road renderer is already parameterised by width/height and the
sprites are anchored to projected segments, no rendering code had to change:
the *only* difference is who is the camera. Cars owned by the other player are
drawn by the same "other cars" pass as the AI rivals, from each camera in turn.

Input stays decoupled too: `InputMap.held_profile(profile, action)` queries a
specific key set, so `P1_COOP_KEYS` (arrows + Z) and `P2_COOP_KEYS` (WASD + C)
never collide.

## Scenes

Scenes are registered under `scene/<name>` and swapped by `SceneManager`, which
handles fades. `PauseScene` keeps a reference to the running `RaceScene` and
resumes it with `SceneManager.set_current`, so pausing never rebuilds the
track. A switch is ignored while a fade is already in flight, which prevents a
scene that requests a switch every frame from starving the transition.

## Registry and data

`rengear/engine/registry.py` maps `kind/name -> object`. Kinds used by the
game: `scene`. Cars and tracks are plain data in `rengear/game/config.py`, so
adding content never edits the engine.
