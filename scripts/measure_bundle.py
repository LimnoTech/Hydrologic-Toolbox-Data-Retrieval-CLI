"""Zip a PyInstaller bundle and time its ``--help``; print one Markdown row.

Usage: ``measure_bundle.py <bundle_dir> <exe_path> [--label TEXT] [--max-mb MB]``.
The zip is written next to ``<bundle_dir>`` as ``<bundle_dir name>.zip``, and only
after the exe's ``--help`` has run. Exits 1 with one line on stderr if the bundle
directory or exe is missing, ``--help`` fails, or a file operation fails. Sizes are
decimal MB (10^6 bytes). With ``--max-mb``, a zip over that size still prints its
row, then one stderr line, and exits 1.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


def format_row(label: str, zip_mb: float, seconds: float) -> str:
    """Return the Markdown table row for one measurement."""
    return f"| {label} | {zip_mb:.1f} | {seconds:.2f} |"


def zip_bundle(bundle_dir: Path) -> Path:
    """Zip ``bundle_dir`` beside itself and return the zip's path."""
    bundle_dir = Path(bundle_dir)
    archive = shutil.make_archive(
        str(bundle_dir), "zip", root_dir=bundle_dir.parent, base_dir=bundle_dir.name
    )
    return Path(archive)


def best_help_time(exe: Path, runs: int = 5) -> float:
    """Return the fastest of ``runs`` timings of ``exe --help``, in seconds."""
    best = float("inf")
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run([exe, "--help"], check=True, capture_output=True)
        best = min(best, time.perf_counter() - start)
    return best


def main(argv: list[str] | None = None) -> int:
    """Measure a bundle and print its row."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("exe_path", type=Path)
    parser.add_argument("--label", default="bundle")
    parser.add_argument("--max-mb", type=float, default=None)
    args = parser.parse_args(argv)

    # Everything that can fail is checked before the zip is written, so a failure
    # leaves no stray zip behind. Each failure is one stderr line and exit 1.
    if not args.bundle_dir.is_dir():
        print(
            f"measure_bundle: bundle directory {args.bundle_dir} not found",
            file=sys.stderr,
        )
        return 1
    if not args.exe_path.is_file():
        print(f"measure_bundle: {args.exe_path} not found", file=sys.stderr)
        return 1
    try:
        seconds = best_help_time(args.exe_path)
        zip_path = zip_bundle(args.bundle_dir)
        zip_mb = zip_path.stat().st_size / 1_000_000
    except subprocess.CalledProcessError as error:
        print(
            f"measure_bundle: {args.exe_path} --help exited {error.returncode}",
            file=sys.stderr,
        )
        return 1
    except OSError as error:
        print(f"measure_bundle: {error}", file=sys.stderr)
        return 1
    # Flush so the row reaches the terminal before the stderr line below.
    print(format_row(args.label, zip_mb, seconds), flush=True)
    if args.max_mb is not None and zip_mb > args.max_mb:
        print(
            f"bundle zip is {zip_mb:.2f} MB, over the {args.max_mb:g} MB limit",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
