"""Guitarist agent - generates rhythm guitar parts."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import (
    ChordProgression, Chord, note_name_to_midi,
)
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext


# Genres that prefer power chords
_POWER_CHORD_GENRES = {Genre.CLASSIC_ROCK, Genre.PUNK, Genre.HARD_ROCK}
# Sections with palm mute feel
_PALM_MUTE_SECTIONS = {"verse", "intro", "breakdown"}


class GuitaristAgent(BaseMusician):
    """Generates rhythm guitar parts with genre-appropriate voicings."""

    def __init__(self, llm: Any = None):
        super().__init__(instrument=Instrument.ELECTRIC_GUITAR, channel=2, llm=llm)

    def generate_part(self, context: SessionContext) -> MidiTrackData:
        genre = context.config.genre
        tc = TickConverter(time_sig=context.config.time_signature)
        key = context.config.key

        sections = self._get_section_bars(context)
        all_events: list[NoteEvent] = []

        for sec_name, start_bar, num_bars, intensity in sections:
            progression = self._get_progression(context, sec_name, genre, key)
            chords = progression.chords
            total_section_beats = num_bars * tc.beats_per_bar

            beat_cursor = 0.0
            chord_idx = 0
            while beat_cursor < total_section_beats:
                chord, chord_dur = chords[chord_idx % len(chords)]
                remaining = total_section_beats - beat_cursor
                dur = min(chord_dur, remaining)

                events = self._strum_chord(
                    chord=chord,
                    genre=genre,
                    section_name=sec_name,
                    start_tick=tc.beats_to_ticks(beat_cursor) + start_bar * tc.ticks_per_bar,
                    duration_beats=dur,
                    intensity=intensity,
                    tc=tc,
                )
                all_events.extend(events)

                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)

        # Select program based on genre/intensity
        program = self._select_program(genre, sections)

        return MidiTrackData(
            name="Guitar",
            instrument=Instrument.ELECTRIC_GUITAR,
            channel=2,
            events=all_events,
            program=program,
        )

    def _strum_chord(
        self,
        chord: Chord,
        genre: Genre,
        section_name: str,
        start_tick: int,
        duration_beats: float,
        intensity: float,
        tc: TickConverter,
    ) -> list[NoteEvent]:
        """Generate strummed chord events over a duration."""
        events: list[NoteEvent] = []
        use_power = genre in _POWER_CHORD_GENRES
        is_palm_mute = section_name.lower() in _PALM_MUTE_SECTIONS and intensity < 0.7

        # Build voicing
        if use_power:
            # Power chord: root + 5th, in guitar range (octave 3-4)
            root = note_name_to_midi(chord.root, 3)
            pitches = [root, root + 7]
            # Double an octave up for fullness
            if intensity >= 0.7:
                pitches.append(root + 12)
        else:
            # Full chord voicing in octave 3
            pitches = chord.midi_notes(octave=3)

        # Determine strum rhythm
        if intensity >= 0.7:
            # 8th note strums
            step_beats = 0.5
        else:
            # Quarter note strums
            step_beats = 1.0

        step_ticks = tc.beats_to_ticks(step_beats)
        total_ticks = tc.beats_to_ticks(duration_beats)

        # Velocity
        base_vel = max(50, min(115, int(85 * intensity)))
        if is_palm_mute:
            base_vel = max(40, base_vel - 25)

        # Duration of each strum (sustain)
        if is_palm_mute:
            note_dur = int(step_ticks * 0.4)  # short, muted
        else:
            note_dur = int(step_ticks * 0.85)  # sustained

        t = 0
        strum_count = 0
        while t < total_ticks:
            tick = start_tick + t
            vel = base_vel

            # Accent on downbeats (1 and 3)
            beat_in_bar = (t / tc.beats_to_ticks(1.0)) % tc.beats_per_bar
            if beat_in_bar < 0.1 or abs(beat_in_bar - 2.0) < 0.1:
                vel = min(127, vel + 10)

            # Slight velocity variation for upstrokes
            if strum_count % 2 == 1:
                vel = max(1, vel - 5)

            # Strum spread: slight delay between notes (5-15 ticks)
            for i, pitch in enumerate(pitches):
                strum_offset = i * 5  # subtle strum spread
                events.append(NoteEvent(
                    pitch=pitch,
                    velocity=max(1, min(127, vel)),
                    start_tick=tick + strum_offset,
                    duration_ticks=note_dur,
                    channel=2,
                ))

            t += step_ticks
            strum_count += 1

        return events

    def _select_program(self, genre: Genre, sections: list) -> int:
        """Choose guitar program based on genre."""
        if genre in (Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.PUNK):
            return GM_PROGRAMS["electric_guitar_overdriven"]
        elif genre == Genre.BLUES:
            return GM_PROGRAMS["electric_guitar_clean"]
        elif genre in (Genre.FOLK, Genre.COUNTRY):
            return GM_PROGRAMS.get("steel_guitar", GM_PROGRAMS["electric_guitar_clean"])
        else:
            return GM_PROGRAMS["electric_guitar_clean"]

    def _get_progression(
        self, context: SessionContext, section_name: str, genre: Genre, key: Any
    ) -> ChordProgression:
        """Get chord progression for a section."""
        if section_name in context.chord_progressions:
            return context.chord_progressions[section_name]

        from audio_engineer.core.music_theory import ProgressionFactory
        root = key.root.value
        if genre == Genre.BLUES:
            return ProgressionFactory.twelve_bar_blues(root)
        elif genre in (Genre.POP, Genre.FOLK, Genre.COUNTRY):
            return ProgressionFactory.pop_I_V_vi_IV(root)
        else:
            return ProgressionFactory.classic_rock_I_IV_V(root)
