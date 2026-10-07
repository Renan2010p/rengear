"""Package RENGEAR to run on the **Neko** engine instead of pygame.

Builds Neko's native ``_neko`` CPython extension, bundles the game with the
``pygame``-compatible Python package that Neko provides, and writes launchers so
you can run ``./rengear`` (Linux/macOS) or ``rengear.bat`` (Windows).

    dist/rengear-neko/
        rengear          <- run this (Linux/macOS)
        rengear.bat      <- run this (Windows)
        app/
            main.py
            rengear/     game code
            pygame/      Neko's pygame layer (incl. _neko.so / _neko.pyd)
            lib/         bundled SDL2 libraries

Usage:
    python -m tools.package_neko              # build + zip
    python -m tools.package_neko --no-zip
    NEKO_DIR=/path/to/neko python -m tools.package_neko

On Windows there is no pkg-config; point the build at SDL2 explicitly:
    set SDL2_INCLUDE=C:\\SDL2\\include
    set SDL2_LIB=C:\\SDL2\\lib\\x64
    python -m tools.package_neko

Requirements: Zig, an SDL2 development environment, and Python headers on the
build machine. ``NEKO_DIR`` locates the Neko checkout (default ../../zig/neko).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
APP_NAME = "rengear-neko"
IS_WINDOWS = sys.platform.startswith("win")
EXT_NAME = "_neko.pyd" if IS_WINDOWS else "_neko.so"

LAUNCHER_SH = """#!/usr/bin/env bash
# RENGEAR on the Neko engine.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/app"
export PYTHONPATH="$DIR/app${PYTHONPATH:+:$PYTHONPATH}"
if [ -d "$DIR/app/lib" ]; then
    export LD_LIBRARY_PATH="$DIR/app/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export DYLD_LIBRARY_PATH="$DIR/app/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi
exec "${PYTHON:-python3}" "$DIR/app/main.py" "$@"
"""

LAUNCHER_BAT = """@echo off
rem RENGEAR on the Neko engine.
cd /d "%~dp0app"
set PYTHONPATH=%~dp0app;%PYTHONPATH%
set PATH=%~dp0app\\lib;%PATH%
python main.py %*
"""


def find_neko() -> Path:
    env = os.environ.get("NEKO_DIR")
    candidates = [Path(env)] if env else []
    candidates += [
        ROOT.parent.parent / "zig" / "neko",
        ROOT.parent / "neko",
        Path.home() / "Projetos" / "zig" / "neko",
    ]
    for c in candidates:
        if (c / "build.zig").is_file():
            return c.resolve()
    raise SystemExit(
        "Neko checkout not found. Set NEKO_DIR=/path/to/neko (with build.zig)."
    )


def build_extension(neko: Path) -> Path:
    args = ["zig", "build", "python", "-Doptimize=ReleaseFast"]
    if IS_WINDOWS:
        # CPython on Windows is built with MSVC; match its ABI.
        args.append("-Dtarget=x86_64-windows-msvc")

    inc = os.environ.get("PYTHON_INCLUDE") or sysconfig.get_path("include")
    if inc:
        args.append(f"-Dpython-include={inc}")
    sdl_inc = os.environ.get("SDL2_INCLUDE")
    sdl_lib = os.environ.get("SDL2_LIB")
    if sdl_inc:
        args.append(f"-Dsdl2-include={sdl_inc}")
    if sdl_lib:
        args.append(f"-Dsdl2-lib={sdl_lib}")

    print(f"[neko] {' '.join(args)}  (cwd {neko})")
    subprocess.check_call(args, cwd=str(neko))

    pkg = neko / "zig-out" / "python" / "pygame"
    if not (pkg / "_neko.so").is_file():
        raise SystemExit(f"Neko did not produce {pkg / '_neko.so'}")
    return pkg


def _ignore(_dir, names):
    return [n for n in names if n == "__pycache__" or n.endswith(".pyc")]


def bundle_libs(code: Path, sdl2_lib: str | None) -> None:
    """Copy the SDL2 shared libraries next to the game (best effort)."""
    libdir = code / "lib"
    if IS_WINDOWS:
        dll_dir = os.environ.get("SDL2_BIN") or sdl2_lib
        if not dll_dir:
            return
        for dll in Path(dll_dir).glob("*.dll"):
            libdir.mkdir(exist_ok=True)
            shutil.copy2(dll, libdir / dll.name)
        return
    so = code / "pygame" / "_neko.so"
    try:
        out = subprocess.run(["ldd", str(so)], capture_output=True, text=True,
                             check=False).stdout
    except OSError:
        return
    for line in out.splitlines():
        if "=>" not in line:
            continue
        path = line.split("=>")[1].strip().split(" ")[0]
        name = os.path.basename(path)
        if path.startswith("/") and name.startswith("libSDL2"):
            libdir.mkdir(exist_ok=True)
            try:
                shutil.copy2(path, libdir / name)
            except OSError:
                pass


def build() -> Path:
    neko = find_neko()
    pygame_pkg = build_extension(neko)

    app = DIST / APP_NAME
    if app.exists():
        shutil.rmtree(app)
    code = app / "app"
    code.mkdir(parents=True)

    shutil.copy2(ROOT / "main.py", code / "main.py")
    shutil.copytree(ROOT / "rengear", code / "rengear", ignore=_ignore)
    shutil.copytree(pygame_pkg, code / "pygame", ignore=_ignore)

    # On Windows Python only imports ``.pyd`` extensions.
    if IS_WINDOWS:
        so = code / "pygame" / "_neko.so"
        if so.is_file():
            so.replace(code / "pygame" / EXT_NAME)

    bundle_libs(code, os.environ.get("SDL2_LIB"))

    for extra in ("LICENSE", "README.md"):
        src = ROOT / extra
        if src.exists():
            shutil.copy2(src, app / extra)

    sh = app / "rengear"
    sh.write_text(LAUNCHER_SH, encoding="utf-8")
    os.chmod(sh, 0o755)
    (app / "rengear.bat").write_text(LAUNCHER_BAT, encoding="utf-8")
    return app


def platform_tag() -> str:
    if IS_WINDOWS:
        return "windows-x64"
    if sys.platform == "darwin":
        return "macos"
    return "linux-x64"


def make_zip(app: Path) -> Path:
    out = ROOT / f"rengear-neko-{platform_tag()}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app.rglob("*")):
            if path.is_file() and path.suffix != ".pyc":
                archive.write(path, Path(APP_NAME) / path.relative_to(app))
    return out


def main() -> int:
    do_zip = "--no-zip" not in sys.argv
    app = build()
    print(f"\nBuilt {app}")
    print(f"Run: {app / ('rengear.bat' if IS_WINDOWS else 'rengear')}")
    if do_zip:
        out = make_zip(app)
        size = out.stat().st_size / (1024 * 1024)
        print(f"wrote {out} ({size:.1f} MiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
