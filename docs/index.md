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

## Feature Overview

=== "Musician Agents"
    - 🥁 **Drummer** — genre-aware kick, snare, and hi-hat patterns
    - 🎸 **Bassist** — root-note bass lines locked to drums and chord changes
    - 🎸 **Guitarist** — rhythm/lead guitar parts and power chords
    - 🎹 **Keyboardist** — chord voicings, pads, and arpeggios

=== "Engineering Agents"
    - 🎚️ **Mixer** — per-track volume, pan, EQ curves
    - 🔊 **Mastering** — final loudness and metadata

=== "AI & Providers"
    - 🤖 **LLM support** — OpenAI, Anthropic, or Google Gemini for guided generation
    - 🎵 **Google Lyria 3** — full-length AI music generation via `MusicGenerationAgent`
    - 🔌 **Multi-provider system** — `ProviderRegistry` routes requests to the best available backend
    - 🔊 **Audio analysis & TTS** — `AudioAnalysisAgent` and `TTSAgent` via the Gemini package

=== "Infrastructure"
    - 🛠️ **MCP Server** — expose generation tools for GitHub Copilot, Claude Code, and other AI assistants
    - 🌐 **REST API** — FastAPI server for programmatic session control
    - 🖥️ **Web UI** — lightweight browser interface served alongside the API
    - 🎛️ **DAW export** — FluidSynth, TiMidity, GarageBand, Logic Pro, MIDI/WAV

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
