"""Tests for expanded constants: GM programs, drum map, scales, chords."""
import pytest
from audio_engineer.core.constants import (
    GM_PROGRAMS,
    GM_DRUMS,
    SCALE_FORMULAS,
    CHORD_FORMULAS,
)


class TestGMPrograms:
    def test_all_128_programs_present(self):
        """Every GM program number 0-127 should be represented."""
        program_numbers = set(GM_PROGRAMS.values())
        for n in range(128):
            assert n in program_numbers, f"GM program {n} missing"

    def test_piano_programs(self):
        assert GM_PROGRAMS["acoustic_grand_piano"] == 0
        assert GM_PROGRAMS["electric_piano_1"] == 4
        assert GM_PROGRAMS["harpsichord"] == 6

    def test_strings(self):
        assert GM_PROGRAMS["violin"] == 40
        assert GM_PROGRAMS["cello"] == 42
        assert GM_PROGRAMS["string_ensemble_1"] == 48
        assert GM_PROGRAMS["orchestral_harp"] == 46
        assert GM_PROGRAMS["timpani"] == 47

    def test_brass(self):
        assert GM_PROGRAMS["trumpet"] == 56
        assert GM_PROGRAMS["french_horn"] == 60
        assert GM_PROGRAMS["brass_section"] == 61

    def test_woodwinds(self):
        assert GM_PROGRAMS["flute"] == 73
        assert GM_PROGRAMS["clarinet"] == 71
        assert GM_PROGRAMS["oboe"] == 68
        assert GM_PROGRAMS["bassoon"] == 70
        assert GM_PROGRAMS["piccolo"] == 72

    def test_synth_leads(self):
        assert GM_PROGRAMS["lead_square"] == 80
        assert GM_PROGRAMS["lead_sawtooth"] == 81

    def test_synth_pads(self):
        assert GM_PROGRAMS["pad_new_age"] == 88
        assert GM_PROGRAMS["pad_warm"] == 89
        assert GM_PROGRAMS["pad_polysynth"] == 90
        assert GM_PROGRAMS["pad_halo"] == 94

    def test_ethnic(self):
        assert GM_PROGRAMS["sitar"] == 104
        assert GM_PROGRAMS["banjo"] == 105
        assert GM_PROGRAMS["kalimba"] == 108

    def test_percussive(self):
        assert GM_PROGRAMS["steel_drums"] == 114
        assert GM_PROGRAMS["taiko_drum"] == 116
        assert GM_PROGRAMS["synth_drum"] == 118


class TestGMDrums:
    def test_standard_kit_intact(self):
        assert GM_DRUMS["kick"] == 36
        assert GM_DRUMS["snare"] == 38
        assert GM_DRUMS["closed_hihat"] == 42
        assert GM_DRUMS["open_hihat"] == 46
        assert GM_DRUMS["crash"] == 49
        assert GM_DRUMS["ride"] == 51

    def test_extended_percussion(self):
        assert GM_DRUMS["cowbell"] == 56
        assert GM_DRUMS["tambourine"] == 54
        assert GM_DRUMS["ride_bell"] == 53
        assert GM_DRUMS["hi_bongo"] == 60
        assert GM_DRUMS["low_bongo"] == 61
        assert GM_DRUMS["open_hi_conga"] == 63
        assert GM_DRUMS["low_conga"] == 64
        assert GM_DRUMS["maracas"] == 70
        assert GM_DRUMS["claves"] == 75
        assert GM_DRUMS["mute_triangle"] == 80
        assert GM_DRUMS["open_triangle"] == 81
        assert GM_DRUMS["vibraslap"] == 58

    def test_all_values_in_valid_midi_range(self):
        for name, val in GM_DRUMS.items():
            assert 0 <= val <= 127, f"{name} out of range: {val}"


class TestExpandedScales:
    @pytest.mark.parametrize("scale", [
        "lydian", "phrygian", "locrian",
        "harmonic_minor", "melodic_minor",
        "whole_tone", "diminished", "augmented", "chromatic",
        "bebop_dominant", "bebop_major",
        "spanish_phrygian", "hungarian_minor",
    ])
    def test_new_scale_present(self, scale):
        assert scale in SCALE_FORMULAS

    def test_whole_tone_has_6_notes(self):
        assert len(SCALE_FORMULAS["whole_tone"]) == 6

    def test_chromatic_has_12_notes(self):
        assert len(SCALE_FORMULAS["chromatic"]) == 12

    def test_harmonic_minor_formula(self):
        assert SCALE_FORMULAS["harmonic_minor"] == [0, 2, 3, 5, 7, 8, 11]

    def test_lydian_has_raised_fourth(self):
        assert 6 in SCALE_FORMULAS["lydian"]  # #4 = tritone

    def test_all_formulas_start_at_zero(self):
        for name, formula in SCALE_FORMULAS.items():
            assert formula[0] == 0, f"{name} doesn't start at 0"

    def test_all_formulas_sorted(self):
        for name, formula in SCALE_FORMULAS.items():
            assert formula == sorted(formula), f"{name} not sorted"


class TestExpandedChords:
    @pytest.mark.parametrize("quality", [
        "half_dim", "dom9", "maj9", "min9", "sharp9", "alt",
        "dom11", "maj11", "min11", "dom13", "maj13", "min13",
        "6th", "min6", "69", "quartal", "quartal5",
    ])
    def test_new_chord_quality_present(self, quality):
        assert quality in CHORD_FORMULAS

    def test_half_dim_formula(self):
        # m7b5: root, m3, b5, m7
        assert CHORD_FORMULAS["half_dim"] == [0, 3, 6, 10]

    def test_sharp9_has_five_notes(self):
        assert len(CHORD_FORMULAS["sharp9"]) == 5

    def test_quartal_uses_fourths(self):
        # Stacked 4ths
        assert CHORD_FORMULAS["quartal"] == [0, 5, 10]

    def test_all_formulas_start_at_zero(self):
        for name, formula in CHORD_FORMULAS.items():
            assert formula[0] == 0, f"{name} doesn't start at 0"
