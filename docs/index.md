# AI Music Studio

> **A multi-agent system for generating MIDI backing tracks.**

AI musician and engineer agents collaborate to produce genre-aware songs with drums, bass, guitar, and keys. Plug in an LLM provider for guided generation, or run fully algorithmically.

---

## Why AI Music Studio?

| Problem | Solution |
| ------- | -------- |
| Writing MIDI parts for every instrument is tedious | Agents generate parts automatically, reacting to each other |
| Algorithmic music often sounds mechanical | Genre-aware patterns + LLM guidance for human feel |
| Exporting to your DAW is a chore | Built-in FluidSynth, TiMidity, GarageBand, Logic Pro, and raw MIDI |
| Hard to iterate on arrangements | REST API and CLI for fast experimentation |

---

## Feature Overview

=== "Musician Agents"
    - 🥁 **Drummer** — genre-aware kick, snare, and hi-hat patterns
    - 🎸 **Bassist** — root-note bass lines locked to drums and chord changes
    - 🎸 **Guitarist** — rhythm/lead guitar parts and power chords
    - 🎹 **Keyboardist** — chord voicings, pads, and arpeggios

=== "Engineering Agents"
    - 🎚️ **Mixer** — per-track volume, pan, EQ curves
    - 🔊 **Mastering** — final loudness and metadata

=== "Infrastructure"
    - 🤖 **LLM support** — OpenAI, Anthropic, or any LangChain provider
    - 🎛️ **DAW export** — FluidSynth, TiMidity, GarageBand, Logic Pro, MIDI/WAV
    - 🌐 **REST API** — FastAPI server for programmatic session control

---

## Quick Example

```bash
pip install -e "."
python scripts/generate_demo.py --genre classic_rock --key E --mode minor --tempo 120 -v
```

Output lands in `./output/` as `<session-id>_full.mid` plus individual per-instrument files.

---

## Next Steps

- [**Installation**](installation.md) — get set up in minutes
- [**Quick Start**](quickstart.md) — generate your first backing track
- [**Architecture**](architecture.md) — understand how the agents work together
- [**Contributing**](contributing.md) — help improve the project
