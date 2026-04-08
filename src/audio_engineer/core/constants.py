"""MIDI constants and music theory reference data."""

# Core MIDI constants
MIDDLE_C = 60
MIDI_DRUM_CHANNEL = 9
TICKS_PER_BEAT = 480

# General MIDI Drum Map (Channel 10 / index 9)
GM_DRUMS: dict[str, int] = {
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
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
}

# Chromatic note names
NOTE_NAMES: list[str] = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
]

# General MIDI Program Numbers (0-indexed)
GM_PROGRAMS: dict[str, int] = {
    "acoustic_grand_piano": 0,
    "bright_acoustic_piano": 1,
    "electric_grand_piano": 2,
    "honky_tonk_piano": 3,
    "electric_piano_1": 4,
    "electric_piano_2": 5,
    "harpsichord": 6,
    "clavinet": 7,
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "dulcimer": 15,
    "drawbar_organ": 16,
    "percussive_organ": 17,
    "rock_organ": 18,
    "church_organ": 19,
    "reed_organ": 20,
    "accordion": 21,
    "harmonica": 22,
    "nylon_guitar": 24,
    "steel_guitar": 25,
    "jazz_guitar": 26,
    "electric_guitar_clean": 27,
    "electric_guitar_muted": 28,
    "electric_guitar_overdriven": 29,
    "electric_guitar_distortion": 30,
    "electric_guitar_harmonics": 31,
    "acoustic_bass": 32,
    "electric_bass_finger": 33,
    "electric_bass_pick": 34,
    "fretless_bass": 35,
    "slap_bass_1": 36,
    "slap_bass_2": 37,
    "synth_bass_1": 38,
    "synth_bass_2": 39,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "alto_sax": 65,
    "tenor_sax": 66,
    "flute": 73,
    "clarinet": 71,
}

# Chord formulas as interval lists (semitones from root)
CHORD_FORMULAS: dict[str, list[int]] = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dom7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "power": [0, 7],
    "dim7": [0, 3, 6, 9],
    "min_maj7": [0, 3, 7, 11],
    "add9": [0, 4, 7, 14],
}
