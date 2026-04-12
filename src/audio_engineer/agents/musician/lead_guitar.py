"""Lead Guitar agent — generates pentatonic licks and melodic runs."""
from __future__ import annotations

from typing import Any

from audio_engineer.core.models import (
    Instrument, Genre, MidiTrackData, NoteEvent,
)
from audio_engineer.core.music_theory import Scale, ChordProgression
from audio_engineer.core.constants import GM_PROGRAMS
from audio_engineer.core.midi_engine import TickConverter

from audio_engineer.agents.base import BaseMusician, SessionContext

# Sections that call for a lead guitar solo / fill
_SOLO_SECTIONS = {"solo", "bridge", "chorus"}


class LeadGuitarAgent(BaseMusician):
    """Generates lead guitar parts: pentatonic licks, scale runs, and fills."""

    def __init__(self, llm: Any = None):
        super().__init__(instrument=Instrument.LEAD_GUITAR, channel=4, llm=llm)

    def generate_part(self, context: SessionContext) -> MidiTrackData:
        genre = context.config.genre
        tc = TickConverter(time_sig=context.config.time_signature)
        key = context.config.key
        scale_name = self._pick_scale(genre, key.mode.value)
        scale = Scale(key.root.value, scale_name)

        sections = self._get_section_bars(context)
        all_events: list[NoteEvent] = []

        for sec_name, start_bar, num_bars, intensity in sections:
            progression = self._get_progression(context, sec_name, genre, key)
            chords = progression.chords
            total_section_beats = num_bars * tc.beats_per_bar

            beat_cursor = 0.0
            chord_idx = 0
            while beat_cursor < total_section_beats:
                _chord, chord_dur = chords[chord_idx % len(chords)]
                remaining = total_section_beats - beat_cursor
                dur = min(chord_dur, remaining)
                tick_start = tc.beats_to_ticks(beat_cursor) + start_bar * tc.ticks_per_bar

                if sec_name.lower() in _SOLO_SECTIONS or intensity >= 0.8:
                    events = self._lick(scale, tick_start, dur, intensity, tc)
                elif intensity >= 0.5:
                    events = self._fill(scale, tick_start, dur, intensity, tc)
                else:
                    events = []  # lay out during quiet sections

                all_events.extend(events)
                beat_cursor += dur
                chord_idx += 1

        all_events.sort(key=lambda e: e.start_tick)
        program = self._select_program(genre)

        return MidiTrackData(
            name="Lead Guitar",
            instrument=Instrument.LEAD_GUITAR,
            channel=self.channel,
            events=all_events,
            program=program,
        )

    def _lick(
        self, scale: Scale, start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Generate a pentatonic lick using ascending/descending scale degrees."""
        events: list[NoteEvent] = []
        vel = max(70, min(115, int(90 * intensity)))
        step_beats = 0.25  # 16th notes
        step_ticks = tc.beats_to_ticks(step_beats)
        note_dur = int(step_ticks * 0.9)
        total_ticks = tc.beats_to_ticks(duration_beats)

        scale_notes = scale.notes_in_octave(4) + scale.notes_in_octave(5)
        # Ascending then descending snake pattern
        pattern = scale_notes + list(reversed(scale_notes[:-1]))

        t = 0
        idx = 0
        while t < total_ticks:
            pitch = pattern[idx % len(pattern)]
            # Accent first note of each beat
            v = min(127, vel + 10) if (t % tc.ticks_per_beat == 0) else vel
            events.append(NoteEvent(
                pitch=pitch, velocity=v,
                start_tick=start_tick + t, duration_ticks=note_dur,
                channel=self.channel,
            ))
            t += step_ticks
            idx += 1
        return events

    def _fill(
        self, scale: Scale, start_tick: int, duration_beats: float,
        intensity: float, tc: TickConverter,
    ) -> list[NoteEvent]:
        """Short 2-beat fill: 3 notes leading to the next chord root."""
        events: list[NoteEvent] = []
        vel = max(60, min(100, int(80 * intensity)))
        step_ticks = tc.beats_to_ticks(0.5)
        note_dur = int(step_ticks * 0.85)
        scale_notes = scale.notes_in_octave(4)

        for i, pitch in enumerate(scale_notes[:4]):
            events.append(NoteEvent(
                pitch=pitch, velocity=vel - i * 5,
                start_tick=start_tick + i * step_ticks,
                duration_ticks=note_dur,
                channel=self.channel,
            ))
        return events

    def _pick_scale(self, genre: Genre, base_mode: str) -> str:
        """Choose appropriate scale for the genre."""
        if genre in (Genre.BLUES, Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.PUNK):
            return "pentatonic_minor"
        if genre == Genre.METAL:
            return "minor"
        if genre in (Genre.JAZZ, Genre.BEBOP, Genre.SWING):
            return "bebop_dominant"
        if genre in (Genre.COUNTRY, Genre.FOLK):
            return "pentatonic_major"
        if genre == Genre.FUNK:
            return "pentatonic_minor"
        # Fall back to the session key mode if available
        return base_mode if base_mode in ("major", "minor", "pentatonic_minor", "pentatonic_major") else "pentatonic_minor"

    def _select_program(self, genre: Genre) -> int:
        if genre in (Genre.CLASSIC_ROCK, Genre.HARD_ROCK, Genre.PUNK):
            return GM_PROGRAMS["electric_guitar_overdriven"]
        if genre == Genre.METAL:
            return GM_PROGRAMS["electric_guitar_distortion"]
        if genre == Genre.BLUES:
            return GM_PROGRAMS["electric_guitar_clean"]
        if genre in (Genre.COUNTRY, Genre.FOLK):
            return GM_PROGRAMS["steel_guitar"]
        return GM_PROGRAMS["electric_guitar_clean"]

    def _get_progression(
        self, context: SessionContext, section_name: str, genre: Genre, key: Any
    ) -> ChordProgression:
        if section_name in context.chord_progressions:
            return context.chord_progressions[section_name]
        from audio_engineer.core.music_theory import ProgressionFactory
        root = key.root.value
        if genre == Genre.BLUES:
            return ProgressionFactory.twelve_bar_blues(root)
        if genre in (Genre.JAZZ, Genre.SWING, Genre.BEBOP):
            return ProgressionFactory.jazz_ii_V_I(root)
        return ProgressionFactory.classic_rock_I_IV_V(root)
