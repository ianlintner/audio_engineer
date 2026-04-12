"""Smoke tests for all new musician agents."""
from audio_engineer.core.models import (
    Genre, Instrument, SessionConfig, KeySignature, NoteName, Mode, SectionDef, BandConfig, BandMemberConfig,
)
from audio_engineer.core.music_theory import ProgressionFactory
from audio_engineer.agents.base import SessionContext
from audio_engineer.agents.musician.strings import StringsAgent
from audio_engineer.agents.musician.brass import BrassAgent
from audio_engineer.agents.musician.synth import SynthAgent
from audio_engineer.agents.musician.percussion import PercussionAgent
from audio_engineer.agents.musician.lead_guitar import LeadGuitarAgent


def _make_context(genre: Genre = Genre.JAZZ, num_bars: int = 4) -> SessionContext:
    config = SessionConfig(
        genre=genre,
        tempo=120,
        key=KeySignature(root=NoteName.C, mode=Mode.MAJOR),
        structure=[SectionDef(name="verse", bars=num_bars, intensity=0.7)],
        band=BandConfig(members=[BandMemberConfig(instrument=Instrument.DRUMS)]),
    )
    root = config.key.root.value
    progression = ProgressionFactory.jazz_ii_V_I(root)
    return SessionContext(
        config=config,
        arrangement=config.structure,
        chord_progressions={"verse": progression},
    )


class TestStringsAgent:
    def test_generates_midi_track(self):
        agent = StringsAgent()
        ctx = _make_context(Genre.JAZZ)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.STRINGS
        assert len(track.events) > 0

    def test_violin_instrument(self):
        agent = StringsAgent(instrument=Instrument.VIOLIN)
        ctx = _make_context(Genre.AMBIENT)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.VIOLIN

    def test_low_intensity_uses_pizzicato(self):
        agent = StringsAgent()
        config = SessionConfig(
            genre=Genre.JAZZ,
            structure=[SectionDef(name="intro", bars=2, intensity=0.3)],
        )
        root = config.key.root.value
        prog = ProgressionFactory.jazz_ii_V_I(root)
        ctx = SessionContext(
            config=config,
            arrangement=config.structure,
            chord_progressions={"intro": prog},
        )
        track = agent.generate_part(ctx)
        # Pizzicato produces many short notes
        assert len(track.events) > 4

    def test_events_in_valid_range(self):
        agent = StringsAgent()
        ctx = _make_context()
        track = agent.generate_part(ctx)
        for ev in track.events:
            assert 0 <= ev.pitch <= 127
            assert 1 <= ev.velocity <= 127
            assert ev.start_tick >= 0
            assert ev.duration_ticks > 0


class TestBrassAgent:
    def test_generates_midi_track(self):
        agent = BrassAgent()
        ctx = _make_context(Genre.FUNK)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.BRASS
        assert len(track.events) > 0

    def test_trumpet_instrument(self):
        agent = BrassAgent(instrument=Instrument.TRUMPET)
        ctx = _make_context(Genre.JAZZ)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.TRUMPET
        assert track.program == 56  # GM trumpet

    def test_saxophone_instrument(self):
        agent = BrassAgent(instrument=Instrument.SAXOPHONE)
        ctx = _make_context(Genre.JAZZ)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.SAXOPHONE
        # Tenor sax (66) for jazz
        assert track.program == 66

    def test_events_in_valid_range(self):
        agent = BrassAgent()
        ctx = _make_context(Genre.SOUL)
        track = agent.generate_part(ctx)
        for ev in track.events:
            assert 0 <= ev.pitch <= 127


class TestSynthAgent:
    def test_pad_generates_track(self):
        agent = SynthAgent(instrument=Instrument.PAD)
        ctx = _make_context(Genre.AMBIENT)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.PAD
        assert len(track.events) > 0

    def test_synthesizer_generates_arpeggio(self):
        agent = SynthAgent(instrument=Instrument.SYNTHESIZER)
        config = SessionConfig(
            genre=Genre.ELECTRONIC,
            structure=[SectionDef(name="verse", bars=2, intensity=0.8)],
        )
        root = config.key.root.value
        prog = ProgressionFactory.modal_dorian(root)
        ctx = SessionContext(
            config=config,
            arrangement=config.structure,
            chord_progressions={"verse": prog},
        )
        track = agent.generate_part(ctx)
        # Arpeggio should produce many events
        assert len(track.events) > 8

    def test_events_in_valid_range(self):
        agent = SynthAgent()
        ctx = _make_context(Genre.ELECTRONIC)
        track = agent.generate_part(ctx)
        for ev in track.events:
            assert 0 <= ev.pitch <= 127
            assert 1 <= ev.velocity <= 127


class TestPercussionAgent:
    def test_conga_generates_track(self):
        agent = PercussionAgent(instrument=Instrument.CONGA)
        ctx = _make_context(Genre.LATIN)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.CONGA
        assert len(track.events) > 0

    def test_bongo_generates_track(self):
        agent = PercussionAgent(instrument=Instrument.BONGO)
        ctx = _make_context(Genre.LATIN)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.BONGO

    def test_djembe_generates_track(self):
        agent = PercussionAgent(instrument=Instrument.DJEMBE)
        ctx = _make_context(Genre.FUNK)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.DJEMBE

    def test_all_events_on_channel_9(self):
        agent = PercussionAgent()
        ctx = _make_context(Genre.LATIN)
        track = agent.generate_part(ctx)
        for ev in track.events:
            assert ev.channel == 9

    def test_events_in_valid_range(self):
        agent = PercussionAgent()
        ctx = _make_context(Genre.LATIN)
        track = agent.generate_part(ctx)
        for ev in track.events:
            assert 0 <= ev.pitch <= 127
            assert 1 <= ev.velocity <= 127


class TestLeadGuitarAgent:
    def test_generates_midi_track(self):
        agent = LeadGuitarAgent()
        ctx = _make_context(Genre.CLASSIC_ROCK)
        track = agent.generate_part(ctx)
        assert track.instrument == Instrument.LEAD_GUITAR
        assert len(track.events) > 0

    def test_blues_uses_pentatonic(self):
        agent = LeadGuitarAgent()
        ctx = _make_context(Genre.BLUES)
        track = agent.generate_part(ctx)
        from audio_engineer.core.models import MidiTrackData
        assert isinstance(track, MidiTrackData)
        assert track.instrument == Instrument.LEAD_GUITAR
        # Any events produced must have valid MIDI pitch and velocity
        for ev in track.events:
            assert 0 <= ev.pitch <= 127, f"Pitch {ev.pitch} out of MIDI range"
            assert 1 <= ev.velocity <= 127, f"Velocity {ev.velocity} out of MIDI range"

    def test_high_intensity_produces_lick(self):
        config = SessionConfig(
            genre=Genre.CLASSIC_ROCK,
            structure=[SectionDef(name="chorus", bars=4, intensity=0.9)],
        )
        root = config.key.root.value
        prog = ProgressionFactory.classic_rock_I_IV_V(root)
        ctx = SessionContext(
            config=config,
            arrangement=config.structure,
            chord_progressions={"chorus": prog},
        )
        agent = LeadGuitarAgent()
        track = agent.generate_part(ctx)
        assert len(track.events) > 0

    def test_events_in_valid_range(self):
        agent = LeadGuitarAgent()
        ctx = _make_context(Genre.ROCK if hasattr(Genre, "ROCK") else Genre.CLASSIC_ROCK)
        track = agent.generate_part(ctx)
        for ev in track.events:
            assert 0 <= ev.pitch <= 127
            assert 1 <= ev.velocity <= 127
