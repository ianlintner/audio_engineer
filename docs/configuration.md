# Configuration

AI Music Studio is configured via environment variables (or a `.env` file if you use `python-dotenv`).

---

## Core Settings

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `OUTPUT_DIR` | Directory where MIDI and audio files are written | `./output` |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## LLM Providers

Set these when using `--llm` modes or the LLM-guided agents:

| Variable | Description |
| -------- | ----------- |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o and related models |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models |
| `OPENAI_MODEL` | Override the default OpenAI model name (default: `gpt-4o`) |
| `ANTHROPIC_MODEL` | Override the default Anthropic model name |

---

## Audio Backends

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `SOUNDFONT_PATH` | Absolute path to a `.sf2` SoundFont file for FluidSynth rendering | _(none)_ |
| `TIMIDITY_CFG` | Path to a custom TiMidity configuration file | _(system default)_ |

---

## API Server

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `API_HOST` | Host to bind the FastAPI server | `0.0.0.0` |
| `API_PORT` | Port for the FastAPI server | `8000` |
| `API_RELOAD` | Enable Uvicorn hot-reload (development only) | `false` |

---

## Example `.env` File

```dotenv
OUTPUT_DIR=./output
LOG_LEVEL=INFO

# LLM (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Audio (optional)
SOUNDFONT_PATH=/usr/share/sounds/sf2/FluidR3_GM.sf2

# API server
API_HOST=127.0.0.1
API_PORT=8000
```

Place this file in the project root. Settings are loaded from `src/audio_engineer/config/settings.py` using `pydantic-settings`.
