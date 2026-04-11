"""Audio format conversion utilities using pydub."""
from __future__ import annotations

import shutil
from pathlib import Path


def wav_to_mp3(wav_path: Path, mp3_path: Path | None = None, bitrate: str = "192k") -> Path:
    """Convert a WAV file to MP3 using pydub (requires ffmpeg).

    Args:
        wav_path: Path to the source WAV file.
        mp3_path: Destination path. Defaults to the same name with .mp3 suffix.
        bitrate: MP3 bitrate (e.g. "128k", "192k", "320k").

    Returns:
        Path to the created MP3 file.

    Raises:
        ImportError: If pydub is not installed.
        FileNotFoundError: If the WAV file or ffmpeg is not found.
        RuntimeError: If the conversion fails.
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError(
            "pydub is required for MP3 export. Install with:\n"
            "  pip install audio-engineer[audio]"
        )

    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    if shutil.which("ffmpeg") is None and shutil.which("avconv") is None:
        raise FileNotFoundError(
            "ffmpeg (or avconv) is required for MP3 export. Install with:\n"
            "  brew install ffmpeg   (macOS)\n"
            "  apt install ffmpeg    (Linux)"
        )

    if mp3_path is None:
        mp3_path = wav_path.with_suffix(".mp3")

    mp3_path.parent.mkdir(parents=True, exist_ok=True)

    audio = AudioSegment.from_wav(str(wav_path))
    audio.export(str(mp3_path), format="mp3", bitrate=bitrate)
    return mp3_path
