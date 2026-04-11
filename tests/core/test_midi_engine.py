"""Tests for the MIDI engine."""

import tempfile
from pathlib import Path

import pytest

from audio_engineer.core.midi_engine import MidiTrackBuilder, TickConverter
from audio_engineer.core.models import NoteEvent, MidiTrackData, Instrument, TimeSignature
from audio_engineer.core.constants import TICKS_PER_BEAT


class TestTickConverter:
    def test_bars_to_ticks(self, tick_converter):
        assert tick_converter.bars_to_ticks(1) == TICKS_PER_BEAT * 4
        assert tick_converter.bars_to_ticks(2) == TICKS_PER_BEAT * 8

    def test_beats_to_ticks(self, tick_converter):
        assert tick_converter.beats_to_ticks(1.0) == TICKS_PER_BEAT
        assert tick_converter.beats_to_ticks(0.5) == TICKS_PER_BEAT // 2

    def test_beat_position(self, tick_converter):
        # Bar 0, beat 1 = tick 0
        assert tick_converter.beat_position(0, 1.0) == 0
        # Bar 0, beat 2 = tick 480
        assert tick_converter.beat_position(0, 2.0) == TICKS_PER_BEAT
        # Bar 1, beat 1
        assert tick_converter.beat_position(1, 1.0) == TICKS_PER_BEAT * 4

    def test_ticks_to_bars_beats(self, tick_converter):
        bars, beats = tick_converter.ticks_to_bars_beats(0)
        assert bars == 0
        assert beats == pytest.approx(1.0)

        bars, beats = tick_converter.ticks_to_bars_beats(TICKS_PER_BEAT * 4)
        assert bars == 1
        assert beats == pytest.approx(1.0)

    def test_custom_time_signature(self):
        tc = TickConverter(time_sig=TimeSignature(numerator=3, denominator=4))
        assert tc.beats_per_bar == 3
        assert tc.ticks_per_bar == TICKS_PER_BEAT * 3


class TestMidiTrackBuilder:
    def test_build_empty_track(self):
        builder = MidiTrackBuilder(name="Test", channel=1, program=33, instrument=Instrument.BASS)
        track = builder.build()
        assert track.name == "Test"
        assert track.instrument == Instrument.BASS
        assert track.channel == 1
        assert track.program == 33
        assert len(track.events) == 0

    def test_add_note(self):
        builder = MidiTrackBuilder(instrument=Instrument.BASS)
        builder.add_note(pitch=60, velocity=100, start_tick=0, duration_ticks=480)
        track = builder.build()
        assert len(track.events) == 1
        assert track.events[0].pitch == 60

    def test_add_chord(self):
        builder = MidiTrackBuilder(instrument=Instrument.KEYS)
        builder.add_chord([60, 64, 67], velocity=90, start_tick=0, duration_ticks=960)
        track = builder.build()
        assert len(track.events) == 3

    def test_fluent_api(self):
        track = (
            MidiTrackBuilder(name="Lead", instrument=Instrument.ELECTRIC_GUITAR)
            .set_tempo(140)
            .add_note(64, 100, 0, 480)
            .add_note(67, 100, 480, 480)
            .build()
        )
        assert track.name == "Lead"
        assert len(track.events) == 2

    def test_events_sorted(self):
        builder = MidiTrackBuilder(instrument=Instrument.BASS)
        builder.add_note(67, 100, 960, 480)
        builder.add_note(60, 100, 0, 480)
        builder.add_note(64, 100, 480, 480)
        track = builder.build()
        ticks = [e.start_tick for e in track.events]
        assert ticks == sorted(ticks)


