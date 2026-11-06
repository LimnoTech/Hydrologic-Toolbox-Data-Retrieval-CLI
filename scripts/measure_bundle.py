"""Zip a PyInstaller bundle and time its ``--help``; print one Markdown row.

Usage: ``measure_bundle.py <bundle_dir> <exe_path> [--label TEXT]``. The zip is
written next to ``<bundle_dir>`` as ``<bundle_dir name>.zip``. Exits non-zero
if the exe's ``--help`` fails, after printing one line to stderr. Sizes are decimal MB
(10^6 bytes).
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
    args = parser.parse_args(argv)

    zip_path = zip_bundle(args.bundle_dir)
    try:
        seconds = best_help_time(args.exe_path)
    except FileNotFoundError:
        print(f"measure_bundle: {args.exe_path} not found", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(
            f"measure_bundle: {args.exe_path} --help exited {error.returncode}",
            file=sys.stderr,
        )
        return 1
    print(format_row(args.label, zip_path.stat().st_size / 1_000_000, seconds))
    return 0


if __name__ == "__main__":
    sys.exit(main())
