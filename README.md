# 🎵 AI Music Studio

> **A multi-agent system for generating MIDI backing tracks.**  
> AI musician and engineer agents collaborate to produce complete, genre-aware songs with drums, bass, guitar, and keys.

[![CI](https://github.com/ianlintner/audio_engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/ianlintner/audio_engineer/actions/workflows/ci.yml)
[![Docs](https://github.com/ianlintner/audio_engineer/actions/workflows/docs.yml/badge.svg)](https://ianlintner.github.io/audio_engineer/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

## ✨ Features

- 🥁 **Drummer Agent** — genre-aware kick, snare, and hi-hat patterns
- 🎸 **Bassist Agent** — root-note bass lines locked to drums and chord changes
- 🎸 **Guitarist Agent** — rhythm/lead guitar parts and power chords
- 🎹 **Keyboardist Agent** — chord voicings, pads, and arpeggios
- 🎚️ **Mixer & Mastering Agents** — per-track volume, pan, and loudness metadata
- 🤖 **LLM-guided generation** — plug in OpenAI, Anthropic, or any LangChain provider
- 🎛️ **DAW integration** — FluidSynth, TiMidity, GarageBand, Logic Pro, and raw MIDI/WAV export
- 🌐 **REST API** — FastAPI server for programmatic session management
- 🔌 **Multi-provider system** — pluggable `AudioProvider` backends with capability-based routing (`ProviderRegistry`)
- 🤖 **Google Gemini integration** — full-length music generation via Lyria 3, audio analysis, and text-to-speech
- 🛠️ **MCP Server** — expose backing-track generation as MCP tools for GitHub Copilot, Claude Code, and other AI coding assistants
- 🖥️ **Web UI** — lightweight browser-based interface served alongside the REST API

---

## 📦 Installation

```bash
# Core install (MIDI generation only)
pip install -e "."

# With development tools
pip install -e ".[dev]"

# With REST API server
pip install -e ".[api]"

# With LLM providers (OpenAI / Anthropic)
pip install -e ".[llm]"

# With Google Gemini (Lyria 3 music generation, audio analysis, TTS)
pip install -e ".[gemini]"

# With audio processing (pydub — WAV/MP3 manipulation)
pip install -e ".[audio]"

# Everything
pip install -e ".[all]"
```

**Requirements:** Python 3.11+

---

## 🚀 Quick Start

```bash
# Generate a classic rock backing track in E minor at 120 BPM
python scripts/generate_demo.py --genre classic_rock --key E --mode minor --tempo 120 -v

# Pop song in C major with keyboard included
python scripts/generate_demo.py --genre pop --key C --mode major --with-keys

# Blues in A minor rendered to WAV via FluidSynth
python scripts/generate_demo.py --genre blues --key A --mode minor --render-audio --backend fluidsynth

# Thrash metal rhythm section at 200 BPM (stress-test script)
python scripts/generate_thrash.py

# Download and configure a SoundFont for audio rendering
python scripts/setup_soundfont.py

# Start the REST API server
pip install -e ".[api]"
python scripts/run_dev.py
```

Output files land in `./output/` by default, named `<session-id>_<instrument>.mid` plus a combined `<session-id>_full.mid`.

---

## 🏗️ Architecture

Tracks are generated **sequentially** — drums first, then bass, guitar, and keys — so each agent can react to what came before. The orchestrator manages chord progressions per section and coordinates file export.

```
SessionOrchestrator
├── DrummerAgent      → drum pattern generation
├── BassistAgent      → bass line locked to drums + chords
├── GuitaristAgent    → rhythm/lead guitar parts
├── KeyboardistAgent  → chord voicings and pads
├── MixerAgent        → volume, pan, EQ per track
└── MasteringAgent    → final loudness and metadata
```

See the **[full architecture docs](https://ianlintner.github.io/audio_engineer/architecture/)** for Mermaid diagrams, data flow, and DAW integration tiers.

---

## 🤖 Agents

| Agent              | Role                                         | Output          |
| ------------------ | -------------------------------------------- | --------------- |
| `DrummerAgent`     | Kick, snare, hi-hat patterns per section     | `MidiTrackData` |
| `BassistAgent`     | Root-note bass lines following chord changes | `MidiTrackData` |
| `GuitaristAgent`   | Rhythm guitar / power chords                 | `MidiTrackData` |
| `KeyboardistAgent` | Chord pads and voicings                      | `MidiTrackData` |
| `MixerAgent`       | Per-track volume, pan, EQ                    | `MixConfig`     |
| `MasteringAgent`   | Final processing metadata                    | `dict`          |

All agents accept an optional `llm` parameter for LLM-guided generation.

---

## 🖥️ CLI Reference

```
python scripts/generate_demo.py [OPTIONS]

Options:
  --genre         Genre preset (classic_rock, blues, pop, folk, country, punk, hard_rock)
  --key           Root note (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
  --mode          Scale mode (major, minor, dorian, mixolydian, phrygian, lydian, locrian)
  --tempo         BPM — 40 to 300 (default: 120)
  --output        Output directory (default: ./output)
  --sections      Number of song sections (default: 4)
  --render-audio  Render WAV via audio backend
  --backend       Audio backend: export | fluidsynth | timidity (default: export)
  --with-keys     Include keyboard in the band
  -v, --verbose   Enable debug logging
```

---

## 🛠️ MCP Server

The MCP server exposes backing-track generation as tools for AI coding assistants (GitHub Copilot, Claude Code, etc.).

```bash
# Install with MCP support (included in core)
pip install -e "."

# Run the MCP server (stdio transport)
audio-engineer-mcp
# or: python -m audio_engineer.mcp_server
```

### Available MCP Tools

| Tool | Description |
| ---- | ----------- |
| `generate_track` | Generate a full MIDI backing track (genre, key, tempo, instruments, sections) |
| `generate_game_music` | Quick game music via mood preset (battle, exploration, town, boss, …) |
| `generate_audio_track` | Route a track request through the provider registry (MIDI or Gemini Lyria) |
| `list_genres` | List all supported genre presets |
| `list_game_moods` | List all game music mood presets with descriptions |
| `list_providers` | List registered audio providers with capabilities and availability |

Set `AUDIO_ENGINEER_OUTPUT` to control where the MCP server writes files.  
See the **[MCP Server guide](https://ianlintner.github.io/audio_engineer/mcp-server/)** for full details.

---

## 🔌 Multi-Provider System

The `ProviderRegistry` routes generation requests to the best available backend:

1. **`MidiProvider`** — algorithmic MIDI generation (always available, zero dependencies)
2. **`GeminiLyriaProvider`** — full-length audio via Google Lyria 3 (requires `pip install -e ".[gemini]"` and `AUDIO_ENGINEER_GEMINI_API_KEY`)

Custom providers can be registered at runtime:

```python
from audio_engineer.providers import ProviderRegistry, AudioProvider, ProviderCapability

registry = ProviderRegistry()
registry.register(my_custom_provider)
```

See the **[Providers guide](https://ianlintner.github.io/audio_engineer/providers/)** for details.

---

## 🤖 Google Gemini Integration

The `audio_engineer.gemini` package wraps the Google GenAI SDK for three capabilities:

| Agent | Class | What it does |
| ----- | ----- | ------------ |
| Music generation | `MusicGenerationAgent` | Full songs or 30 s clips via Lyria 3 (clip or pro model) |
| Audio analysis | `AudioAnalysisAgent` | Transcription, genre/mood detection, audio Q&A |
| Text-to-speech | `TTSAgent` | Narration and vocal scratch tracks |

```bash
pip install -e ".[gemini]"
export AUDIO_ENGINEER_GEMINI_API_KEY=your_key_here
```

See the **[Gemini guide](https://ianlintner.github.io/audio_engineer/gemini/)** for usage examples.

---



Start the dev server: `python scripts/run_dev.py` (requires `pip install -e ".[api]"`)

| Method | Path                        | Description                              |
| ------ | --------------------------- | ---------------------------------------- |
| `POST` | `/sessions`                 | Create a new session                     |
| `POST` | `/sessions/{id}/run`        | Run the session (trigger generation)     |
| `GET`  | `/sessions/{id}`            | Get session status and output file paths |
| `GET`  | `/sessions/{id}/tracks`     | List generated tracks                    |
| `GET`  | `/sessions/{id}/export`     | Download the combined MIDI file          |

Interactive API docs: `http://localhost:8000/docs`

---

## ⚙️ Configuration

All settings use the `AUDIO_ENGINEER_` environment variable prefix (or a `.env` file in the project root).

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_OUTPUT_DIR` | Directory for generated files | `./output` |
| `AUDIO_ENGINEER_LOG_LEVEL` | Logging verbosity | `INFO` |
| `AUDIO_ENGINEER_OPENAI_API_KEY` | OpenAI key for LLM agents | _(unset)_ |
| `AUDIO_ENGINEER_ANTHROPIC_API_KEY` | Anthropic key for LLM agents | _(unset)_ |
| `AUDIO_ENGINEER_GEMINI_API_KEY` | Google Gemini API key (Lyria 3 / audio analysis) | _(unset)_ |
| `AUDIO_ENGINEER_LLM_PROVIDER` | Active LLM backend: `openai`, `anthropic`, `gemini` | `openai` |
| `AUDIO_ENGINEER_DEFAULT_AUDIO_PROVIDER` | Default audio generation provider | `midi_engine` |
| `AUDIO_ENGINEER_SOUNDFONT_PATH` | Path to a `.sf2` SoundFont for FluidSynth rendering | _(unset)_ |
| `AUDIO_ENGINEER_HOST` | FastAPI server host | `0.0.0.0` |
| `AUDIO_ENGINEER_PORT` | FastAPI server port | `8000` |

---

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/ scripts/

# Run a quick smoke test
python scripts/generate_demo.py --genre blues --key A --mode minor -v
```

---

## 📁 Project Structure

```
src/audio_engineer/
├── agents/
│   ├── base.py              # BaseMusician, BaseEngineer, SessionContext
│   ├── orchestrator.py      # SessionOrchestrator
│   ├── musician/            # DrummerAgent, BassistAgent, GuitaristAgent, KeyboardistAgent
│   └── engineer/            # MixerAgent, MasteringAgent
├── core/
│   ├── models.py            # Pydantic models (Session, MidiTrackData, etc.)
│   ├── music_theory.py      # Scales, chords, progressions
│   ├── midi_engine.py       # MIDI file construction
│   ├── patterns.py          # Genre-specific pattern library
│   ├── rhythm.py            # Rhythmic utilities
│   ├── audio_track.py       # AudioTrack model for provider results
│   ├── track_composer.py    # Higher-level track composition helpers
│   └── constants.py         # TICKS_PER_BEAT, MIDI note maps, etc.
├── providers/               # Multi-provider audio generation system
│   ├── base.py              # AudioProvider ABC, TrackRequest/Result, ProviderCapability
│   ├── registry.py          # ProviderRegistry with capability-based routing
│   ├── midi_provider.py     # MidiProvider (algorithmic, zero-dependency)
│   └── gemini_provider.py   # GeminiLyriaProvider (Lyria 3 audio generation)
├── gemini/                  # Google Gemini AI integration
│   ├── client.py            # GeminiClient singleton wrapper
│   ├── music_gen.py         # MusicGenerationAgent (Lyria 3 clip & pro)
│   ├── audio_analysis.py    # AudioAnalysisAgent
│   └── tts.py               # TTSAgent (text-to-speech)
├── daw/                     # Audio backends (FluidSynth, TiMidity, GarageBand, Logic Pro)
├── api/                     # FastAPI application and route handlers
├── ui/                      # Static web interface (served by the API)
├── mcp_server.py            # MCP server entry point (audio-engineer-mcp)
└── config/                  # Settings and logging configuration
```

---

## 📖 Documentation

Full documentation is published at **[https://ianlintner.github.io/audio_engineer/](https://ianlintner.github.io/audio_engineer/)**.

Topics include:

- [Installation & Setup](https://ianlintner.github.io/audio_engineer/installation/)
- [Quick Start Guide](https://ianlintner.github.io/audio_engineer/quickstart/)
- [CLI Reference](https://ianlintner.github.io/audio_engineer/cli/)
- [REST API Reference](https://ianlintner.github.io/audio_engineer/api/)
- [MCP Server](https://ianlintner.github.io/audio_engineer/mcp-server/)
- [Multi-Provider System](https://ianlintner.github.io/audio_engineer/providers/)
- [Gemini Integration](https://ianlintner.github.io/audio_engineer/gemini/)
- [Architecture](https://ianlintner.github.io/audio_engineer/architecture/)
- [Agent Guide](https://ianlintner.github.io/audio_engineer/agents/)
- [Music Theory Internals](https://ianlintner.github.io/audio_engineer/music-theory/)
- [DAW Integration](https://ianlintner.github.io/audio_engineer/daw-integration/)
- [Contributing](https://ianlintner.github.io/audio_engineer/contributing/)

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key rules:
- Keep orchestration order stable: drums → bass → guitar → keys
- Prefer deterministic defaults; isolate randomness behind explicit seeds
- Add or update tests for non-trivial behavior changes
- Keep PRs focused — no unrelated refactors

---

## 📄 License

[MIT](LICENSE)
