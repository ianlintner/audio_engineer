"""Tests for MixerAgent."""

import pytest
from audio_engineer.core.models import (
    SessionConfig, Genre, Instrument, MidiTrackData,
    NoteEvent, MixConfig, SectionDef,
)
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.engineer.mixer import MixerAgent


@pytest.fixture
def mixer():
    return MixerAgent()


@pytest.fixture
def sample_tracks():
    return [
        MidiTrackData(
            name="Drums", instrument=Instrument.DRUMS, channel=9,
            events=[NoteEvent(pitch=36, velocity=100, start_tick=0, duration_ticks=240, channel=9)],
            program=0,
        ),
        MidiTrackData(
            name="Bass", instrument=Instrument.BASS, channel=1,
            events=[NoteEvent(pitch=36, velocity=90, start_tick=0, duration_ticks=480, channel=1)],
            program=33,
        ),
        MidiTrackData(
            name="Guitar", instrument=Instrument.ELECTRIC_GUITAR, channel=2,
            events=[NoteEvent(pitch=52, velocity=80, start_tick=0, duration_ticks=480, channel=2)],
            program=29,
        ),
    ]


@pytest.fixture
def basic_context():
    config = SessionConfig(genre=Genre.CLASSIC_ROCK)
    return SessionContext(config=config)


class TestMixerAgent:
    def test_produces_mix_config(self, mixer, sample_tracks, basic_context):
        result = mixer.process(sample_tracks, basic_context)
        assert isinstance(result, MixConfig)

    def test_one_config_per_track(self, mixer, sample_tracks, basic_context):
        result = mixer.process(sample_tracks, basic_context)
        assert len(result.tracks) == len(sample_tracks)

    def test_drums_centered(self, mixer, sample_tracks, basic_context):
        result = mixer.process(sample_tracks, basic_context)
        drum_config = next(t for t in result.tracks if t.instrument == Instrument.DRUMS)
        assert drum_config.pan == 0.0

    def test_bass_centered(self, mixer, sample_tracks, basic_context):
        result = mixer.process(sample_tracks, basic_context)
        bass_config = next(t for t in result.tracks if t.instrument == Instrument.BASS)
        assert bass_config.pan == 0.0

    def test_volumes_in_range(self, mixer, sample_tracks, basic_context):
        result = mixer.process(sample_tracks, basic_context)
        for tc in result.tracks:
            assert 0.0 <= tc.volume <= 1.0
            assert -1.0 <= tc.pan <= 1.0

    def test_master_volume(self, mixer, sample_tracks, basic_context):
        result = mixer.process(sample_tracks, basic_context)
        assert 0.0 < result.master_volume <= 1.0

    def test_works_without_llm(self, sample_tracks, basic_context):
        mixer = MixerAgent(llm=None)
        result = mixer.process(sample_tracks, basic_context)
        assert isinstance(result, MixConfig)
