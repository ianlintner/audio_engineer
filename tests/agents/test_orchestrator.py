"""Tests for the SessionOrchestrator."""
import json
from pathlib import Path

import pytest

from audio_engineer.core.models import (
    Genre, Instrument, SessionConfig, SessionStatus, Session,
    KeySignature, NoteName, Mode, BandConfig, BandMemberConfig, SectionDef,
)
from audio_engineer.agents.orchestrator import SessionOrchestrator


@pytest.fixture
def orchestrator(tmp_path):
    return SessionOrchestrator(output_dir=tmp_path)


@pytest.fixture
def config():
    return SessionConfig(
        genre=Genre.CLASSIC_ROCK,
        tempo=120,
        key=KeySignature(root=NoteName.E, mode=Mode.MINOR),
        structure=[
            SectionDef(name="intro", bars=4, intensity=0.5),
            SectionDef(name="verse", bars=4, intensity=0.6),
            SectionDef(name="chorus", bars=4, intensity=0.9),
        ],
    )


class TestCreateSession:
    def test_returns_session(self, orchestrator):
        session = orchestrator.create_session()
        assert isinstance(session, Session)
        assert session.status == SessionStatus.CREATED

    def test_assigns_id(self, orchestrator):
        session = orchestrator.create_session()
        assert len(session.id) == 8

    def test_uses_provided_config(self, orchestrator, config):
        session = orchestrator.create_session(config)
        assert session.config.genre == Genre.CLASSIC_ROCK
        assert session.config.tempo == 120

    def test_default_config_when_none(self, orchestrator):
        session = orchestrator.create_session(None)
        assert session.config.genre == Genre.CLASSIC_ROCK


class TestRunSession:
    def test_produces_tracks(self, orchestrator, config):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        assert "drums" in session.tracks
        assert "bass" in session.tracks
        assert "guitar" in session.tracks

    def test_status_is_complete(self, orchestrator, config):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        assert session.status == SessionStatus.COMPLETE

    def test_output_files_created(self, orchestrator, config, tmp_path):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        assert len(session.output_files) > 0
        for f in session.output_files:
            assert Path(f).exists()

    def test_midi_files_in_output(self, orchestrator, config, tmp_path):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        midi_files = [f for f in session.output_files if f.endswith(".mid")]
        # full + drums + bass + guitar = 4 MIDI files
        assert len(midi_files) >= 4

    def test_config_json_exported(self, orchestrator, config, tmp_path):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        json_files = [f for f in session.output_files if f.endswith(".json")]
        assert len(json_files) == 1
        data = json.loads(Path(json_files[0]).read_text())
        assert data["genre"] == "classic_rock"

    def test_output_dir_structure(self, orchestrator, config, tmp_path):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        session_dir = tmp_path / session.id
        assert session_dir.is_dir()
        files = list(session_dir.iterdir())
        assert len(files) >= 4

    def test_with_keys_instrument(self, orchestrator, tmp_path):
        config = SessionConfig(
            genre=Genre.POP,
            structure=[SectionDef(name="verse", bars=4, intensity=0.6)],
            band=BandConfig(members=[
                BandMemberConfig(instrument=Instrument.DRUMS),
                BandMemberConfig(instrument=Instrument.BASS),
                BandMemberConfig(instrument=Instrument.ELECTRIC_GUITAR),
                BandMemberConfig(instrument=Instrument.KEYS),
            ]),
        )
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        assert "keys" in session.tracks
        assert session.status == SessionStatus.COMPLETE

    def test_blues_genre(self, orchestrator, tmp_path):
        config = SessionConfig(
            genre=Genre.BLUES,
            structure=[SectionDef(name="verse", bars=4, intensity=0.6)],
        )
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        assert session.status == SessionStatus.COMPLETE

    def test_mix_config_set(self, orchestrator, config):
        session = orchestrator.create_session(config)
        session = orchestrator.run_session(session)

        assert session.mix is not None


class TestOrchestratorProviderRegistry:
    def test_orchestrator_has_provider_registry(self, tmp_path):
        orch = SessionOrchestrator(output_dir=tmp_path)
        assert orch.provider_registry is not None

    def test_registry_has_midi_provider(self, tmp_path):
        orch = SessionOrchestrator(output_dir=tmp_path)
        available = orch.provider_registry.list_available()
        assert "midi_engine" in available

    def test_registry_lists_all_providers(self, tmp_path):
        orch = SessionOrchestrator(output_dir=tmp_path)
        all_names = orch.provider_registry.list_providers()
        # At minimum: midi_engine. Gemini if available.
        assert "midi_engine" in all_names

    def test_session_produces_track_composer(self, tmp_path):
        from audio_engineer.core.models import SessionConfig

        orch = SessionOrchestrator(output_dir=tmp_path)
        session = orch.create_session(SessionConfig())
        session = orch.run_session(session)
        # The composer should have been used internally
        assert session.status.value == "complete"
        assert len(session.output_files) > 0
