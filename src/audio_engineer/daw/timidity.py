"""TiMidity++ backend (Tier 1) - renders MIDI to audio via timidity CLI."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..core.models import RenderConfig
from .base import AudioFormat, DAWBackend, DAWInfo


class TiMidityBackend(DAWBackend):
    """Tier 1 backend using TiMidity++ CLI to render MIDI to WAV."""

    def render_audio(
        self, midi_path: Path, output_path: Path, config: RenderConfig | None = None
    ) -> Path:
        cfg = config or RenderConfig()
        wav_path = output_path.with_suffix(".wav")
        wav_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "timidity",
            str(midi_path),
            "-Ow",
            "-o", str(wav_path),
            "--output-stereo",
            "-s", str(cfg.sample_rate),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"timidity failed: {result.stderr.strip()}")

        if cfg.format == "mp3":
            from .convert import wav_to_mp3

            mp3_path = output_path.with_suffix(".mp3")
            wav_to_mp3(wav_path, mp3_path, bitrate=cfg.mp3_bitrate)
            wav_path.unlink(missing_ok=True)
            return mp3_path

        return wav_path

    def is_available(self) -> bool:
        return shutil.which("timidity") is not None

    def supported_formats(self) -> list[AudioFormat]:
        formats = [AudioFormat.WAV]
        try:
            from .convert import wav_to_mp3  # noqa: F401
            import shutil
            if shutil.which("ffmpeg") or shutil.which("avconv"):
                formats.append(AudioFormat.MP3)
        except ImportError:
            pass
        return formats

    def get_info(self) -> DAWInfo:
        return DAWInfo(
            name="TiMidity++",
            tier=1,
            platform="all",
            available=self.is_available(),
        )
