"""Tests for expanded genres, instruments, genre blending, and alias resolution."""
from __future__ import annotations

import pytest

from audio_engineer.core.models import (
    Genre,
    GenreBlend,
    Instrument,
    GENRE_ALIASES,
    resolve_genre,
    SessionConfig,
)
from audio_engineer.core.music_theory import ProgressionFactory


# ---------------------------------------------------------------------------
# Genre enum expansion
# ---------------------------------------------------------------------------

class TestGenreExpansion:
    """Verify we have a wide roster of genres and subgenres."""

    def test_genre_count_above_80(self):
        """We target ≥80 recognisable genres/subgenres."""
        assert len(Genre) >= 80

    @pytest.mark.parametrize("genre_value", [
        # Rock family
        "classic_rock", "hard_rock", "punk", "indie_rock", "alt_rock",
        "grunge", "prog_rock", "psychedelic_rock", "garage_rock",
        "post_rock", "surf_rock", "southern_rock", "soft_rock",
        # Metal family
        "metal", "thrash_metal", "death_metal", "doom_metal",
        "black_metal", "power_metal", "progressive_metal",
        "nu_metal", "metalcore",
        # Pop
        "pop", "synth_pop", "indie_pop", "dream_pop", "k_pop",
        "disco", "new_wave",
        # Blues
        "blues", "delta_blues", "chicago_blues",
        # Jazz
        "jazz", "swing", "bebop", "cool_jazz", "fusion",
        "smooth_jazz", "free_jazz", "acid_jazz",
        # Funk / Soul / R&B
        "funk", "soul", "rnb", "neo_soul", "motown",
        # Hip-hop
        "hip_hop", "trap", "lo_fi_hip_hop", "boom_bap",
        # Electronic
        "electronic", "house", "deep_house", "tech_house",
        "techno", "trance", "drum_and_bass", "dubstep",
        "ambient", "synthwave", "idm", "chillwave", "downtempo",
        "garage_electronic", "electro",
        # Country / folk
        "country", "folk", "bluegrass", "americana", "celtic",
        # Latin
        "latin", "bossa_nova", "salsa", "samba", "reggaeton",
        "cumbia", "tango",
        # Caribbean
        "reggae", "ska", "dub", "dancehall", "calypso",
        # African
        "afrobeat", "highlife",
        # World
        "flamenco", "middle_eastern", "bollywood",
        # Classical
        "classical", "baroque", "romantic_era", "cinematic",
        # Spiritual
        "gospel", "worship",
        # Experimental
        "noise", "shoegaze", "math_rock", "emo", "post_punk",
        "industrial", "vaporwave",
    ])
    def test_genre_enum_contains_value(self, genre_value: str):
        assert Genre(genre_value) is not None


# ---------------------------------------------------------------------------
# Instrument enum expansion
# ---------------------------------------------------------------------------

class TestInstrumentExpansion:
    """Verify the expanded instrument palette."""

    def test_instrument_count_above_40(self):
        assert len(Instrument) >= 40

    @pytest.mark.parametrize("instr_value", [
        "drums", "bass", "electric_guitar", "acoustic_guitar",
        "lead_guitar", "keys", "organ", "strings", "violin",
        "cello", "viola", "contrabass", "harp",
        "brass", "trumpet", "trombone", "french_horn", "tuba",
        "woodwinds", "saxophone", "flute", "clarinet", "oboe",
        "synthesizer", "pad", "vibraphone", "marimba",
        "percussion", "banjo", "ukulele", "mandolin", "sitar",
        "conga", "bongo", "djembe",
        "harmonica", "accordion", "steel_drums", "tabla",
        "erhu", "koto", "kalimba", "bagpipe", "fiddle",
        "electric_piano",
    ])
    def test_instrument_enum_contains_value(self, instr_value: str):
        assert Instrument(instr_value) is not None


# ---------------------------------------------------------------------------
# Genre alias / NLP resolution
# ---------------------------------------------------------------------------

