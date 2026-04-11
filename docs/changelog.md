# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- MkDocs + Material documentation site with full architecture, agent, music theory, DAW integration, and CLI reference docs
- GitHub Actions workflow for automatic docs deployment to GitHub Pages
- `docs` extras group in `pyproject.toml`
- **Multi-provider system** — `AudioProvider` ABC, `ProviderRegistry` with capability-based routing, `MidiProvider` (algorithmic), and `GeminiLyriaProvider` (Lyria 3 audio)
- **Google Gemini integration** — `GeminiClient`, `MusicGenerationAgent` (Lyria 3 clip and pro models), `AudioAnalysisAgent`, and `TTSAgent`
- **MCP server** (`audio-engineer-mcp`) — exposes `generate_track`, `generate_game_music`, `generate_audio_track`, `list_providers`, `list_genres`, and `list_game_moods` as MCP tools for AI coding assistants
- **Web UI** — lightweight browser-based interface (`src/audio_engineer/ui/static/index.html`) served alongside the REST API
- `gemini` extras group in `pyproject.toml` (`google-genai>=1.70`)
- `audio` extras group in `pyproject.toml` (`pydub>=0.25`)
- `AudioTrack` model (`core/audio_track.py`) — unified container for provider-generated audio data
- `TrackComposer` helpers (`core/track_composer.py`) — higher-level track composition utilities
- `scripts/generate_thrash.py` — thrash metal stress-test script (200 BPM, E minor)
- `scripts/setup_soundfont.py` — automated SoundFont download and configuration helper
- Game music mood presets for MCP: battle, exploration, mystery, town, boss, peaceful, victory, sad, dungeon, chase, stealth, menu

### Changed
- All configuration environment variables now require the `AUDIO_ENGINEER_` prefix (e.g. `AUDIO_ENGINEER_OUTPUT_DIR`, `AUDIO_ENGINEER_GEMINI_API_KEY`)
- `SessionOrchestrator` exposes a `provider_registry` attribute for runtime provider management

---

## [0.1.0] — 2026-04-05

### Added
- `SessionOrchestrator` — coordinates sequential multi-agent generation
- `DrummerAgent` — genre-aware kick, snare, and hi-hat patterns
- `BassistAgent` — root-note bass lines locked to drums and chord changes
- `GuitaristAgent` — rhythm guitar with power chord and strum patterns
- `KeyboardistAgent` — chord pads and voicings (opt-in via `--with-keys`)
- `MixerAgent` — per-track volume, pan, and EQ metadata
- `MasteringAgent` — final loudness and session metadata
- `MidiEngine` — MIDI file construction built on `mido`
- `MusicTheory` helpers — scales, chord progressions, voicings for 7 modes
- Pattern library — genre presets for classic rock, blues, pop, folk, country, punk, hard rock
- FluidSynth, TiMidity, GarageBand, and Logic Pro DAW backends
- FastAPI REST API with session create/run/status/export endpoints
- MCP server entry point (`audio-engineer-mcp`)
- CLI demo script (`scripts/generate_demo.py`)
- Full test suite across agents, core, API, and DAW layers

[Unreleased]: https://github.com/ianlintner/audio_engineer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ianlintner/audio_engineer/releases/tag/v0.1.0
