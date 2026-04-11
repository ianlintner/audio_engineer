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

---

## Available Modes

| Mode | Interval Pattern | Characteristic Sound |
| ---- | ---------------- | -------------------- |
| `major` | W W H W W W H | Bright, happy |
| `minor` | W H W W H W W | Dark, melancholic |
| `dorian` | W H W W W H W | Minor with raised 6th — jazzy |
| `mixolydian` | W W H W W H W | Major with flat 7th — bluesy |
| `phrygian` | H W W W H W W | Spanish / flamenco feel |
| `lydian` | W W W H W W H | Dreamy, floating |
| `locrian` | H W W H W W W | Dissonant, rarely used |

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
