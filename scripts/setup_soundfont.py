#!/usr/bin/env python3
"""Download a free General MIDI SoundFont for use with FluidSynth."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

SOUNDFONT_DIR = Path.home() / ".audio_engineer" / "soundfonts"
SOUNDFONT_NAME = "FluidR3_GM.sf2"
SOUNDFONT_URL = (
    "https://keymusician01.s3.amazonaws.com/FluidR3_GM.sf2"
)


def _progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100.0, downloaded / total_size * 100)
        mb_done = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\r  {mb_done:.1f}/{mb_total:.1f} MB ({pct:.0f}%)")
    else:
        mb_done = downloaded / (1024 * 1024)
        sys.stdout.write(f"\r  {mb_done:.1f} MB downloaded")
    sys.stdout.flush()


def main() -> None:
    dest = SOUNDFONT_DIR / SOUNDFONT_NAME

    if dest.exists():
        print(f"SoundFont already exists: {dest}")
        print(f"  Size: {dest.stat().st_size / (1024*1024):.1f} MB")
        return

    SOUNDFONT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {SOUNDFONT_NAME}...")
    print(f"  URL: {SOUNDFONT_URL}")
    print(f"  Destination: {dest}")

    try:
        urllib.request.urlretrieve(SOUNDFONT_URL, dest, reporthook=_progress_hook)
        print()  # newline after progress
    except Exception as exc:
        # Clean up partial download
        if dest.exists():
            dest.unlink()
        print(f"\nDownload failed: {exc}", file=sys.stderr)
        print("You can manually download a GM SoundFont and place it at:", file=sys.stderr)
        print(f"  {dest}", file=sys.stderr)
        sys.exit(1)

    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"Done! SoundFont saved ({size_mb:.1f} MB)")
    print(f"Set AUDIO_ENGINEER_SOUNDFONT_PATH={dest} or it will be auto-detected.")


if __name__ == "__main__":
    main()
