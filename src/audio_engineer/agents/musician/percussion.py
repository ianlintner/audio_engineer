"""Percussion agent — ethnic / hand drum patterns (conga, bongo, djembe)."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.constants import GM_DRUMS, TICKS_PER_BEAT

from audio_engineer.agents.base import BaseMusician, SessionContext


# Latin / Afro-Cuban hand drum patterns expressed as (drum_key, beat_position) lists
_CONGA_PATTERNS: dict[Genre, list[tuple[str, float, int]]] = {
    Genre.LATIN: [
        ("open_hi_conga", 1.0, 90), ("mute_hi_conga", 1.5, 75),
        ("open_hi_conga", 2.0, 85), ("low_conga", 2.5, 80),
        ("open_hi_conga", 3.0, 90), ("mute_hi_conga", 3.5, 70),
        ("low_conga", 4.0, 85), ("open_hi_conga", 4.5, 80),
    ],
    Genre.BOSSA_NOVA: [
        ("open_hi_conga", 1.0, 80), ("low_conga", 1.75, 70),
        ("open_hi_conga", 2.5, 78), ("mute_hi_conga", 3.0, 65),
        ("open_hi_conga", 3.5, 80), ("low_conga", 4.25, 72),
    ],
    Genre.FUNK: [
        ("open_hi_conga", 1.0, 95), ("mute_hi_conga", 1.25, 70),
        ("low_conga", 1.75, 85), ("open_hi_conga", 2.25, 80),
        ("open_hi_conga", 3.0, 95), ("mute_hi_conga", 3.25, 68),
        ("low_conga", 3.75, 82), ("open_hi_conga", 4.5, 78),
    ],
}

_BONGO_PATTERNS: dict[Genre, list[tuple[str, float, int]]] = {
    Genre.LATIN: [
        ("hi_bongo", 1.0, 90), ("hi_bongo", 1.5, 80),
        ("low_bongo", 2.0, 85), ("hi_bongo", 2.5, 75),
        ("hi_bongo", 3.0, 88), ("low_bongo", 3.33, 70),
        ("hi_bongo", 3.67, 78), ("low_bongo", 4.0, 85),
        ("hi_bongo", 4.5, 80),
    ],
    Genre.BOSSA_NOVA: [
        ("hi_bongo", 1.0, 82), ("low_bongo", 1.5, 72),
        ("hi_bongo", 2.25, 80), ("hi_bongo", 3.0, 85),
        ("low_bongo", 3.5, 70), ("hi_bongo", 4.25, 78),
    ],
}

_DJEMBE_PATTERNS: dict[Genre, list[tuple[str, float, int]]] = {
    Genre.FUNK: [
        ("open_hi_conga", 1.0, 95), ("low_conga", 1.5, 80),
        ("open_hi_conga", 2.25, 90), ("low_conga", 3.0, 85),
        ("open_hi_conga", 3.5, 92), ("low_conga", 4.0, 80),
        ("open_hi_conga", 4.5, 88),
    ],
    Genre.LATIN: [
        ("open_hi_conga", 1.0, 92), ("low_conga", 1.67, 78),
        ("open_hi_conga", 2.33, 85), ("low_conga", 3.0, 80),
        ("open_hi_conga", 3.67, 90), ("low_conga", 4.33, 75),
    ],
}

# Default fallback pattern when genre has nothing specific
_DEFAULT_PATTERN: list[tuple[str, float, int]] = [
    ("open_hi_conga", 1.0, 88), ("low_conga", 2.0, 80),
    ("open_hi_conga", 3.0, 88), ("low_conga", 4.0, 80),
]


class PercussionAgent(BaseMusician):
    """Generates ethnic / hand drum patterns for conga, bongo, and djembe."""

    def __init__(self, llm: Any = None, instrument: Instrument = Instrument.CONGA):
        super().__init__(instrument=instrument, channel=9, llm=llm)

    def generate_part(self, context: SessionContext) -> MidiTrackData:
        genre = context.config.genre
        tc_beats_per_bar = context.config.time_signature.numerator
        tpb = TICKS_PER_BEAT

        sections = self._get_section_bars(context)
        pattern = self._select_pattern(genre)
        all_events: list[NoteEvent] = []

        for _sec_name, start_bar, num_bars, intensity in sections:
            vel_scale = max(0.3, min(1.0, intensity))
            for bar_idx in range(num_bars):
                abs_bar = start_bar + bar_idx
                bar_start = abs_bar * tpb * tc_beats_per_bar
                for drum_key, beat_pos, base_vel in pattern:
                    if drum_key not in GM_DRUMS:
                        continue
                    tick = bar_start + int((beat_pos - 1.0) * tpb)
                    vel = max(1, min(127, int(base_vel * vel_scale)))
                    all_events.append(NoteEvent(
                        pitch=GM_DRUMS[drum_key],
                        velocity=vel,
                        start_tick=tick,
                        duration_ticks=tpb // 4,
                        channel=9,
                    ))

        all_events.sort(key=lambda e: e.start_tick)

        return MidiTrackData(
            name="Percussion",
            instrument=self.instrument,
            channel=9,
            events=all_events,
            program=0,
        )

    def _select_pattern(self, genre: Genre) -> list[tuple[str, float, int]]:
        if self.instrument == Instrument.BONGO:
            return _BONGO_PATTERNS.get(genre) or next(iter(_BONGO_PATTERNS.values()), _DEFAULT_PATTERN)
        if self.instrument == Instrument.DJEMBE:
            return _DJEMBE_PATTERNS.get(genre) or next(iter(_DJEMBE_PATTERNS.values()), _DEFAULT_PATTERN)
        if self.instrument == Instrument.TABLA:
            # Tabla uses similar mapping to bongos (hi/low pair)
            return _BONGO_PATTERNS.get(genre) or next(iter(_BONGO_PATTERNS.values()), _DEFAULT_PATTERN)
        if self.instrument == Instrument.STEEL_DRUMS:
            # Steel drums use a simple rhythmic pattern
            return _DEFAULT_PATTERN
        # CONGA or PERCUSSION
        return _CONGA_PATTERNS.get(genre, _DEFAULT_PATTERN)
