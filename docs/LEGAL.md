# Legal notes: an original arcade racer

> This document is a practical summary, **not legal advice**. If you plan to
> sell or heavily promote a game, consult a lawyer in your jurisdiction.

RENGEAR is inspired by the *gameplay* of classic pseudo-3D arcade racers such
as *Top Gear* and *OutRun*, but it shares **nothing protected** with them: no
names, no cars, no tracks, no artwork, no music, no logos, no code. This page
explains how that is possible and how to keep it that way.

## Ideas are not copyrighted — expression is

Copyright protects the *expression* of an idea, not the idea itself:

- **Not protected:** game mechanics and rules — a pseudo-3D road made of
  segments, curves and hills, a lap counter, nitro, rival AI, a rear-view
  player car. These are functional ideas, which is why a whole genre of
  pseudo-3D racing games exists from many studios.
- **Protected:** the specific cars, names, track layouts, story text, sprites,
  music, sound effects, logos and trade dress of another game.

So you may build a game that *feels* like Top Gear. You may not copy its cars,
tracks, art, audio or branding.

## Trademarks

- Do **not** use "*Top Gear*", "*OutRun*", "*Ferrari*", "*Lotus*", or any
  real manufacturer's name, logo or car design.
- Do not name the project after, or imitate the box art / logo style of, an
  existing game or car brand.
- Genre terms (`arcade racer`, `pseudo-3D racer`) are fine to *describe* the
  game.

## Assets: generate or create your own

The safest path — the one this project takes — is to create every asset
yourself:

- **Art:** RENGEAR draws all sprites procedurally in `rengear/game/art.py`
  (geometric pixel art). No sprite is ripped, traced or sampled.
- **Audio:** all sounds and the music loop are synthesised from oscillators in
  `rengear/engine/audio.py`. No sample is used.
- **Tracks and cars:** invented names and layouts, generated or scripted by
  this project's own code.
- **Fonts:** only pygame's bundled default font is used.
- **Code:** written from scratch; no proprietary SDKs or leaked source.

If you add third-party assets, check their licences — they must be compatible
with the GPL (e.g. CC0, CC-BY, GPL).

## Names

| Risk if copied            | RENGEAR's original choice          |
|---------------------------|------------------------------------|
| "Top Gear"                | **RENGEAR**                        |
| real car marques          | **Spark, Comet, Vulcan, Dune**     |
| real circuits/countries   | **Nara Coast, Dusk Canyon, …**     |

Characters, names, track designs and world-building are creative expression —
make them yours.

## Checklist before publishing

- [ ] Original title, with no protected words or lookalike logos.
- [ ] No real car brands, names or designs.
- [ ] All sprites, sounds and music created by you or properly licensed.
- [ ] No data ripped from a commercial ROM (tracks, text, sprites, audio).
- [ ] Mechanics re-implemented from scratch (you may take inspiration freely).
- [ ] A clear licence for your own work (this project: **GPL-3.0-or-later**).
- [ ] Reasonable effort made to avoid consumer confusion with any existing IP.

## About this project's licence

RENGEAR's source is licensed **GPL-3.0-or-later** (see `LICENSE`). The
procedurally generated graphics and audio are produced by that same GPL code,
so they are distributed under the same terms. You may study, modify and
redistribute the game as long as derivative works remain free under the GPL.

## Do not

- Do not rename this project to anything containing another company's or car
  maker's trademark.
- Do not add ripped assets to a fork and redistribute it; that would infringe
  others' rights regardless of the GPL.
- Do not imply that this project is endorsed by or affiliated with any existing
  game or company.