class TestMidiEngine:
    def test_create_builder(self, midi_engine):
        builder = midi_engine.create_builder("Bass", channel=1, program=33, instrument=Instrument.BASS)
        assert isinstance(builder, MidiTrackBuilder)

    def test_track_to_mido(self, midi_engine, sample_track):
        mido_track = midi_engine.track_to_mido(sample_track, tempo=120)
        assert mido_track.name == "Test Track"
        # Should have: set_tempo, program_change, note_on, note_off
        msg_types = [msg.type for msg in mido_track if not msg.is_meta]
        assert "program_change" in msg_types
        assert "note_on" in msg_types
        assert "note_off" in msg_types

    def test_merge_tracks(self, midi_engine, sample_track):
        mid = midi_engine.merge_tracks([sample_track], tempo=120)
        assert mid.type == 1
        assert len(mid.tracks) == 1
        assert mid.ticks_per_beat == TICKS_PER_BEAT

    def test_merge_multiple_tracks(self, midi_engine):
        track1 = MidiTrackData(
            name="Bass", instrument=Instrument.BASS, channel=1, program=33,
            events=[NoteEvent(pitch=36, velocity=100, start_tick=0, duration_ticks=480)],
        )
        track2 = MidiTrackData(
            name="Drums", instrument=Instrument.DRUMS, channel=9, program=0,
            events=[NoteEvent(pitch=36, velocity=100, start_tick=0, duration_ticks=120, channel=9)],
        )
        mid = midi_engine.merge_tracks([track1, track2], tempo=120)
        assert len(mid.tracks) == 2

    def test_export_midi(self, midi_engine, sample_track):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.mid"
            mid = midi_engine.merge_tracks([sample_track], tempo=120)
            result = midi_engine.export_midi(mid, path)
            assert result.exists()
            assert result.suffix == ".mid"

    def test_export_track(self, midi_engine, sample_track):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "track.mid"
            result = midi_engine.export_track(sample_track, path, tempo=120)
            assert result.exists()

    def test_export_creates_dirs(self, midi_engine, sample_track):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "test.mid"
            mid = midi_engine.merge_tracks([sample_track], tempo=120)
            result = midi_engine.export_midi(mid, path)
            assert result.exists()

    def test_quantize(self, midi_engine):
        track = MidiTrackData(
            name="Test", instrument=Instrument.BASS, channel=0,
            events=[
                NoteEvent(pitch=60, velocity=100, start_tick=5, duration_ticks=480),
                NoteEvent(pitch=62, velocity=100, start_tick=483, duration_ticks=480),
            ],
        )
        quantized = midi_engine.quantize(track, resolution_ticks=TICKS_PER_BEAT)
        assert quantized.events[0].start_tick == 0
        assert quantized.events[1].start_tick == TICKS_PER_BEAT

    def test_quantize_16th(self, midi_engine):
        sixteenth = TICKS_PER_BEAT // 4  # 120
        track = MidiTrackData(
            name="Test", instrument=Instrument.BASS, channel=0,
            events=[
                NoteEvent(pitch=60, velocity=100, start_tick=115, duration_ticks=100),
            ],
        )
        quantized = midi_engine.quantize(track, resolution_ticks=sixteenth)
        assert quantized.events[0].start_tick == sixteenth  # 120

    def test_humanize(self, midi_engine):
        track = MidiTrackData(
            name="Test", instrument=Instrument.BASS, channel=0,
            events=[
                NoteEvent(pitch=60, velocity=100, start_tick=480, duration_ticks=480),
                NoteEvent(pitch=62, velocity=100, start_tick=960, duration_ticks=480),
            ],
        )
        humanized = midi_engine.humanize(track, timing_ticks=5, velocity_range=4)
        # Events should still exist with same count
        assert len(humanized.events) == 2
        # Velocities and timings may differ slightly
        # Just check they're within valid range
        for event in humanized.events:
            assert 0 <= event.start_tick
            assert 1 <= event.velocity <= 127

    def test_humanize_preserves_order(self, midi_engine):
        events = [
            NoteEvent(pitch=60, velocity=100, start_tick=i * 480, duration_ticks=480)
            for i in range(10)
        ]
        track = MidiTrackData(
            name="Test", instrument=Instrument.BASS, channel=0, events=events,
        )
        humanized = midi_engine.humanize(track, timing_ticks=2, velocity_range=2)
        ticks = [e.start_tick for e in humanized.events]
        assert ticks == sorted(ticks)
