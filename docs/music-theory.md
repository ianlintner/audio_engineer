# Music Theory Internals

The `audio_engineer.core.music_theory` module provides the building blocks that every agent uses to generate musically correct output.

---

## Scales

### Scale Construction

A scale is derived from a root note and a mode interval pattern expressed as semitone offsets from the root (e.g. `[0, 2, 4, 5, 7, 9, 11]` for major).

All supported modes (defined in `SCALE_FORMULAS` in `core/constants.py`):

| Mode | Intervals (semitones from root) |
| ---- | -------------------------------- |
| `major` | 0 2 4 5 7 9 11 |
| `minor` | 0 2 3 5 7 8 10 |
| `dorian` | 0 2 3 5 7 9 10 |
| `mixolydian` | 0 2 4 5 7 9 10 |
| `phrygian` | 0 1 3 5 7 8 10 |
| `lydian` | 0 2 4 6 7 9 11 |
| `locrian` | 0 1 3 5 6 8 10 |
| `harmonic_minor` | 0 2 3 5 7 8 11 |
| `melodic_minor` | 0 2 3 5 7 9 11 |
| `whole_tone` | 0 2 4 6 8 10 *(6 notes)* |
| `diminished` | 0 2 3 5 6 8 9 11 |
| `augmented` | 0 3 4 7 8 11 |
| `chromatic` | 0 1 2 3 4 5 6 7 8 9 10 11 |
| `bebop_dominant` | 0 2 4 5 7 9 10 11 |
| `bebop_major` | 0 2 4 5 7 8 9 11 |
| `spanish_phrygian` | 0 1 4 5 7 8 10 *(flamenco / Phrygian dominant)* |
| `hungarian_minor` | 0 2 3 6 7 8 11 |
| `pentatonic_major` | 0 2 4 7 9 |
| `pentatonic_minor` | 0 3 5 7 10 |
| `blues` | 0 3 5 6 7 10 |

Scale degrees are calculated as cumulative semitone offsets from the MIDI note number for the root.

---

## Chord Progressions

Progressions are expressed as Roman numeral sequences and resolved to absolute chord roots at runtime:

| Genre | Default Progression |
| ----- | ------------------- |
| `classic_rock` | I – IV – V – I |
| `blues` | I7 – IV7 – I7 – V7 – IV7 – I7 |
| `pop` | I – V – vi – IV |
| `folk` | I – IV – I – V |
| `country` | I – I – IV – IV – V – IV – I – V |
| `jazz` | ii min7 – V dom7 – I maj7 (ii-V-I) |
| `funk` | I dom7 – IV dom7 |
| `reggae` | I – IV – V (one-drop feel) |
| `metal` | I – bVII – bVI (power chords) |
| `hip_hop` | i min7 – VI maj7 – III maj7 – VII dom7 |
| `latin` | ii min7 – V dom7 – I maj7 (tumbao feel) |
| `gospel` | I – IV – I – V |
| `bossa_nova` | ii min7 – V dom7 – I maj7 – IV sus2 – I maj7 |

Agents call `MusicTheory.get_progression(genre, key, mode, sections)` to receive a list of `(root_note, chord_type)` tuples, one per bar.

### ProgressionFactory

`ProgressionFactory` provides named progression builders returning a `ChordProgression` object:

| Method | Description |
| ------ | ----------- |
| `jazz_ii_V_I(key)` | ii min7 – V dom7 – I maj7 |
| `jazz_turnaround(key)` | I maj7 – vi min7 – ii min7 – V dom7 |
| `jazz_rhythm_changes(key)` | 8-chord Rhythm Changes (Bb jazz standard form) |
| `blues_jazz(key)` | 13-chord jazz blues with tritone substitutions |
| `modal_dorian(key)` | 2-chord sustained Dorian vamp (i min7 – IV dom7) |
| `bossa_nova(key)` | ii min7 – V dom7 – I maj7 – IV sus2 – I maj7 |
| `minor_i_VII_VI_VII(key)` | Natural minor vamp: i – bVII – bVI – bVII |
| `gospel_I_IV_I_V(key)` | I – IV – I – V gospel changes |
| `metal_power_I_VII_VI(key)` | I – bVII – bVI – bVII power chord progression |
| `funk_I7_IV7(key)` | Dominant 7th vamp: I7 – IV7 |
| `classic_rock_I_IV_V(key)` | I – IV – V – I classic rock changes |

---

## Chord Voicings

`MusicTheory.get_chord_voicing(root, chord_type, octave)` returns a list of MIDI note numbers for a given chord.

All supported chord types (defined in `CHORD_FORMULAS` in `core/constants.py`):

