"""Brass agent — generates brass stabs, horn lines, and sax parts."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import ChordProgression
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext

_STAB_SECTIONS = {"chorus", "solo", "bridge"}


class BrassAgent(BaseMusician):
    """Generates brass/horn parts: stabs, pad lines, or sax solos."""

    def __init__(self, llm: Any = None, instrument: Instrument = Instrument.BRASS):
        channel = 6
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

                if sec_name.lower() in _STAB_SECTIONS or intensity >= 0.75:
                    events = self._stab(pitches, tick_start, dur, intensity, tc)
                else:
                    events = self._long_tone(pitches, tick_start, dur, intensity, tc)

                all_events.extend(events)
                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)
        program = self._select_program(genre, self.instrument)

        return MidiTrackData(
            name="Brass",
            instrument=self.instrument,
            channel=self.channel,
            events=all_events,
            program=program,
        )

    def _stab(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Short punchy chord stabs on beat 1 (and optionally beat 3)."""
        events: list[NoteEvent] = []
        vel = max(70, min(120, int(95 * intensity)))
        stab_dur = tc.ticks_per_beat // 2  # 8th note stab

        # Beat 1 stab
        for p in pitches:
            events.append(NoteEvent(
                pitch=p, velocity=vel, start_tick=start_tick,
                duration_ticks=stab_dur, channel=self.channel,
            ))
        # Beat 3 stab if duration long enough
        if duration_beats >= 3.0:
            tick3 = start_tick + tc.beats_to_ticks(2.0)
            for p in pitches:
                events.append(NoteEvent(
                    pitch=p, velocity=max(1, vel - 10), start_tick=tick3,
                    duration_ticks=stab_dur, channel=self.channel,
                ))
        # Fall-off note (one semitone below, very short, at end of phrase)
        if duration_beats >= 4.0 and pitches:
            falloff_tick = start_tick + tc.beats_to_ticks(duration_beats) - tc.ticks_per_beat // 4
            events.append(NoteEvent(
                pitch=max(0, pitches[-1] - 2), velocity=max(1, vel - 30),
                start_tick=falloff_tick, duration_ticks=tc.ticks_per_beat // 4,
                channel=self.channel,
            ))
        return events

    def _long_tone(
        self, pitches: list[int], start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Sustained long tone / pad."""
        vel = max(45, min(95, int(70 * intensity)))
        dur_ticks = tc.beats_to_ticks(duration_beats) - 20
        return [
            NoteEvent(
                pitch=p, velocity=vel, start_tick=start_tick,
                duration_ticks=max(1, dur_ticks), channel=self.channel,
            )
            for p in pitches[:2]  # brass: limit to 2 notes for realism
        ]

    def _select_program(self, genre: Genre, instrument: Instrument) -> int:
        if instrument == Instrument.TRUMPET:
            return GM_PROGRAMS["trumpet"]
        if instrument == Instrument.TROMBONE:
            return GM_PROGRAMS["trombone"]
        if instrument == Instrument.FRENCH_HORN:
            return GM_PROGRAMS["french_horn"]
        if instrument == Instrument.TUBA:
            return GM_PROGRAMS["tuba"]
        if instrument == Instrument.SAXOPHONE:
            if genre in (Genre.JAZZ, Genre.SWING, Genre.BEBOP, Genre.BLUES, Genre.COOL_JAZZ,
                         Genre.SMOOTH_JAZZ, Genre.FREE_JAZZ, Genre.FUSION, Genre.ACID_JAZZ):
                return GM_PROGRAMS["tenor_sax"]
            return GM_PROGRAMS["alto_sax"]
        if instrument == Instrument.WOODWINDS:
            return GM_PROGRAMS["oboe"]
        if instrument == Instrument.FLUTE:
            return GM_PROGRAMS["flute"]
        if instrument == Instrument.CLARINET:
            return GM_PROGRAMS["clarinet"]
        if instrument == Instrument.OBOE:
            return GM_PROGRAMS["oboe"]
        if instrument == Instrument.HARMONICA:
            return GM_PROGRAMS["harmonica"]
        if instrument == Instrument.BAGPIPE:
            return GM_PROGRAMS["bagpipe"]
        if genre in (Genre.FUNK, Genre.SOUL, Genre.RNB, Genre.GOSPEL, Genre.MOTOWN,
                     Genre.AFROBEAT, Genre.SALSA, Genre.SKA):
            return GM_PROGRAMS["brass_section"]
        if genre in (Genre.JAZZ, Genre.SWING, Genre.BEBOP, Genre.COOL_JAZZ,
                     Genre.SMOOTH_JAZZ, Genre.FUSION):
            return GM_PROGRAMS["tenor_sax"]
        return GM_PROGRAMS["brass_section"]

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
        if genre in (Genre.FUNK, Genre.RNB):
            return ProgressionFactory.funk_I7_IV7(root)
        return ProgressionFactory.pop_I_V_vi_IV(root)