class TestGenreAliases:
    """GENRE_ALIASES maps common terms to canonical Genre values."""

    def test_alias_count_above_150(self):
        assert len(GENRE_ALIASES) >= 150

    @pytest.mark.parametrize("text, expected", [
        ("trap", Genre.TRAP),
        ("lo-fi", Genre.LO_FI_HIP_HOP),
        ("lofi", Genre.LO_FI_HIP_HOP),
        ("dnb", Genre.DRUM_AND_BASS),
        ("drum and bass", Genre.DRUM_AND_BASS),
        ("jungle", Genre.DRUM_AND_BASS),
        ("edm", Genre.ELECTRONIC),
        ("hip-hop", Genre.HIP_HOP),
        ("rap", Genre.HIP_HOP),
        ("synthwave", Genre.SYNTHWAVE),
        ("retrowave", Genre.SYNTHWAVE),
        ("k-pop", Genre.K_POP),
        ("kpop", Genre.K_POP),
        ("big band", Genre.SWING),
        ("punk rock", Genre.PUNK),
        ("heavy metal", Genre.METAL),
        ("film score", Genre.CINEMATIC),
        ("arabic", Genre.MIDDLE_EASTERN),
        ("afrobeats", Genre.AFROBEAT),
        ("chillhop", Genre.LO_FI_HIP_HOP),
        ("ska punk", Genre.SKA),
        ("soca", Genre.CALYPSO),
        ("djent", Genre.PROGRESSIVE_METAL),
        ("2-step", Genre.GARAGE_ELECTRONIC),
    ])
    def test_resolve_genre_from_alias(self, text: str, expected: Genre):
        assert resolve_genre(text) == expected

    def test_resolve_genre_unknown_returns_none(self):
        assert resolve_genre("xyzzy_nonexistent") is None

    def test_resolve_genre_via_enum_value(self):
        """Direct enum values should resolve even if not in alias table."""
        assert resolve_genre("classic_rock") == Genre.CLASSIC_ROCK

    def test_resolve_genre_case_insensitive(self):
        assert resolve_genre("TRAP") == Genre.TRAP
        assert resolve_genre("Synthwave") == Genre.SYNTHWAVE


# ---------------------------------------------------------------------------
# GenreBlend model
# ---------------------------------------------------------------------------

class TestGenreBlend:
    """GenreBlend allows combining genres with weights."""

    def test_single_genre(self):
        blend = GenreBlend(genres=[Genre.JAZZ])
        assert blend.primary == Genre.JAZZ
        assert blend.normalised_weights == [1.0]

    def test_two_genres_equal_weight(self):
        blend = GenreBlend(genres=[Genre.JAZZ, Genre.FUNK])
        assert blend.primary == Genre.JAZZ  # first when tied
        assert blend.normalised_weights == [0.5, 0.5]

    def test_weighted_primary(self):
        blend = GenreBlend(
            genres=[Genre.CLASSIC_ROCK, Genre.JAZZ, Genre.FUNK],
            weights=[0.5, 0.3, 0.2],
        )
        assert blend.primary == Genre.CLASSIC_ROCK
        assert sum(blend.normalised_weights) == pytest.approx(1.0)

    def test_max_4_genres(self):
        with pytest.raises(Exception):  # noqa: PT011 — Pydantic raises ValidationError
            GenreBlend(genres=[Genre.POP, Genre.JAZZ, Genre.FUNK, Genre.BLUES, Genre.REGGAE])

    def test_weights_length_mismatch_rejected(self):
        with pytest.raises(Exception):  # noqa: PT011
            GenreBlend(genres=[Genre.JAZZ, Genre.FUNK], weights=[1.0])

    def test_negative_weight_rejected(self):
        with pytest.raises(Exception):  # noqa: PT011
            GenreBlend(genres=[Genre.JAZZ], weights=[-0.5])

    def test_zero_sum_weights_fall_back_to_equal(self):
        blend = GenreBlend(genres=[Genre.JAZZ, Genre.FUNK], weights=[0.0, 0.0])
        assert blend.normalised_weights == [0.5, 0.5]


# ---------------------------------------------------------------------------
# New ProgressionFactory methods
# ---------------------------------------------------------------------------

