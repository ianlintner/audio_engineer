"""Drummer agent - generates drum tracks using pattern repository."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.patterns import PatternRepository, DrumPattern, DrumFill
from audio_engineer.core.constants import GM_DRUMS, TICKS_PER_BEAT
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext


# Sections that get crash cymbals on the downbeat
_ACCENT_SECTIONS = {"chorus", "bridge", "solo", "outro"}
# Sections where half-time feel is preferred
_HALF_TIME_SECTIONS = {"intro", "outro", "breakdown"}


class DrummerAgent(BaseMusician):
    """Generates drum tracks by combining patterns, fills, and accents."""

    def __init__(self, llm: Any = None):
        super().__init__(instrument=Instrument.DRUMS, channel=9, llm=llm)
        self.pattern_repo = PatternRepository()

    def generate_part(self, context: SessionContext) -> MidiTrackData:
        genre = context.config.genre
        tc = TickConverter(time_sig=context.config.time_signature)

        sections = self._get_section_bars(context)
        patterns = self.pattern_repo.get_drum_patterns(genre)
        fills = self.pattern_repo.get_drum_fills(genre)

        # Fallback patterns if genre has none registered
        if not patterns:
            patterns = self.pattern_repo.get_drum_patterns(Genre.CLASSIC_ROCK)
        if not fills:
            fills = self.pattern_repo.get_drum_fills(Genre.CLASSIC_ROCK)

        all_events: list[NoteEvent] = []

        for sec_idx, (sec_name, start_bar, num_bars, intensity) in enumerate(sections):
            pattern = self._select_pattern(patterns, sec_name, intensity)
            fill = self._select_fill(fills, intensity) if fills else None

            # Determine if next section is different (trigger fill)
            is_last_section_occurrence = (
                sec_idx + 1 >= len(sections)
                or sections[sec_idx + 1][0] != sec_name
            )

            for bar_idx in range(num_bars):
                abs_bar = start_bar + bar_idx
                is_last_bar = bar_idx == num_bars - 1
                is_first_bar = bar_idx == 0

                # Place fill on last bar before section change
                if is_last_bar and is_last_section_occurrence and fill and num_bars > 1:
                    # Use pattern for first 2 beats, fill for last 2
                    bar_events = pattern.to_events(bar_offset=abs_bar, intensity=intensity)
                    # Keep only first half of pattern
                    half_bar_tick = abs_bar * tc.ticks_per_bar + tc.ticks_per_bar // 2
                    bar_events = [e for e in bar_events if e.start_tick < half_bar_tick]
                    # Add fill on beats 3-4
                    fill_events = fill.to_events(bar_offset=abs_bar, beat_start=3.0)
                    fill_events = self._scale_velocity(fill_events, intensity)
                    bar_events.extend(fill_events)
                    all_events.extend(bar_events)
                else:
                    bar_events = pattern.to_events(bar_offset=abs_bar, intensity=intensity)
                    all_events.extend(bar_events)

                # Crash on downbeat of accent sections (first bar)
                if is_first_bar and sec_name.lower() in _ACCENT_SECTIONS:
                    crash_tick = abs_bar * tc.ticks_per_bar
                    crash_vel = min(127, int(110 * intensity))
                    all_events.append(NoteEvent(
                        pitch=GM_DRUMS["crash"],
                        velocity=crash_vel,
                        start_tick=crash_tick,
                        duration_ticks=TICKS_PER_BEAT,
                        channel=9,
                    ))

                # Also crash on first bar after a fill (next section start)
                # This is handled by the accent check above for chorus/etc.

        # Sort events by start_tick
        all_events.sort(key=lambda e: e.start_tick)

        return MidiTrackData(
            name="Drums",
            instrument=Instrument.DRUMS,
            channel=9,
            events=all_events,
            program=0,  # drums ignore program
        )

    def _select_pattern(
        self, patterns: list[DrumPattern], section_name: str, intensity: float
    ) -> DrumPattern:
        """Select a pattern based on section and intensity heuristics."""
        if not patterns:
            raise ValueError("No drum patterns available")

        # LLM-enhanced selection
        if self.llm is not None:
            return self._llm_select_pattern(patterns, section_name, intensity)

        # Heuristic: low intensity or half-time sections -> simpler pattern
        section_lower = section_name.lower()
        if section_lower in _HALF_TIME_SECTIONS and intensity < 0.6:
            # Prefer half-time or simpler patterns
            for p in patterns:
                if "half" in p.name or "slow" in p.name:
                    return p
            return patterns[0]

        # High intensity -> busier pattern
        if intensity >= 0.8:
            for p in patterns:
                if "driving" in p.name or "four" in p.name:
                    return p

        # Default: first pattern (standard)
        return patterns[0]

    def _select_fill(self, fills: list[DrumFill], intensity: float) -> DrumFill:
        """Select a fill based on intensity."""
        if not fills:
            raise ValueError("No drum fills available")

        if self.llm is not None:
            return self._llm_select_fill(fills, intensity)

        # Heuristic: higher intensity -> more dramatic fill
        if intensity >= 0.8 and len(fills) > 1:
            return fills[1]  # snare_build or similar
        return fills[0]

    def _scale_velocity(self, events: list[NoteEvent], intensity: float) -> list[NoteEvent]:
        """Scale event velocities by intensity."""
        scale = max(0.3, min(1.0, intensity))
        result = []
        for e in events:
            new_vel = max(1, min(127, int(e.velocity * scale)))
            result.append(e.model_copy(update={"velocity": new_vel}))
        return result

    def _llm_select_pattern(
        self, patterns: list[DrumPattern], section_name: str, intensity: float
    ) -> DrumPattern:
        """Use LLM to choose a pattern (stub - falls back to heuristic if LLM fails)."""
        try:
            names = [p.name for p in patterns]
            prompt = (
                f"Choose the best drum pattern for a '{section_name}' section "
                f"with intensity {intensity:.1f}. Options: {names}. "
                f"Reply with just the pattern name."
            )
            response = self.llm(prompt) if callable(self.llm) else str(self.llm)
            for p in patterns:
                if p.name in response:
                    return p
        except Exception:
            pass
        return self._select_pattern.__wrapped__(self, patterns, section_name, intensity) if hasattr(self._select_pattern, '__wrapped__') else patterns[0]

    def _llm_select_fill(self, fills: list[DrumFill], intensity: float) -> DrumFill:
        """Use LLM to choose a fill (stub)."""
        try:
            names = [f.name for f in fills]
            prompt = (
                f"Choose a drum fill for intensity {intensity:.1f}. "
                f"Options: {names}. Reply with just the fill name."
            )
            response = self.llm(prompt) if callable(self.llm) else str(self.llm)
            for f in fills:
                if f.name in response:
                    return f
        except Exception:
            pass
        return fills[0]
