"""Keyboardist agent - generates keyboard/piano/organ comping."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import (
    ChordProgression, Chord,
)
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext


class KeyboardistAgent(BaseMusician):
    """Generates keyboard comping - pads for low intensity, rhythmic for high."""

    def __init__(self, llm: Any = None, instrument: Instrument = Instrument.KEYS):
        super().__init__(instrument=instrument, channel=3, llm=llm)

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

                tick_start = tc.beats_to_ticks(beat_cursor) + start_bar * tc.ticks_per_bar

                if intensity < 0.5:
                    events = self._sustained_pad(chord, tick_start, dur, intensity, tc)
                else:
                    events = self._rhythmic_comp(chord, tick_start, dur, intensity, tc)

                all_events.extend(events)
                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)

        program = self._select_program(genre)

        return MidiTrackData(
            name=self.instrument.value.capitalize(),
            instrument=self.instrument,
            channel=self.channel,
            events=all_events,
            program=program,
        )

    def _sustained_pad(
        self, chord: Chord, start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Whole-note sustained pad voicing."""
        pitches = chord.midi_notes(octave=4)
        vel = max(40, min(90, int(70 * intensity)))
        dur_ticks = tc.beats_to_ticks(duration_beats) - 10  # slight gap
        return [
            NoteEvent(
                pitch=p, velocity=vel, start_tick=start_tick,
                duration_ticks=max(1, dur_ticks), channel=3,
            )
            for p in pitches
        ]

    def _rhythmic_comp(
        self, chord: Chord, start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Rhythmic chord comping - quarter or 8th note hits."""
        events: list[NoteEvent] = []
        pitches = chord.midi_notes(octave=4)
        base_vel = max(55, min(100, int(80 * intensity)))

        step = 0.5 if intensity >= 0.8 else 1.0
        step_ticks = tc.beats_to_ticks(step)
        note_dur = int(step_ticks * 0.7)
        total_ticks = tc.beats_to_ticks(duration_beats)

        t = 0
        hit = 0
        while t < total_ticks:
            tick = start_tick + t
            vel = base_vel
            # Syncopation: skip some hits for a comping feel
            if hit % 4 == 2 and intensity < 0.9:
                t += step_ticks
                hit += 1
                continue

            for p in pitches:
                events.append(NoteEvent(
                    pitch=p, velocity=max(1, min(127, vel)),
                    start_tick=tick, duration_ticks=note_dur, channel=3,
                ))
            t += step_ticks
            hit += 1

        return events

    def _select_program(self, genre: Genre) -> int:
        if self.instrument == Instrument.ORGAN:
            return GM_PROGRAMS.get("drawbar_organ", GM_PROGRAMS["rock_organ"])
        if self.instrument in (Instrument.VIBRAPHONE,):
            return GM_PROGRAMS.get("vibraphone", GM_PROGRAMS["acoustic_grand_piano"])
        if self.instrument in (Instrument.MARIMBA,):
            return GM_PROGRAMS.get("marimba", GM_PROGRAMS["acoustic_grand_piano"])
        if genre in (Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.BLUES):
            return GM_PROGRAMS["rock_organ"]
        return GM_PROGRAMS["acoustic_grand_piano"]

    def _get_progression(
        self, context: SessionContext, section_name: str, genre: Genre, key: Any
    ) -> ChordProgression:
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
