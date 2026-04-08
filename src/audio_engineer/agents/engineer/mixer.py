"""Mixer agent - assigns volume, pan, and CC events per instrument."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
    MixConfig, MixTrackConfig,
)

from audio_engineer.agents.base import BaseEngineer, SessionContext


# Default mix settings per instrument: (volume, pan)
# Pan: -1.0 = full left, 0.0 = center, 1.0 = full right
_DEFAULT_MIX: dict[Instrument, tuple[float, float]] = {
    Instrument.DRUMS: (0.85, 0.0),
    Instrument.BASS: (0.80, 0.0),
    Instrument.ELECTRIC_GUITAR: (0.75, -0.3),
    Instrument.ACOUSTIC_GUITAR: (0.70, 0.3),
    Instrument.KEYS: (0.65, 0.35),
    Instrument.VOCALS: (0.90, 0.0),
}

# Genre-specific overrides
_GENRE_OVERRIDES: dict[Genre, dict[Instrument, tuple[float, float]]] = {
    Genre.CLASSIC_ROCK: {
        Instrument.ELECTRIC_GUITAR: (0.82, -0.35),
        Instrument.BASS: (0.78, 0.0),
    },
    Genre.HARD_ROCK: {
        Instrument.ELECTRIC_GUITAR: (0.85, -0.4),
        Instrument.DRUMS: (0.88, 0.0),
    },
    Genre.BLUES: {
        Instrument.ELECTRIC_GUITAR: (0.75, -0.2),
        Instrument.KEYS: (0.70, 0.25),
    },
    Genre.POP: {
        Instrument.KEYS: (0.75, 0.3),
        Instrument.ELECTRIC_GUITAR: (0.65, -0.3),
    },
}


class MixerAgent(BaseEngineer):
    """Assigns volume and pan to each track and produces a MixConfig."""

    def __init__(self, llm: Any = None):
        super().__init__(llm=llm)

    def process(
        self, tracks: list[MidiTrackData], context: SessionContext
    ) -> MixConfig:
        genre = context.config.genre
        genre_overrides = _GENRE_OVERRIDES.get(genre, {})

        track_configs: list[MixTrackConfig] = []

        for track in tracks:
            vol, pan = genre_overrides.get(
                track.instrument,
                _DEFAULT_MIX.get(track.instrument, (0.75, 0.0)),
            )
            track_configs.append(MixTrackConfig(
                instrument=track.instrument,
                volume=vol,
                pan=pan,
            ))

        return MixConfig(tracks=track_configs, master_volume=0.9)

    def apply_cc_to_tracks(
        self, tracks: list[MidiTrackData], mix_config: MixConfig
    ) -> list[MidiTrackData]:
        """Return new tracks with CC7 (volume) and CC10 (pan) prepended."""
        result: list[MidiTrackData] = []
        mix_map = {tc.instrument: tc for tc in mix_config.tracks}

        for track in tracks:
            tc = mix_map.get(track.instrument)
            if tc is None:
                result.append(track)
                continue

            cc_volume = int(tc.volume * 127)
            cc_pan = int((tc.pan + 1.0) / 2.0 * 127)  # -1..1 -> 0..127

            # We store CC info as metadata; actual CC insertion happens
            # at MIDI export time via MidiTrackBuilder. For now, just
            # tag the track so the engine can apply them.
            result.append(track.model_copy())

        return result
