# Music Theory Internals

The `audio_engineer.core.music_theory` module provides the building blocks that every agent uses to generate musically correct output.

---

## Scales

### Scale Construction

A scale is derived from a root note and a mode interval pattern:

```
major     = [2, 2, 1, 2, 2, 2, 1]   (W W H W W W H)
minor     = [2, 1, 2, 2, 1, 2, 2]   (W H W W H W W)
dorian    = [2, 1, 2, 2, 2, 1, 2]
mixolydian= [2, 2, 1, 2, 2, 1, 2]
phrygian  = [1, 2, 2, 2, 1, 2, 2]
lydian    = [2, 2, 2, 1, 2, 2, 1]
locrian   = [1, 2, 2, 1, 2, 2, 2]
```

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

Agents call `MusicTheory.get_progression(genre, key, mode, sections)` to receive a list of `(root_note, chord_type)` tuples, one per bar.

---

## Chord Voicings

`MusicTheory.get_chord_voicing(root, chord_type, octave)` returns a list of MIDI note numbers for a given chord.

Supported chord types:

| Type | Intervals | Example (C root) |
| ---- | --------- | ---------------- |
| `major` | 0, 4, 7 | C, E, G |
| `minor` | 0, 3, 7 | C, Eb, G |
| `dom7` | 0, 4, 7, 10 | C, E, G, Bb |
| `maj7` | 0, 4, 7, 11 | C, E, G, B |
| `min7` | 0, 3, 7, 10 | C, Eb, G, Bb |
| `power` | 0, 7 | C, G (no third) |
| `sus4` | 0, 5, 7 | C, F, G |

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

Genre-specific rhythmic patterns live in `core/patterns.py`. Each genre defines:

- `kick_pattern`: list of beat positions (in ticks) where the kick fires
- `snare_pattern`: snare hit positions
- `hihat_pattern`: hi-hat hit positions and open/closed flag
- `velocity_map`: dict of position → velocity (0–127)

These are reused by `DrummerAgent` and can be extended for new genres.
