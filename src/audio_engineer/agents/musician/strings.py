"""Strings agent — generates string ensemble / violin parts."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import ChordProgression
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext


class StringsAgent(BaseMusician):
    """Generates string parts: legato pads, pizzicato, or tremolo lines."""

    def __init__(self, llm: Any = None, instrument: Instrument = Instrument.STRINGS):
        channel = 5
        super().__init__(instrument=instrument, channel=channel, llm=llm)

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

                if intensity < 0.4:
                    events = self._pizzicato(chord.midi_notes(octave=4), tick_start, dur, intensity, tc)
                elif intensity >= 0.85:
                    events = self._tremolo(chord.midi_notes(octave=4), tick_start, dur, intensity, tc)
                else:
                    events = self._legato_pad(chord.midi_notes(octave=4), tick_start, dur, intensity, tc)

                all_events.extend(events)
                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)
        program = self._select_program(genre, self.instrument)

        return MidiTrackData(
            name="Strings",
            instrument=self.instrument,
            channel=self.channel,
            events=all_events,
            program=program,
        )

    def _legato_pad(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Sustained legato chord — whole duration, slight gap at end."""
        vel = max(45, min(95, int(72 * intensity)))
        dur_ticks = tc.beats_to_ticks(duration_beats) - 20
        return [
            NoteEvent(
                pitch=p, velocity=vel, start_tick=start_tick,
                duration_ticks=max(1, dur_ticks), channel=self.channel,
            )
            for p in pitches
        ]

    def _pizzicato(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Short pizzicato plucks on each beat."""
        events: list[NoteEvent] = []
        vel = max(40, min(85, int(65 * intensity)))
        note_dur = tc.ticks_per_beat // 4  # 16th note
        step_ticks = tc.ticks_per_beat
        total_ticks = tc.beats_to_ticks(duration_beats)
        t = 0
        while t < total_ticks:
            for p in pitches:
                events.append(NoteEvent(
                    pitch=p, velocity=vel, start_tick=start_tick + t,
                    duration_ticks=note_dur, channel=self.channel,
                ))
            t += step_ticks
        return events

    def _tremolo(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Rapid repeated 32nd notes for tremolo effect."""
        events: list[NoteEvent] = []
        vel = max(60, min(110, int(85 * intensity)))
        step_ticks = tc.ticks_per_beat // 8  # 32nd note
        note_dur = step_ticks - 5
        total_ticks = tc.beats_to_ticks(duration_beats)
        t = 0
        while t < total_ticks:
            for p in pitches:
                events.append(NoteEvent(
                    pitch=p, velocity=vel, start_tick=start_tick + t,
                    duration_ticks=max(1, note_dur), channel=self.channel,
                ))
            t += step_ticks
        return events

    def _select_program(self, genre: Genre, instrument: Instrument) -> int:
        if instrument == Instrument.VIOLIN:
            return GM_PROGRAMS["violin"]
        if genre in (Genre.ELECTRONIC, Genre.AMBIENT):
            return GM_PROGRAMS["synth_strings_1"]
        return GM_PROGRAMS["string_ensemble_1"]

    def _get_progression(
        self, context: SessionContext, section_name: str, genre: Genre, key: Any
    ) -> ChordProgression:
        if section_name in context.chord_progressions:
            return context.chord_progressions[section_name]
        from audio_engineer.core.music_theory import ProgressionFactory
        root = key.root.value
        if genre in (Genre.JAZZ, Genre.SWING, Genre.BEBOP):
            return ProgressionFactory.jazz_ii_V_I(root)
        if genre == Genre.BLUES:
            return ProgressionFactory.twelve_bar_blues(root)
        return ProgressionFactory.pop_I_V_vi_IV(root)
