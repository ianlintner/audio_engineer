"""Compose multiple AudioTracks (MIDI + audio) into layered output."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from audio_engineer.core.audio_track import AudioTrack, TrackType
from audio_engineer.core.midi_engine import MidiEngine

logger = logging.getLogger(__name__)


class TrackComposer:
    """Collects AudioTracks and exports them as layered stems.

    MIDI tracks are merged into a single .mid file.
    Audio tracks are exported as individual stem files.
    """

    def __init__(self) -> None:
        self.tracks: list[AudioTrack] = []
        self._midi_engine = MidiEngine()

    def add_track(self, track: AudioTrack) -> None:
        self.tracks.append(track)

    def clear(self) -> None:
        self.tracks.clear()

    def get_midi_tracks(self) -> list[AudioTrack]:
        return [t for t in self.tracks if t.track_type == TrackType.MIDI]

    def get_audio_tracks(self) -> list[AudioTrack]:
        return [t for t in self.tracks if t.track_type == TrackType.AUDIO]

    def export_midi(self, path: Path | str, tempo: int = 120) -> Path:
        """Merge all MIDI tracks into a single .mid file."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        midi_tracks = [t.midi_data for t in self.get_midi_tracks() if t.midi_data]
        if not midi_tracks:
            raise ValueError("No MIDI tracks to export")

        midi_file = self._midi_engine.merge_tracks(midi_tracks, tempo)
        self._midi_engine.export_midi(midi_file, out)
        logger.info("Exported MIDI: %s (%d tracks)", out, len(midi_tracks))
        return out

    def export_audio_stems(self, directory: Path | str) -> list[Path]:
        """Save each audio track as an individual stem file."""
        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        stems: list[Path] = []
        seen: set[str] = set()

        for track in self.get_audio_tracks():
            if not track.has_audio:
                continue
            ext = _mime_to_ext(track.mime_type)
            safe_name = re.sub(r'[^\w\-.]', '_', track.name)
            base = f"{safe_name}{ext}"
            if base in seen:
                counter = 2
                while f"{safe_name}_{counter}{ext}" in seen:
                    counter += 1
                base = f"{safe_name}_{counter}{ext}"
            seen.add(base)
            stem_path = out_dir / base
            track.save_audio(stem_path)
            stems.append(stem_path)
            logger.info("Exported audio stem: %s", stem_path)

        return stems

    def export_all(self, directory: Path | str, tempo: int = 120) -> list[Path]:
        """Export both MIDI and audio stems to a directory."""
        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []

        # MIDI
        midi_tracks = self.get_midi_tracks()
        if midi_tracks:
            midi_path = out_dir / "combined.mid"
            self.export_midi(midi_path, tempo)
            files.append(midi_path)

        # Audio stems
        files.extend(self.export_audio_stems(out_dir))

        return files

    def manifest(self) -> list[dict]:
        """Return a summary of all tracks for serialization."""
        return [
            {
                "name": t.name,
                "type": t.track_type.value,
                "provider": t.provider,
                "has_data": t.has_audio or t.has_midi,
                "tags": t.tags,
            }
            for t in self.tracks
        ]


def _mime_to_ext(mime_type: str) -> str:
    mapping = {
        "audio/mp3": ".mp3",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/flac": ".flac",
        "audio/ogg": ".ogg",
        "audio/aac": ".aac",
    }
    return mapping.get(mime_type) or _fallback_ext(mime_type)


def _fallback_ext(mime_type: str) -> str:
    logger.warning("Unknown MIME type %r, falling back to .bin", mime_type)
    return ".bin"
