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
        output_path = output_path.with_suffix(".wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "timidity",
            str(midi_path),
            "-Ow",
            "-o", str(output_path),
            "--output-stereo",
            "-s", str(cfg.sample_rate),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"timidity failed: {result.stderr.strip()}")
        return output_path

    def is_available(self) -> bool:
        return shutil.which("timidity") is not None

    def supported_formats(self) -> list[AudioFormat]:
        return [AudioFormat.WAV]

    def get_info(self) -> DAWInfo:
        return DAWInfo(
            name="TiMidity++",
            tier=1,
            platform="all",
            available=self.is_available(),
        )
