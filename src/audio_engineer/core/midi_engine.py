"""MIDI Engine - Core MIDI file construction and manipulation."""

from __future__ import annotations

import mido
from pathlib import Path
from typing import Self

from .models import NoteEvent, MidiTrackData, TimeSignature, Instrument
from .constants import TICKS_PER_BEAT
from .rhythm import humanize_timing, humanize_velocity


class TickConverter:
    """Convert between ticks, beats, and bars."""

    def __init__(self, ticks_per_beat: int = TICKS_PER_BEAT, time_sig: TimeSignature | None = None):
        self.ticks_per_beat = ticks_per_beat
        ts = time_sig or TimeSignature()
        self.beats_per_bar = ts.numerator
        self.ticks_per_bar = ticks_per_beat * self.beats_per_bar

    def bars_to_ticks(self, bars: int) -> int:
        return bars * self.ticks_per_bar

    def beats_to_ticks(self, beats: float) -> int:
        return int(beats * self.ticks_per_beat)

    def beat_position(self, bar: int, beat: float) -> int:
        """Get absolute tick for bar (0-indexed) and beat (1-indexed)."""
        return self.bars_to_ticks(bar) + self.beats_to_ticks(beat - 1.0)

    def ticks_to_bars_beats(self, ticks: int) -> tuple[int, float]:
        bars = ticks // self.ticks_per_bar
        remaining = ticks % self.ticks_per_bar
        beats = remaining / self.ticks_per_beat + 1.0
        return bars, beats


class MidiTrackBuilder:
    """Fluent builder for constructing MIDI tracks."""

    def __init__(
        self,
        name: str = "Track",
        channel: int = 0,
        program: int = 0,
        instrument: Instrument = Instrument.DRUMS,
    ):
        self._name = name
        self._channel = channel
        self._program = program
        self._instrument = instrument
        self._events: list[NoteEvent] = []
        self._tempo: int = 120
        self._time_sig = TimeSignature()
        self._cc_events: list[tuple[int, int, int]] = []  # (controller, value, tick)

    def set_tempo(self, bpm: int) -> Self:
        self._tempo = bpm
        return self

    def set_time_signature(self, numerator: int, denominator: int) -> Self:
        self._time_sig = TimeSignature(numerator=numerator, denominator=denominator)
        return self

    def add_note(self, pitch: int, velocity: int, start_tick: int, duration_ticks: int) -> Self:
        self._events.append(NoteEvent(
            pitch=pitch, velocity=velocity,
            start_tick=start_tick, duration_ticks=duration_ticks,
            channel=self._channel,
        ))
        return self

    def add_chord(self, pitches: list[int], velocity: int, start_tick: int, duration_ticks: int) -> Self:
        for p in pitches:
            self.add_note(p, velocity, start_tick, duration_ticks)
        return self

    def add_cc(self, controller: int, value: int, tick: int) -> Self:
        self._cc_events.append((controller, value, tick))
        return self

    def build(self) -> MidiTrackData:
        return MidiTrackData(
            name=self._name,
            instrument=self._instrument,
            channel=self._channel,
            events=sorted(self._events, key=lambda e: e.start_tick),
            program=self._program,
        )


class MidiEngine:
    """Central MIDI file construction and manipulation engine."""

    def __init__(self, ticks_per_beat: int = TICKS_PER_BEAT):
        self.ticks_per_beat = ticks_per_beat
        self.tick_converter = TickConverter(ticks_per_beat)

    def create_builder(
        self,
        name: str,
        channel: int = 0,
        program: int = 0,
        instrument: Instrument = Instrument.DRUMS,
    ) -> MidiTrackBuilder:
        return MidiTrackBuilder(name=name, channel=channel, program=program, instrument=instrument)

    def track_to_mido(self, track_data: MidiTrackData, tempo: int = 120) -> mido.MidiTrack:
        """Convert MidiTrackData to a mido MidiTrack."""
        track = mido.MidiTrack()
        track.name = track_data.name

        # Set tempo on first track
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo), time=0))

        # Program change
        track.append(mido.Message(
            "program_change", program=track_data.program,
            channel=track_data.channel, time=0,
        ))

        # Convert note events to MIDI messages (note_on / note_off pairs)
        messages: list[tuple[str, int, int, int, int]] = []
        for event in track_data.events:
            messages.append(("note_on", event.start_tick, event.pitch, event.velocity, event.channel))
            messages.append(("note_off", event.start_tick + event.duration_ticks, event.pitch, 0, event.channel))

        # Sort by absolute time, note_off before note_on at same tick
        messages.sort(key=lambda m: (m[1], 0 if m[0] == "note_off" else 1))

        # Convert to delta times
        current_tick = 0
        for msg_type, abs_tick, pitch, velocity, channel in messages:
            delta = abs_tick - current_tick
            if msg_type == "note_on":
                track.append(mido.Message(
                    "note_on", note=pitch, velocity=velocity,
                    channel=channel, time=delta,
                ))
            else:
                track.append(mido.Message(
                    "note_off", note=pitch, velocity=velocity,
                    channel=channel, time=delta,
                ))
            current_tick = abs_tick

        return track

    def merge_tracks(self, tracks: list[MidiTrackData], tempo: int = 120) -> mido.MidiFile:
        """Merge multiple tracks into a single MIDI file (Type 1)."""
        mid = mido.MidiFile(ticks_per_beat=self.ticks_per_beat, type=1)
        for track_data in tracks:
            mid.tracks.append(self.track_to_mido(track_data, tempo))
        return mid

    def humanize(self, track: MidiTrackData, timing_ticks: int = 10, velocity_range: int = 8) -> MidiTrackData:
        """Add human-like imprecision."""
        new_events = []
        for event in track.events:
            new_tick = max(0, humanize_timing(event.start_tick, timing_ticks))
            new_vel = humanize_velocity(event.velocity, velocity_range)
            new_events.append(event.model_copy(update={
                "start_tick": new_tick,
                "velocity": new_vel,
            }))
        return track.model_copy(update={"events": sorted(new_events, key=lambda e: e.start_tick)})

    def quantize(self, track: MidiTrackData, resolution_ticks: int | None = None) -> MidiTrackData:
        """Snap notes to nearest grid position."""
        res = resolution_ticks or (self.ticks_per_beat // 4)  # 16th note default
        new_events = []
        for event in track.events:
            quantized_start = round(event.start_tick / res) * res
            new_events.append(event.model_copy(update={"start_tick": quantized_start}))
        return track.model_copy(update={"events": sorted(new_events, key=lambda e: e.start_tick)})

    def export_midi(self, midi_file: mido.MidiFile, path: Path) -> Path:
        """Export mido.MidiFile to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        midi_file.save(str(path))
        return path

    def export_track(self, track: MidiTrackData, path: Path, tempo: int = 120) -> Path:
        """Export a single track as a MIDI file."""
        mid = self.merge_tracks([track], tempo)
        return self.export_midi(mid, path)
