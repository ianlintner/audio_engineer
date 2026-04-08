"""File export backend (Tier 3) - always available MIDI export."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..core.models import RenderConfig, MidiTrackData
from .base import AudioFormat, DAWBackend, DAWInfo


class FileExportBackend(DAWBackend):
    """Tier 3 backend that exports MIDI files directly. Always available."""

    def export_midi(self, midi_path: Path, output_dir: Path) -> Path:
        """Copy a MIDI file to the output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        dest = output_dir / midi_path.name
        shutil.copy2(midi_path, dest)
        return dest

    def export_tracks(
        self, tracks: dict[str, MidiTrackData], output_dir: Path
    ) -> list[Path]:
        """Export individual track MIDI files to the output directory."""
        from ..core.midi_engine import MidiEngine

        output_dir.mkdir(parents=True, exist_ok=True)
        engine = MidiEngine()
        exported: list[Path] = []
        for name, track_data in tracks.items():
            track_path = output_dir / f"{name}.mid"
            engine.render_to_file([track_data], track_path)
            exported.append(track_path)
        return exported

    def render_audio(
        self, midi_path: Path, output_path: Path, config: RenderConfig | None = None
    ) -> Path:
        """Not supported - MIDI export only.

        Raises:
            NotImplementedError: Always. Use FluidSynthBackend for audio rendering.
        """
        raise NotImplementedError(
            "FileExportBackend only supports MIDI export. "
            "Install FluidSynth for audio rendering: "
            "  brew install fluid-synth   (macOS)\n"
            "  apt install fluidsynth     (Linux)\n"
            "Then use FluidSynthBackend or set preferred_backend='fluidsynth'."
        )

    def is_available(self) -> bool:
        return True

    def supported_formats(self) -> list[AudioFormat]:
        return []

    def get_info(self) -> DAWInfo:
        return DAWInfo(
            name="FileExport",
            version="1.0",
            tier=3,
            platform="all",
            available=True,
        )
