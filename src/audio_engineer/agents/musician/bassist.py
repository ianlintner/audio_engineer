"""Bassist agent - generates bass lines following chord progressions."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import (
    ChordProgression, Chord, Scale, note_name_to_midi,
)
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext


class BassistAgent(BaseMusician):
    """Generates bass lines following chord roots with rhythmic variation."""

    def __init__(self, llm: Any = None):
        super().__init__(instrument=Instrument.BASS, channel=1, llm=llm)

    def generate_part(self, context: SessionContext) -> MidiTrackData:
        genre = context.config.genre
        tc = TickConverter(time_sig=context.config.time_signature)
        key = context.config.key
        scale = Scale(key.root.value, key.mode.value)

        sections = self._get_section_bars(context)
        all_events: list[NoteEvent] = []

        # Get kick pattern ticks for sync (if drums already generated)
        kick_beats = self._extract_kick_beats(context, tc)

        for sec_name, start_bar, num_bars, intensity in sections:
            progression = self._get_progression(context, sec_name, genre, key)
            chords = progression.chords
            total_section_beats = num_bars * tc.beats_per_bar

            # Walk through the chord progression, repeating as needed
            beat_cursor = 0.0
            chord_idx = 0
            while beat_cursor < total_section_beats:
                chord, chord_dur = chords[chord_idx % len(chords)]
                # Clamp duration to remaining beats
                remaining = total_section_beats - beat_cursor
                dur = min(chord_dur, remaining)

                root_midi = note_name_to_midi(chord.root, 2)  # bass octave

                events = self._generate_bass_for_chord(
                    root_midi=root_midi,
                    chord=chord,
                    scale=scale,
                    start_tick=tc.beats_to_ticks(beat_cursor) + start_bar * tc.ticks_per_bar,
                    duration_beats=dur,
                    intensity=intensity,
                    tc=tc,
                    kick_beats=kick_beats,
                    genre=genre,
                )
                all_events.extend(events)

                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)

        program = GM_PROGRAMS["electric_bass_pick"] if genre in (Genre.CLASSIC_ROCK, Genre.PUNK, Genre.HARD_ROCK) else GM_PROGRAMS["electric_bass_finger"]

        return MidiTrackData(
            name="Bass",
            instrument=Instrument.BASS,
            channel=1,
            events=all_events,
            program=program,
        )

    def _generate_bass_for_chord(
        self,
        root_midi: int,
        chord: Chord,
        scale: Scale,
        start_tick: int,
        duration_beats: float,
        intensity: float,
        tc: TickConverter,
        kick_beats: set[int],
        genre: Genre,
    ) -> list[NoteEvent]:
        """Generate bass notes over a chord span."""
        events: list[NoteEvent] = []
        base_vel = max(60, min(120, int(90 * intensity)))

        if intensity >= 0.7:
            # 8th note pattern
            step_beats = 0.5
        else:
            # Quarter note pattern
            step_beats = 1.0

        step_ticks = tc.beats_to_ticks(step_beats)
        dur_ticks = int(step_ticks * 0.9)  # slight gap between notes
        total_ticks = tc.beats_to_ticks(duration_beats)

        t = 0
        note_count = 0
        while t < total_ticks:
            tick = start_tick + t
            pitch = root_midi

            # Every other note at high intensity: add approach/passing tone
            if intensity >= 0.8 and note_count % 2 == 1 and note_count > 0:
                pitch = self._approach_note(root_midi, chord, scale)

            # Fifth on beat 3 for walking bass feel
            if note_count == 2 and duration_beats >= 3.0:
                pitch = root_midi + 7  # perfect 5th

            vel = base_vel
            # Accent notes that land on kick beats
            if kick_beats and tick in kick_beats:
                vel = min(127, vel + 10)

            events.append(NoteEvent(
                pitch=max(0, min(127, pitch)),
                velocity=max(1, min(127, vel)),
                start_tick=tick,
                duration_ticks=dur_ticks,
                channel=1,
            ))
            t += step_ticks
            note_count += 1

        return events

    def _approach_note(self, root_midi: int, chord: Chord, scale: Scale) -> int:
        """Generate an approach note - chromatic or scale-based."""
        # Try scale tone one step above root
        fifth = root_midi + 7
        if scale.contains(fifth):
            return fifth
        # Chromatic approach from below
        return root_midi - 1

    def _get_progression(
        self, context: SessionContext, section_name: str, genre: Genre, key: Any
    ) -> ChordProgression:
        """Get chord progression for a section."""
        # Check if context has a progression for this section
        if section_name in context.chord_progressions:
            return context.chord_progressions[section_name]

        # Generate a default progression based on genre
        from audio_engineer.core.music_theory import ProgressionFactory

        root = key.root.value
        if genre == Genre.BLUES:
            return ProgressionFactory.twelve_bar_blues(root)
        elif genre in (Genre.POP, Genre.FOLK, Genre.COUNTRY):
            return ProgressionFactory.pop_I_V_vi_IV(root)
        else:
            return ProgressionFactory.classic_rock_I_IV_V(root)

    def _extract_kick_beats(self, context: SessionContext, tc: TickConverter) -> set[int]:
        """Extract tick positions of kick drum from existing drum track."""
        kick_ticks: set[int] = set()
        from audio_engineer.core.constants import GM_DRUMS
        kick_pitch = GM_DRUMS["kick"]

        for track in context.existing_tracks.values():
            if track.instrument == Instrument.DRUMS:
                for event in track.events:
                    if event.pitch == kick_pitch:
                        kick_ticks.add(event.start_tick)
        return kick_ticks
