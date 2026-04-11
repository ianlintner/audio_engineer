"""Synth agent — generates synthesizer pads, leads, and arpeggio lines."""
from __future__ import annotations

import random
from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import ChordProgression
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext


class SynthAgent(BaseMusician):
    """Generates synth pads, leads, and arpeggio patterns."""

    def __init__(self, llm: Any = None, instrument: Instrument = Instrument.PAD):
        channel = 7
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
                pitches = chord.midi_notes(octave=4)

                if self.instrument == Instrument.SYNTHESIZER and intensity >= 0.6:
                    events = self._arpeggio(pitches, tick_start, dur, intensity, tc)
                else:
                    events = self._sustained_pad(pitches, tick_start, dur, intensity, tc)

                all_events.extend(events)
                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)
        program = self._select_program(genre, self.instrument)

        return MidiTrackData(
            name="Synth",
            instrument=self.instrument,
            channel=self.channel,
            events=all_events,
            program=program,
        )

    def _sustained_pad(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Long, slowly-evolving sustained pad chord."""
        base_vel = max(35, min(85, int(60 * intensity)))
        dur_ticks = tc.beats_to_ticks(duration_beats) - 10
        events: list[NoteEvent] = []
        for i, p in enumerate(pitches):
            # Slightly stagger attack for natural pad swell
            delay = i * (tc.ticks_per_beat // 16)
            events.append(NoteEvent(
                pitch=p,
                velocity=max(1, base_vel - i * 4),
                start_tick=start_tick + delay,
                duration_ticks=max(1, dur_ticks - delay),
                channel=self.channel,
            ))
        return events

    def _arpeggio(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
        direction: str = "up",
    ) -> list[NoteEvent]:
        """Arpeggio pattern cycling through chord tones."""
        events: list[NoteEvent] = []
        vel = max(55, min(100, int(80 * intensity)))
        step_beats = 0.25  # 16th notes
        step_ticks = tc.beats_to_ticks(step_beats)
        note_dur = int(step_ticks * 0.8)
        total_ticks = tc.beats_to_ticks(duration_beats)

        # Build arpeggio pitch list (up, down, or random)
        extended = pitches + [p + 12 for p in pitches]  # two-octave run
        if direction == "down":
            extended = list(reversed(extended))
        elif direction == "random":
            extended = list(pitches)
            random.shuffle(extended)

        t = 0
        idx = 0
        while t < total_ticks:
            p = extended[idx % len(extended)]
            events.append(NoteEvent(
                pitch=max(0, min(127, p)),
                velocity=vel,
                start_tick=start_tick + t,
                duration_ticks=note_dur,
                channel=self.channel,
            ))
            t += step_ticks
            idx += 1
        return events

    def _select_program(self, genre: Genre, instrument: Instrument) -> int:
        if instrument == Instrument.SYNTHESIZER:
            if genre in (Genre.ELECTRONIC, Genre.HOUSE):
                return GM_PROGRAMS["lead_sawtooth"]
            if genre == Genre.AMBIENT:
                return GM_PROGRAMS["pad_new_age"]
            return GM_PROGRAMS["lead_square"]
        # PAD
        if genre == Genre.AMBIENT:
            return GM_PROGRAMS["pad_halo"]
        if genre in (Genre.ELECTRONIC, Genre.HOUSE):
            return GM_PROGRAMS["pad_polysynth"]
        if genre in (Genre.JAZZ, Genre.SOUL, Genre.RNB):
            return GM_PROGRAMS["pad_warm"]
        return GM_PROGRAMS["pad_new_age"]

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
        if genre in (Genre.ELECTRONIC, Genre.HOUSE, Genre.AMBIENT):
            return ProgressionFactory.modal_dorian(root)
        return ProgressionFactory.pop_I_V_vi_IV(root)