class TestExpandedProgressions:
    """Every new progression method should return a non-empty ChordProgression."""

    @pytest.mark.parametrize("factory_fn", [
        ProgressionFactory.indie_I_vi_iii_IV,
        ProgressionFactory.grunge_minor_vamp,
        ProgressionFactory.prog_rock_epic,
        ProgressionFactory.disco_I_vi_ii_V,
        ProgressionFactory.synthwave_i_III_VII_VI,
        ProgressionFactory.trap_minor_vamp,
        ProgressionFactory.trance_uplifting,
        ProgressionFactory.dubstep_halftime,
        ProgressionFactory.dnb_minor_tension,
        ProgressionFactory.salsa_montuno,
        ProgressionFactory.reggaeton_i_IV_V,
        ProgressionFactory.ska_offbeat,
        ProgressionFactory.afrobeat_vamp,
        ProgressionFactory.flamenco_phrygian,
        ProgressionFactory.middle_eastern_hijaz,
        ProgressionFactory.classical_I_IV_V_I,
        ProgressionFactory.baroque_circle_of_fifths,
        ProgressionFactory.cinematic_epic,
        ProgressionFactory.bluegrass_I_IV_V,
        ProgressionFactory.neo_soul_ii_V_I,
        ProgressionFactory.worship_I_IV_vi_V,
        ProgressionFactory.post_rock_ambient,
        ProgressionFactory.math_rock_odd,
        ProgressionFactory.emo_vi_IV_I_V,
        ProgressionFactory.industrial_power_riff,
    ])
    def test_progression_returns_nonempty(self, factory_fn):
        prog = factory_fn("C")
        assert len(prog) > 0

    @pytest.mark.parametrize("factory_fn", [
        ProgressionFactory.reggaeton_i_IV_V,
        ProgressionFactory.afrobeat_vamp,
        ProgressionFactory.flamenco_phrygian,
    ])
    def test_flat_key_progressions(self, factory_fn):
        """Progressions that previously crashed on flat keys like Bb."""
        prog = factory_fn("Bb")
        assert len(prog) > 0


# ---------------------------------------------------------------------------
# Centralised genre→progression routing
# ---------------------------------------------------------------------------

class TestCentralisedRouting:
    """Both orchestrator and midi_provider use get_genre_progressions."""

    def test_get_genre_progressions_import(self):
        from audio_engineer.core.music_theory import get_genre_progressions as fn
        result = fn(Genre.JAZZ, "C", "major")
        assert "verse" in result
        assert "chorus" in result


# ---------------------------------------------------------------------------
# Genre → progression routing
# ---------------------------------------------------------------------------

class TestGenreProgressionRouting:
    """Verify every Genre enum value produces a valid progression mapping
    through the orchestrator's genre progression lookup."""

    def test_all_genres_produce_progressions(self):
        from audio_engineer.agents.orchestrator import SessionOrchestrator
        orch = SessionOrchestrator()
        for genre in Genre:
            progs = orch._get_genre_progressions(genre, "C", "major")
            assert "verse" in progs
            assert "chorus" in progs
            assert len(progs["verse"]) > 0
            assert len(progs["chorus"]) > 0


# ---------------------------------------------------------------------------
# New instruments wire through midi_provider
# ---------------------------------------------------------------------------

class TestNewInstrumentWiring:
    """New Instrument values should be present in the MIDI provider agent map."""

    def test_all_non_vocal_instruments_mapped(self):
        from audio_engineer.providers.midi_provider import _INSTRUMENT_AGENTS
        unmapped = []
        for instr in Instrument:
            if instr == Instrument.VOCALS:
                continue
            if instr.value not in _INSTRUMENT_AGENTS:
                unmapped.append(instr.value)
        assert unmapped == [], f"Instruments not mapped to agents: {unmapped}"

    @pytest.mark.parametrize("instr_val", [
        "cello", "viola", "contrabass", "harp",
        "trombone", "french_horn", "tuba",
        "flute", "clarinet", "oboe",
        "harmonica", "accordion", "steel_drums",
        "tabla", "erhu", "koto", "kalimba", "bagpipe",
        "fiddle", "electric_piano",
    ])
    def test_new_instrument_generates_track(self, instr_val: str):
        from audio_engineer.providers.midi_provider import MidiProvider
        from audio_engineer.providers.base import TrackRequest
        provider = MidiProvider()
        req = TrackRequest(
            track_name=f"test_{instr_val}",
            description=f"Test {instr_val} track",
            instrument=instr_val,
            genre="classic_rock",
            tempo=120,
        )
        result = provider.generate_track(req)
        assert result.success, f"Failed for {instr_val}: {result.error}"


# ---------------------------------------------------------------------------
# SessionConfig with new genres
# ---------------------------------------------------------------------------

class TestSessionConfigWithNewGenres:
    """SessionConfig should accept the expanded genres."""

    @pytest.mark.parametrize("genre", [Genre.TRAP, Genre.SYNTHWAVE, Genre.DOOM_METAL, Genre.AFROBEAT])
    def test_session_config_accepts_genre(self, genre: Genre):
        cfg = SessionConfig(genre=genre)
        assert cfg.genre == genre
