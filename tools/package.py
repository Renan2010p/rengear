"""Build a distributable ``.zip`` of RENGEAR for the current platform.

It freezes ``main.py`` with PyInstaller into a self-contained folder, adds the
licence, readme and convenience launchers, then zips the result as
``rengear-<platform>.zip`` in the repository root.  The release workflow runs
this on Windows and Linux and attaches both zips to a GitHub Release.

    python -m pip install pyinstaller
    python -m tools.package
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

LINUX_LAUNCHER = """#!/usr/bin/env bash
# Launch RENGEAR (packaged build).
set -e
cd "$(dirname "$0")"
exec ./rengear "$@"
"""

WINDOWS_LAUNCHER = (
    "@echo off\r\n"
    "rem Launch RENGEAR (packaged build).\r\n"
    'cd /d "%~dp0"\r\n'
    "rengear.exe %*\r\n"
)


def platform_tag() -> str:
    if sys.platform.startswith("win"):
        return "windows-x64"
    if sys.platform == "darwin":
        return "macos"
    return "linux-x64"


def build() -> Path:
    """Run PyInstaller and decorate the output folder."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:  # pragma: no cover - developer feedback
        raise SystemExit("PyInstaller is required: python -m pip install pyinstaller")

    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--name", "rengear", "--onedir",
        "--paths", str(ROOT),
        "--collect-submodules", "rengear",
    ]
    if sys.platform.startswith("win"):
        args.append("--noconsole")
    args.append(str(ROOT / "main.py"))
    subprocess.check_call(args, cwd=ROOT)

    app = DIST / "rengear"
    if not app.is_dir():
        raise SystemExit(f"PyInstaller did not produce {app}")

    for extra in ("LICENSE", "README.md"):
        src = ROOT / extra
        if src.exists():
            shutil.copy2(src, app / extra)

    (app / "rengear.sh").write_text(LINUX_LAUNCHER, encoding="utf-8")
    (app / "rengear.bat").write_text(WINDOWS_LAUNCHER, encoding="utf-8")
    os.chmod(app / "rengear.sh", 0o755)
    return app


def make_zip(app: Path) -> Path:
    out = ROOT / f"rengear-{platform_tag()}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                archive.write(path, Path("rengear") / path.relative_to(app))
    return out


def main() -> int:
    app = build()
    out = make_zip(app)
    size = out.stat().st_size / (1024 * 1024)
    print(f"wrote {out} ({size:.1f} MiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
