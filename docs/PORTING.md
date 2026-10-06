# Porting: the platform seam

RENGEAR is built so the game rules never touch the OS. Everything the host
must provide is described by one class:

```
rengear/engine/platform/base.py     ->  Backend, Event, EventType, Key, WindowConfig
rengear/engine/platform/pygame_backend.py  ->  the current implementation
rengear/engine/platform/__init__.py ->  the only file that picks a backend
```

## The rule

- `rengear/engine/*.py` and all of `rengear/game/` are **pure**: no `import
  pygame` for window/events/timing/input/audio/files. The one exception is the
  rendering calls; those are the graphics backend for stage 1 and are isolated
  to the scene/road drawing, never to the rules.
- Game code asks for semantic actions (`left`, `accelerate`, `nitro`, …) and
  reads `Key`/`Event` enums, never SDL constants.
- Selecting a backend is a one-liner in `platform/__init__.py`:

  ```bash
  RENGEAR_BACKEND=pygame python main.py
  ```

## What a new backend must implement

| `Backend` method        | meaning                                            |
|-------------------------|----------------------------------------------------|
| `init(config)`          | open a window / framebuffer                        |
| `shutdown()`            | release the platform                               |
| `set_caption(title)`    | window title                                       |
| `resize(size)`          | respond to a resize                                |
| `new_surface(w, h, a)`  | allocate a drawable surface                        |
| `overlay(size, rgba)`   | a filled translucent surface (fades)               |
| `present(canvas)`       | scale to the window and flip                       |
| `poll_events()`         | return a list of platform-neutral `Event`          |
| `tick(fps)`             | frame rate limit, return elapsed seconds           |
| `pressed_keys()`        | the set of logical `Key` currently held            |
| `load_font(size, bold)` | a font object with `.render`                       |
| `audio_ready()`         | whether sound is available                         |
| `make_sound(buffer)`    | build a playable sound from raw samples            |
| `user_data_dir(name)`   | per-user writable directory                        |

## Port checklist

1. Implement `Backend` for the target and register it in
   `platform/__init__.py`.
2. Keep the `Key`/`EventType` mapping in the backend only.
3. The road renderer uses `pygame.draw.polygon` / `Surface`; map these to the
   target's equivalent (or reimplement `RoadRenderer` against the new graphics
   API — it is self-contained).
4. `rengear/game/art.py` builds every sprite procedurally; port the primitives
   (rect, polygon, circle, line) and the sprites follow.
5. `rengear/engine/audio.py` synthesises PCM with pure maths; only
   `make_sound` is platform-specific.
6. Run `python -m tests.test_engine` — the geometry, track and car tests are
   headless and platform-independent.

Because the rules use track space (z, offset, speed) and never pixels, the
same `car.py`, `tracks.py` and `scenes/race.py` logic carries over unchanged.
