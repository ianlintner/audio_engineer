# AI Music Studio

A multi-agent system for generating MIDI backing tracks. AI musician and engineer agents collaborate to produce complete songs with drums, bass, guitar, and keys.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Generate a demo backing track
python scripts/generate_demo.py --genre classic_rock --key E --mode minor --tempo 120 -v

# With keyboard
python scripts/generate_demo.py --genre pop --key C --mode major --with-keys

# Start the API server (requires [api] extras)
pip install -e ".[api]"
python scripts/run_dev.py
```

## Architecture

```
SessionOrchestrator
├── DrummerAgent      → drum pattern generation
├── BassistAgent      → bass line locked to drums + chords
├── GuitaristAgent    → rhythm/lead guitar parts
├── KeyboardistAgent  → chord voicings and pads
├── MixerAgent        → volume, pan, EQ per track
└── MasteringAgent    → final loudness and metadata
```

Tracks are generated sequentially — drums first, then bass, guitar, and keys — so each agent can react to what came before. The orchestrator manages chord progressions per section and exports combined + individual MIDI files.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details.

## Agents

| Agent              | Role                                         | Output          |
| ------------------ | -------------------------------------------- | --------------- |
| `DrummerAgent`     | Kick, snare, hi-hat patterns per section     | `MidiTrackData` |
| `BassistAgent`     | Root-note bass lines following chord changes | `MidiTrackData` |
| `GuitaristAgent`   | Rhythm guitar / power chords                 | `MidiTrackData` |
| `KeyboardistAgent` | Chord pads and voicings                      | `MidiTrackData` |
| `MixerAgent`       | Per-track volume, pan, EQ                    | `MixConfig`     |
| `MasteringAgent`   | Final processing metadata                    | `dict`          |

All agents accept an optional `llm` parameter for LLM-guided generation.

## CLI Usage

```
python scripts/generate_demo.py [OPTIONS]

Options:
  --genre         Genre (classic_rock, blues, pop, folk, country, punk, hard_rock)
  --key           Root note (C, C#, D, ..., B)
  --mode          Scale mode (major, minor, dorian, mixolydian, etc.)
  --tempo         BPM (40-300, default: 120)
  --output        Output directory (default: ./output)
  --render-audio  Render WAV via audio backend
  --backend       Audio backend (export, fluidsynth, timidity)
  --with-keys     Include keyboard in the band
  -v, --verbose   Debug logging
```

## API Endpoints

When running the dev server (`python scripts/run_dev.py`):

| Method | Path                 | Description                  |
| ------ | -------------------- | ---------------------------- |
| `POST` | `/sessions`          | Create a new session         |
| `POST` | `/sessions/{id}/run` | Run the session              |
| `GET`  | `/sessions/{id}`     | Get session status and files |

## Configuration

| Variable     | Description                   | Default    |
| ------------ | ----------------------------- | ---------- |
| `OUTPUT_DIR` | Directory for generated files | `./output` |
| `LOG_LEVEL`  | Logging level                 | `INFO`     |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Run a quick smoke test
python scripts/generate_demo.py --genre blues --key A --mode minor -v
```

## Project Structure

```
src/audio_engineer/
├── agents/
│   ├── base.py              # BaseMusician, BaseEngineer, SessionContext
│   ├── orchestrator.py      # SessionOrchestrator
│   ├── musician/             # DrummerAgent, BassistAgent, etc.
│   └── engineer/             # MixerAgent, MasteringAgent
├── core/
│   ├── models.py             # Pydantic models (Session, MidiTrackData, etc.)
│   ├── music_theory.py       # Scales, chords, progressions
│   ├── midi_engine.py        # MIDI file construction
│   └── constants.py          # TICKS_PER_BEAT, etc.
├── daw/                      # Audio backends (FluidSynth, TiMidity, etc.)
└── config/                   # Settings and logging
```
