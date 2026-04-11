"""FluidSynth backend (Tier 1) - renders MIDI to audio via fluidsynth CLI."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..core.models import RenderConfig
from .base import AudioFormat, DAWBackend, DAWInfo

_SOUNDFONT_DIRS = [
    Path("/usr/share/sounds/sf2"),
    Path("/usr/share/soundfonts"),
    Path("/usr/local/share/fluidsynth"),
    Path("/opt/homebrew/share/soundfonts"),
    Path.home() / ".audio_engineer" / "soundfonts",
]

_SOUNDFONT_NAMES = [
    "FluidR3_GM.sf2",
    "FluidR3_GM2-2.sf2",
    "GeneralUser GS.sf2",
    "default.sf2",
]


class FluidSynthBackend(DAWBackend):
    """Tier 1 backend using the fluidsynth CLI to render MIDI to WAV."""

    def __init__(self, soundfont_path: str | Path | None = None):
        self._soundfont = Path(soundfont_path) if soundfont_path else None

    def _find_default_soundfont(self) -> Path | None:
        """Search common locations for a GM SoundFont."""
        for directory in _SOUNDFONT_DIRS:
            if not directory.is_dir():
                continue
            for name in _SOUNDFONT_NAMES:
                candidate = directory / name
                if candidate.is_file():
                    return candidate
            # Fall back to any .sf2 in the directory
            sf2_files = list(directory.glob("*.sf2"))
            if sf2_files:
                return sf2_files[0]
        return None

    def _get_soundfont(self) -> Path:
        sf = self._soundfont or self._find_default_soundfont()
        if sf is None or not sf.is_file():
            raise FileNotFoundError(
                "No SoundFont found. Install one with:\n"
                "  python scripts/setup_soundfont.py\n"
                "Or set AUDIO_ENGINEER_SOUNDFONT_PATH in your .env"
            )
        return sf

    def render_audio(
        self, midi_path: Path, output_path: Path, config: RenderConfig | None = None
    ) -> Path:
        cfg = config or RenderConfig()
        soundfont = self._get_soundfont()
        wav_path = output_path.with_suffix(".wav")
        wav_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "fluidsynth", "-ni",
            str(soundfont),
            str(midi_path),
            "-F", str(wav_path),
            "-r", str(cfg.sample_rate),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"fluidsynth failed: {result.stderr.strip()}")

        if cfg.format == "mp3":
            from .convert import wav_to_mp3

            mp3_path = output_path.with_suffix(".mp3")
            wav_to_mp3(wav_path, mp3_path, bitrate=cfg.mp3_bitrate)
            wav_path.unlink(missing_ok=True)
            return mp3_path

        return wav_path

    def is_available(self) -> bool:
        return shutil.which("fluidsynth") is not None

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
            name="FluidSynth",
            tier=1,
            platform="all",
            available=self.is_available(),
        )
