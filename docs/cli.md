# CLI Reference

The primary CLI entry point is `scripts/generate_demo.py`.

---

## Synopsis

```bash
python scripts/generate_demo.py [OPTIONS]
```

---

## Options

### Musical Parameters

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--genre` | string | `classic_rock` | Genre preset. Controls drum patterns, guitar voicings, and feel. |
| `--key` | string | `C` | Root note. Accepts `C`, `C#`, `D`, `D#`, `E`, `F`, `F#`, `G`, `G#`, `A`, `A#`, `B`. |
| `--mode` | string | `major` | Scale mode. See table below. |
| `--tempo` | int | `120` | Beats per minute (40–300). |
| `--sections` | int | `4` | Number of song sections (intro, verse, chorus, …). |
| `--with-keys` | flag | off | Include a `KeyboardistAgent` in the session. |

### Output & Rendering

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `--output` | path | `./output` | Directory where MIDI and audio files are written. |
| `--render-audio` | flag | off | Render the combined MIDI to WAV after generation. |
| `--backend` | string | `export` | Audio backend: `export` (MIDI only), `fluidsynth`, `timidity`. |

### Misc

| Option | Type | Default | Description |
| ------ | ---- | ------- | ----------- |
| `-v` / `--verbose` | flag | off | Enable `DEBUG`-level logging. |

---

## Available Genres

| Genre | Feel | Typical Tempo |
| ----- | ---- | ------------- |
| `classic_rock` | Four-on-the-floor with syncopated snare | 110–140 BPM |
| `blues` | Shuffled triplet feel | 80–120 BPM |
| `pop` | Clean, straight-eighth feel | 100–130 BPM |
| `folk` | Acoustic, sparse patterns | 80–110 BPM |
| `country` | Two-step, boom-chick feel | 100–140 BPM |
| `punk` | Fast, simple, aggressive | 140–200 BPM |
| `hard_rock` | Heavy, palm-muted riffs | 120–160 BPM |
| `jazz` | Swing ride cymbal, comping snare | 120–240 BPM |
| `funk` | 16th-note hi-hat, syncopated kick | 90–115 BPM |
| `reggae` | One-drop (kick beat 3, snare 2+4) | 60–90 BPM |
| `soul` | Gospel-influenced groove | 80–110 BPM |
| `rnb` | Trap hi-hat / modern R&B | 70–100 BPM |
| `metal` | Blast beats, double-kick, half-time | 160–250 BPM |
| `hip_hop` | Boom-bap, trap, lo-fi | 70–100 BPM |
| `latin` | Clave son/rumba, samba surdo | 90–130 BPM |
| `bossa_nova` | Quiet syncopated hi-hat | 110–140 BPM |
| `electronic` | 4-on-the-floor EDM / house | 120–140 BPM |
| `house` | Open hi-hat on off-beats | 120–135 BPM |
| `ambient` | Sparse, textural | 60–90 BPM |
| `gospel` | Soulful backbeat | 70–110 BPM |
| `swing` | Traditional jazz swing feel | 120–200 BPM |
| `bebop` | Fast bebop ride pattern | 180–320 BPM |

---

## Available Modes

| Mode | Semitone offsets | Characteristic Sound |
| ---- | ---------------- | -------------------- |
| `major` | 0 2 4 5 7 9 11 | Bright, happy |
| `minor` | 0 2 3 5 7 8 10 | Dark, melancholic |
| `dorian` | 0 2 3 5 7 9 10 | Minor with raised 6th — jazzy |
| `mixolydian` | 0 2 4 5 7 9 10 | Major with flat 7th — bluesy |
| `phrygian` | 0 1 3 5 7 8 10 | Spanish / flamenco feel |
| `lydian` | 0 2 4 6 7 9 11 | Dreamy, floating |
| `locrian` | 0 1 3 5 6 8 10 | Dissonant, unstable |
| `harmonic_minor` | 0 2 3 5 7 8 11 | Classical minor with raised 7th |
| `melodic_minor` | 0 2 3 5 7 9 11 | Jazz melodic minor |
| `whole_tone` | 0 2 4 6 8 10 | Dreamlike, symmetric |
| `diminished` | 0 2 3 5 6 8 9 11 | Tense, symmetric |
| `bebop_dominant` | 0 2 4 5 7 9 10 11 | Bebop passing tone |
| `bebop_major` | 0 2 4 5 7 8 9 11 | Bebop major with chromatic 6th |
| `spanish_phrygian` | 0 1 4 5 7 8 10 | Flamenco / Phrygian dominant |
| `hungarian_minor` | 0 2 3 6 7 8 11 | Eastern European, exotic |

---

## Examples

```bash
# Classic rock in E minor at 130 BPM
python scripts/generate_demo.py --genre classic_rock --key E --mode minor --tempo 130

# Blues shuffle in A minor, rendered to WAV
python scripts/generate_demo.py --genre blues --key A --mode minor \
  --render-audio --backend fluidsynth -v

# Pop with keyboard, custom output directory
python scripts/generate_demo.py --genre pop --key C --mode major \
  --with-keys --output ~/my-tracks

# Dorian jazz-rock groove
python scripts/generate_demo.py --genre classic_rock --key D --mode dorian --tempo 112
```

---

## MCP Server

The package also ships an MCP (Model Context Protocol) server entry point:

```bash
audio-engineer-mcp
```

This exposes the generation pipeline to LLM tool-use frameworks that support MCP.
