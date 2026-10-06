# Tracks and cars

Both tracks and cars are **data**, not code paths. You can add either without
touching the engine.

## Add a track

1. Give it a theme in `rengear/game/config.py` under `TRACKS`, and add its key
   to `TRACK_ORDER`:

   ```python
   "swamp": {
       "name": "MIRE BOG",
       "note": "low country",
       "sky":    ((40, 70, 60), (120, 160, 140)),   # top, horizon
       "ground": ((46, 70, 44), (34, 54, 36)),      # light, dark
       "road":   ((84, 88, 84), (74, 78, 74)),
       "rumble": ((220, 230, 220), (150, 60, 40)),
       "lane":   (225, 230, 220),
       "props":  ["pine", "rock", "sign"],
   },
   ```

2. Write its piece script in `rengear/game/tracks.py`:

   ```python
   def swamp(t):
       t.add_straight(60)
       _hills(t, [
           (30,  4, 20),
           (30, -4, -20),
           (45,  0, 30),
       ])
       t.add_straight(40)
   ```

   and register it in `TRACK_SCRIPTS`.

`add_road(enter, hold, leave, curve, hill)`:
- `enter`/`hold`/`leave` — segments to ease in, hold, ease out.
- `curve` — `>0` bends right, `<0` bends left, `0` straight.
- `hill` — `>0` climbs, `<0` descends.

The builder automatically seeds roadside props and closes the height loop so
the track wraps seamlessly.

## Add a car

Add an entry to `CARS` in `rengear/game/config.py` and its key to `CAR_ORDER`:

```python
"jet": {
    "name": "JET",
    "blurb": "lightweight",
    "color": (240, 240, 240), "accent": (240, 90, 60),
    "power": 0.95, "top": 1.04, "grip": 1.02, "nitro": 1.10,
},
```

- `power` scales acceleration.
- `top` scales top speed.
- `grip` scales steering and resistance to curves.
- `nitro` scales the boost.

The body sprite is generated from `color`/`accent` by `rengear/game/art.py`, so
no art file is needed.

## Add a prop

Add a factory to `PROP_FACTORIES` in `rengear/game/art.py`, then reference its
name from a track theme's `props` list. Factories return a
`pygame.Surface`; the renderer scales it by depth.

## Add a rival

Rivals live in `RIVALS` in `rengear/game/config.py`:
`(name, colour, accent, speed_fraction, grip, aggression)`. The AI brakes into
curves based on its speed fraction and drifts with its aggression.
