"""MIDI constants and music theory reference data."""

# Core MIDI constants
MIDDLE_C = 60
MIDI_DRUM_CHANNEL = 9
TICKS_PER_BEAT = 480

# General MIDI Drum Map (Channel 10 / index 9)
GM_DRUMS: dict[str, int] = {
    # Standard kit
    "kick": 36,
    "snare": 38,
    "closed_hihat": 42,
    "open_hihat": 46,
    "crash": 49,
    "ride": 51,
    "floor_tom": 43,
    "mid_tom": 47,
    "high_tom": 50,
    "rim": 37,
    "clap": 39,
    "pedal_hihat": 44,
    # Extended GM percussion
    "ride_bell": 53,
    "tambourine": 54,
    "splash_cymbal": 55,
    "cowbell": 56,
    "vibraslap": 58,
    "ride_cymbal_2": 59,
    "hi_bongo": 60,
    "low_bongo": 61,
    "mute_hi_conga": 62,
    "open_hi_conga": 63,
    "low_conga": 64,
    "high_timbale": 65,
    "low_timbale": 66,
    "high_agogo": 67,
    "low_agogo": 68,
    "cabasa": 69,
    "maracas": 70,
    "short_whistle": 71,
    "long_whistle": 72,
    "short_guiro": 73,
    "long_guiro": 74,
    "claves": 75,
    "hi_wood_block": 76,
    "low_wood_block": 77,
    "mute_cuica": 78,
    "open_cuica": 79,
    "mute_triangle": 80,
    "open_triangle": 81,
    # Additional kit sounds
    "crash_2": 57,
    "snare_2": 40,
}

# Intervals in semitones
INTERVALS: dict[str, int] = {
    "P1": 0,
    "m2": 1,
    "M2": 2,
    "m3": 3,
    "M3": 4,
    "P4": 5,
    "TT": 6,
    "P5": 7,
    "m6": 8,
    "M6": 9,
    "m7": 10,
    "M7": 11,
    "P8": 12,
}

# Scale formulas as lists of semitone intervals from root
SCALE_FORMULAS: dict[str, list[int]] = {
    # Diatonic modes
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    # Pentatonic / blues
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    # Harmonic / melodic minor
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    # Symmetrical
    "whole_tone": [0, 2, 4, 6, 8, 10],
    "diminished": [0, 2, 3, 5, 6, 8, 9, 11],   # whole-half
    "augmented": [0, 3, 4, 7, 8, 11],
    "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    # Bebop
    "bebop_dominant": [0, 2, 4, 5, 7, 9, 10, 11],
    "bebop_major": [0, 2, 4, 5, 7, 8, 9, 11],
    # Exotic
    "spanish_phrygian": [0, 1, 4, 5, 7, 8, 10],  # flamenco / Phrygian dominant
    "hungarian_minor": [0, 2, 3, 6, 7, 8, 11],
}

# Chromatic note names
NOTE_NAMES: list[str] = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
]

