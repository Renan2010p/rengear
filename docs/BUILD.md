# Building and releasing

## Run from source

```bash
python -m pip install -r requirements.txt
python main.py
```

Requires **Python 3.10+** and **pygame 2.1+**.

## Build a package locally

The packaging script freezes the game with **PyInstaller** into a
self-contained folder and zips it as `rengear-<platform>.zip`:

```bash
python -m pip install pyinstaller
python -m tools.package
```

It produces `rengear-linux-x64.zip` (or `rengear-windows-x64.zip`). There is
no compilation and no third-party asset to bundle: PyInstaller collects
pygame, the `rengear` package and its modules, and the game generates every
sprite and sound at runtime.

The zip contains:

```
rengear/
  rengear         (or rengear.exe on Windows)  the game
  rengear.sh      launcher for Linux/macOS
  rengear.bat     launcher for Windows
  LICENSE
  README.md
  _internal/...   Python runtime + pygame (PyInstaller)
```

> `build/` and `dist/` are build artefacts and are git-ignored.

## Release workflow

[`.github/workflows/release.yml`](../.github/workflows/release.yml) builds the
packages on GitHub and publishes them:

1. **Trigger** — pushing a tag matching `v*` (e.g. `v0.1.0`), or manually via
   *Actions → release → Run workflow*.
2. **Build matrix** — `ubuntu-latest` and `windows-latest`. Each installs
   Python 3.12, pygame and PyInstaller, runs the test-suite, packages the zip
   and uploads it as a build artifact.
3. **Publish** — on a tag, a final job downloads both artifacts and creates a
   GitHub Release with `rengear-linux-x64.zip` and
   `rengear-windows-x64.zip` attached (release notes are generated
   automatically).

### Cut a release

```bash
git tag v0.1.0
git push origin v0.1.0
```

That is all — the workflows attach the two zips to a new Release. Manual runs
(without a tag) still produce the zips as downloadable artifacts, they just do
not create a Release.

## Continuous integration

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every push
and pull request: it installs pygame, runs `python -m tests.test_engine`
headless (`SDL_VIDEODRIVER=dummy`) and drives one full race with
`python -m tools.smoke`.

## Notes

- **Prebuilt binaries are not committed.** Builds are produced by CI to keep
  the repository source-only.
- **macOS** is not part of the matrix yet; `tools/package.py` already tags a
  `macos` build if run there.
- PyInstaller freezes the Python runtime, so the runner must build on the same
  OS family it targets. That is why the matrix builds Windows on `windows` and
  Linux on `ubuntu`.