| Type | Intervals | Example (C root) |
| ---- | --------- | ---------------- |
| `major` | 0, 4, 7 | C E G |
| `minor` | 0, 3, 7 | C Eb G |
| `dom7` | 0, 4, 7, 10 | C E G Bb |
| `maj7` | 0, 4, 7, 11 | C E G B |
| `min7` | 0, 3, 7, 10 | C Eb G Bb |
| `dim7` | 0, 3, 6, 9 | C Eb Gb A |
| `half_dim` | 0, 3, 6, 10 | C Eb Gb Bb (ø7) |
| `aug` | 0, 4, 8 | C E Ab |
| `sus2` | 0, 2, 7 | C D G |
| `sus4` | 0, 5, 7 | C F G |
| `power` | 0, 7 | C G (no third) |
| `add9` | 0, 4, 7, 14 | C E G D |
| `9th` | 0, 4, 7, 10, 14 | C E G Bb D |
| `maj9` | 0, 4, 7, 11, 14 | C E G B D |
| `min9` | 0, 3, 7, 10, 14 | C Eb G Bb D |
| `dom9` | 0, 4, 7, 10, 14 | C E G Bb D |
| `dom11` | 0, 4, 7, 10, 14, 17 | C E G Bb D F |
| `maj11` | 0, 4, 7, 11, 14, 17 | C E G B D F |
| `min11` | 0, 3, 7, 10, 14, 17 | C Eb G Bb D F |
| `dom13` | 0, 4, 7, 10, 14, 17, 21 | C E G Bb D F A |
| `maj13` | 0, 4, 7, 11, 14, 17, 21 | C E G B D F A |
| `min13` | 0, 3, 7, 10, 14, 17, 21 | C Eb G Bb D F A |
| `sharp9` | 0, 4, 7, 10, 15 | C E G Bb D# (Hendrix chord) |
| `alt` | 0, 4, 6, 10, 15 | altered dominant |
| `6th` | 0, 4, 7, 9 | C E G A |
| `min6` | 0, 3, 7, 9 | C Eb G A |
| `69` | 0, 4, 7, 9, 14 | C E G A D |
| `quartal` | 0, 5, 10 | C F Bb (stacked 4ths) |
| `quartal5` | 0, 5, 10, 15 | C F Bb Eb (4 stacked 4ths) |
| `flat5` | 0, 4, 6 | C E Gb |
| `sharp11` | 0, 4, 7, 11, 18 | C E G B F# |

---

## MIDI Note Mapping

Notes are referenced by MIDI number (0–127). Middle C = C4 = MIDI 60.

```
C4  = 60   D4  = 62   E4  = 64   F4  = 65
G4  = 67   A4  = 69   B4  = 71   C5  = 72
```

Bass lines typically run in octave 2–3 (MIDI 36–59).  
Guitar voicings run in octave 3–5 (MIDI 48–84).

---

## TICKS_PER_BEAT

The MIDI engine uses `TICKS_PER_BEAT = 480` (defined in `core/constants.py`). This gives 16th-note resolution at 120 ticks per 16th note.

| Duration | Ticks |
| -------- | ----- |
| Whole note | 1920 |
| Half note | 960 |
| Quarter note | 480 |
| 8th note | 240 |
| 16th note | 120 |
| 32nd note | 60 |

---

## Pattern Library

Genre-specific rhythmic patterns live in `core/patterns.py`.

### Drum Patterns

Each genre registers one or more `DrumPattern` objects, each with a `.name` and a `.to_events(bar_offset, intensity)` method returning a list of `NoteEvent` objects.

40+ patterns are registered across 22 genres. Access them via `PatternRepository`:

```python
from audio_engineer.core.patterns import PatternRepository
from audio_engineer.core.models import Genre

repo = PatternRepository()
patterns = repo.get_drum_patterns(Genre.JAZZ)
events = patterns[0].to_events(bar_offset=0, intensity=0.8)
```

### Drum Rudiments

All 40 PAS Standard Drum Rudiments are encoded as `NoteEvent` sequences and available via the `DRUM_RUDIMENTS` registry:

```python
from audio_engineer.core.patterns import DRUM_RUDIMENTS

rudiment = DRUM_RUDIMENTS["single_paradiddle"]
events = rudiment.to_events(bar_offset=0, beat_offset=1.0)
```

Categories: single/multiple stroke rolls (15), diddles (4), flams (12), drags (9+).

### Bass Patterns

`BassPattern` objects generate bass `NoteEvent` lists from a root MIDI note:

```python
from audio_engineer.core.patterns import BASS_PATTERNS
from audio_engineer.core.constants import TICKS_PER_BEAT

pattern = BASS_PATTERNS["jazz_walking"]
events = pattern.to_events(root_midi=48, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
```

Available patterns: `jazz_walking`, `funk_slap`, `reggae_skank`, `rnb_two_feel`, `pop_root_fifth`, `latin_tumbao`, `motown_bass_line`, `country_boom_chick`.

### Melodic Patterns

`MelodicPattern` objects generate chord-tone `NoteEvent` lists from a list of MIDI pitches:

```python
from audio_engineer.core.patterns import MELODIC_PATTERNS

pattern = MELODIC_PATTERNS["keys_synth_arp"]
chord_pitches = [60, 64, 67]  # C major
events = pattern.to_events(chord_pitches, tpb=TICKS_PER_BEAT, bar_offset_ticks=0)
```

Available patterns: `jazz_chord_shell`, `jazz_chord_full`, `guitar_arpeggio_up`, `guitar_arpeggio_down`, `guitar_travis_picking`, `guitar_bossa_comp`, `funk_rhythm_guitar_16th`, `keys_stride_left_hand`, `keys_jazz_two_handed`, `keys_synth_arp`.