# General MIDI Program Numbers (0-indexed)
GM_PROGRAMS: dict[str, int] = {
    # --- Piano (0-7) ---
    "acoustic_grand_piano": 0,
    "bright_acoustic_piano": 1,
    "electric_grand_piano": 2,
    "honky_tonk_piano": 3,
    "electric_piano_1": 4,
    "electric_piano_2": 5,
    "harpsichord": 6,
    "clavinet": 7,
    # --- Chromatic Percussion (8-15) ---
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "dulcimer": 15,
    # --- Organ (16-23) ---
    "drawbar_organ": 16,
    "percussive_organ": 17,
    "rock_organ": 18,
    "church_organ": 19,
    "reed_organ": 20,
    "accordion": 21,
    "harmonica": 22,
    "tango_accordion": 23,
    # --- Guitar (24-31) ---
    "nylon_guitar": 24,
    "steel_guitar": 25,
    "jazz_guitar": 26,
    "electric_guitar_clean": 27,
    "electric_guitar_muted": 28,
    "electric_guitar_overdriven": 29,
    "electric_guitar_distortion": 30,
    "electric_guitar_harmonics": 31,
    # --- Bass (32-39) ---
    "acoustic_bass": 32,
    "electric_bass_finger": 33,
    "electric_bass_pick": 34,
    "fretless_bass": 35,
    "slap_bass_1": 36,
    "slap_bass_2": 37,
    "synth_bass_1": 38,
    "synth_bass_2": 39,
    # --- Strings (40-47) ---
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "tremolo_strings": 44,
    "pizzicato_strings": 45,
    "orchestral_harp": 46,
    "timpani": 47,
    # --- Ensemble (48-55) ---
    "string_ensemble_1": 48,
    "string_ensemble_2": 49,
    "synth_strings_1": 50,
    "synth_strings_2": 51,
    "choir_aahs": 52,
    "voice_oohs": 53,
    "synth_voice": 54,
    "orchestra_hit": 55,
    # --- Brass (56-63) ---
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "muted_trumpet": 59,
    "french_horn": 60,
    "brass_section": 61,
    "synth_brass_1": 62,
    "synth_brass_2": 63,
    # --- Reed (64-71) ---
    "soprano_sax": 64,
    "alto_sax": 65,
    "tenor_sax": 66,
    "baritone_sax": 67,
    "oboe": 68,
    "english_horn": 69,
    "bassoon": 70,
    "clarinet": 71,
    # --- Pipe (72-79) ---
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "blown_bottle": 76,
    "shakuhachi": 77,
    "whistle": 78,
    "ocarina": 79,
    # --- Synth Lead (80-87) ---
    "lead_square": 80,
    "lead_sawtooth": 81,
    "lead_calliope": 82,
    "lead_chiff": 83,
    "lead_charang": 84,
    "lead_voice": 85,
    "lead_fifths": 86,
    "lead_bass_lead": 87,
    # --- Synth Pad (88-95) ---
    "pad_new_age": 88,
    "pad_warm": 89,
    "pad_polysynth": 90,
    "pad_choir": 91,
    "pad_bowed": 92,
    "pad_metallic": 93,
    "pad_halo": 94,
    "pad_sweep": 95,
    # --- Synth Effects (96-103) ---
    "fx_rain": 96,
    "fx_soundtrack": 97,
    "fx_crystal": 98,
    "fx_atmosphere": 99,
    "fx_brightness": 100,
    "fx_goblins": 101,
    "fx_echoes": 102,
    "fx_sci_fi": 103,
    # --- Ethnic (104-111) ---
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    # --- Percussive (112-119) ---
    "tinkle_bell": 112,
    "agogo": 113,
    "steel_drums": 114,
    "woodblock": 115,
    "taiko_drum": 116,
    "melodic_tom": 117,
    "synth_drum": 118,
    "reverse_cymbal": 119,
    # --- Sound Effects (120-127) ---
    "guitar_fret_noise": 120,
    "breath_noise": 121,
    "seashore": 122,
    "bird_tweet": 123,
    "telephone_ring": 124,
    "helicopter": 125,
    "applause": 126,
    "gunshot": 127,
}

# Chord formulas as interval lists (semitones from root)
CHORD_FORMULAS: dict[str, list[int]] = {
    # Triads
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "power": [0, 7],
    # 6th chords
    "6th": [0, 4, 7, 9],
    "min6": [0, 3, 7, 9],
    "69": [0, 4, 7, 9, 14],
    # 7th chords
    "dom7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dim7": [0, 3, 6, 9],
    "half_dim": [0, 3, 6, 10],    # m7b5 / ø7
    "min_maj7": [0, 3, 7, 11],
    "aug_maj7": [0, 4, 8, 11],
    # 9th chords
    "dom9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "min9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14],
    # Altered / extended dominants
    "sharp9": [0, 4, 7, 10, 15],   # dom7#9 ("Hendrix chord")
    "flat5": [0, 4, 6, 10],         # dom7b5
    "sharp11": [0, 4, 7, 10, 18],   # dom7#11 / Lydian dominant
    "alt": [0, 4, 6, 10, 15],       # altered dominant (b5, #9)
    # 11th chords
    "dom11": [0, 4, 7, 10, 14, 17],
    "maj11": [0, 4, 7, 11, 14, 17],
    "min11": [0, 3, 7, 10, 14, 17],
    # 13th chords
    "dom13": [0, 4, 7, 10, 14, 17, 21],
    "maj13": [0, 4, 7, 11, 14, 17, 21],
    "min13": [0, 3, 7, 10, 14, 17, 21],
    # Quartal harmony
    "quartal": [0, 5, 10],          # stacked perfect 4ths
    "quartal5": [0, 5, 10, 15],     # 4-note quartal voicing
}
