# Configuration

AI Music Studio is configured via environment variables or a `.env` file in the project root. All variables use the `AUDIO_ENGINEER_` prefix (handled by `pydantic-settings`).

---

## Core Settings

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_OUTPUT_DIR` | Directory where MIDI and audio files are written | `./output` |
| `AUDIO_ENGINEER_LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## LLM Providers

Set these when using `--llm` modes or the LLM-guided agents:

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_OPENAI_API_KEY` | OpenAI API key for GPT-4o and related models | _(unset)_ |
| `AUDIO_ENGINEER_ANTHROPIC_API_KEY` | Anthropic API key for Claude models | _(unset)_ |
| `AUDIO_ENGINEER_GEMINI_API_KEY` | Google Gemini API key (Lyria 3, audio analysis, TTS) | _(unset)_ |
| `AUDIO_ENGINEER_LLM_PROVIDER` | Active LLM backend: `openai`, `anthropic`, or `gemini` | `openai` |
| `AUDIO_ENGINEER_LLM_MODEL` | Model name for the active LLM provider | `gpt-4o-mini` |
| `AUDIO_ENGINEER_GEMINI_MODEL` | Gemini model for reasoning (not music generation) | `gemini-2.5-flash` |

---

## Audio Providers

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_DEFAULT_AUDIO_PROVIDER` | Default provider for audio generation | `midi_engine` |
| `AUDIO_ENGINEER_DEFAULT_MIDI_PROVIDER` | Default provider for MIDI generation | `midi_engine` |
| `AUDIO_ENGINEER_ENABLE_GEMINI_PROVIDER` | Register `GeminiLyriaProvider` at startup | `true` |

---

## Audio Backends

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_SOUNDFONT_PATH` | Absolute path to a `.sf2` SoundFont file for FluidSynth rendering | _(none)_ |
| `AUDIO_ENGINEER_TIMIDITY_CFG` | Path to a custom TiMidity configuration file | _(system default)_ |
| `AUDIO_ENGINEER_DEFAULT_SAMPLE_RATE` | Sample rate for audio rendering (Hz) | `44100` |
| `AUDIO_ENGINEER_AUDIO_FORMAT` | Output audio format: `wav` or `mp3` | `wav` |
| `AUDIO_ENGINEER_MP3_BITRATE` | MP3 encoding bitrate | `192k` |
| `AUDIO_ENGINEER_PREFERRED_BACKEND` | Preferred DAW backend: `fluidsynth`, `timidity`, or `export` | `fluidsynth` |

---

## API Server

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_HOST` | Host to bind the FastAPI server | `0.0.0.0` |
| `AUDIO_ENGINEER_PORT` | Port for the FastAPI server | `8000` |
| `AUDIO_ENGINEER_DEBUG` | Enable Uvicorn debug / hot-reload (development only) | `false` |

---

## MCP Server

The MCP server reads one additional environment variable that is **not** processed by `pydantic-settings`:

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_OUTPUT` | Output directory used by the MCP server | auto-detected project root `output/` |

---

## Example `.env` File

```dotenv
AUDIO_ENGINEER_OUTPUT_DIR=./output
AUDIO_ENGINEER_LOG_LEVEL=INFO

# LLM (optional — pick one or more)
AUDIO_ENGINEER_LLM_PROVIDER=openai
AUDIO_ENGINEER_OPENAI_API_KEY=sk-...
AUDIO_ENGINEER_ANTHROPIC_API_KEY=sk-ant-...
AUDIO_ENGINEER_GEMINI_API_KEY=AIza...

# Audio generation provider
AUDIO_ENGINEER_DEFAULT_AUDIO_PROVIDER=midi_engine

# Audio rendering (optional)
AUDIO_ENGINEER_SOUNDFONT_PATH=/usr/share/sounds/sf2/FluidR3_GM.sf2

# API server
AUDIO_ENGINEER_HOST=127.0.0.1
AUDIO_ENGINEER_PORT=8000
```

Place this file in the project root. Settings are loaded from `src/audio_engineer/config/settings.py` using `pydantic-settings`.
