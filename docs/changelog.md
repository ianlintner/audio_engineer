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
- **Complete GM Program map** — all 128 GM instrument programs in `GM_PROGRAMS` (was ~40)
- **Full GM Drum Map** — all 47 standard GM percussion sounds in `GM_DRUMS` (congas, bongos, timbales, cowbell, tambourine, triangles, cuica, guiro, maracas, etc.)
- **Expanded scale library** — 13 new modes: harmonic minor, melodic minor, lydian, phrygian, locrian, whole-tone, diminished, augmented, chromatic, bebop dominant, bebop major, Spanish phrygian, Hungarian minor
- **Expanded chord library** — 22 new chord types: 9th / maj9 / min9, dom11 / maj11 / min11, dom13 / maj13 / min13, sharp9, alt, half-dim (ø7), quartal, 6th, min6, 6/9
- **15 new genres** — `Genre` enum extended to 22: Jazz, Funk, Reggae, Soul, R&B, Metal, Hip-Hop, Latin, Bossa Nova, Electronic, House, Ambient, Gospel, Swing, Bebop
- **20 new instruments** — `Instrument` enum extended to 26: lead guitar, strings, brass, woodwinds, saxophone, trumpet, violin, synthesizer, pad, organ, vibraphone, marimba, percussion, conga, bongo, djembe, sitar, banjo, ukulele, mandolin
- **11 new modes** — `Mode` enum extended with: `HARMONIC_MINOR`, `MELODIC_MINOR`, `LYDIAN`, `PHRYGIAN`, `LOCRIAN`, `WHOLE_TONE`, `DIMINISHED`, `BEBOP_DOMINANT`, `BEBOP_MAJOR`, `SPANISH_PHRYGIAN`, `HUNGARIAN_MINOR`
- **40 PAS Standard Drum Rudiments** — `DrumRudiment` class encoding all 40 rudiments as `NoteEvent` sequences (rolls, diddles, flams, drags) in `core/patterns.py`
- **40+ new drum patterns** — genre patterns for Jazz, Funk, Reggae, Soul/R&B, Metal, Hip-Hop, Latin, Electronic, Gospel, Ambient, Bebop, Swing (jazz ride, metal blast beat, reggae one-drop, trap hi-hat, samba surdo, clave son, 4-on-the-floor EDM, D'n'B amen break, etc.)
- **`BassPattern` class** — 8 genre-specific bass patterns: jazz walking, funk slap, reggae skank, R&B two-feel, pop root-fifth, Latin tumbao, Motown, country boom-chick
- **`MelodicPattern` class** — 10 patterns: jazz chord shells, guitar arpeggios, Travis picking, bossa nova comp, funk rhythm 16ths, stride keys, jazz two-handed keys, synth arp
- **10 new `ProgressionFactory` methods** — `jazz_ii_V_I`, `jazz_turnaround`, `jazz_rhythm_changes`, `blues_jazz`, `modal_dorian`, `bossa_nova`, `minor_i_VII_VI_VII`, `gospel_I_IV_I_V`, `metal_power_I_VII_VI`, `funk_I7_IV7`
- **`StringsAgent`** (`agents/musician/strings.py`) — legato lines, pizzicato (low intensity), tremolo (high intensity) for strings/violin
- **`BrassAgent`** (`agents/musician/brass.py`) — stab chords, long tones, fall-offs for brass/trumpet/saxophone
- **`SynthAgent`** (`agents/musician/synth.py`) — sustained pads and 16th-note arpeggio patterns for synthesizer/pad instruments
- **`PercussionAgent`** (`agents/musician/percussion.py`) — Latin/Afro-Cuban hand drum patterns for conga, bongo, djembe on MIDI channel 9
- **`LeadGuitarAgent`** (`agents/musician/lead_guitar.py`) — pentatonic licks, scale runs, and fills over chord changes
- **`LLMMidiProvider`** (`providers/llm_midi_provider.py`) — LLM-driven MIDI generation; accepts any `Callable[[str], str]`; falls back to `MidiProvider` on JSON parse failure
- **LLM prompt helpers** (`core/llm_prompts.py`) — `build_midi_prompt`, `parse_midi_json` (strips Markdown fences), `validate_midi_events`, `events_to_note_events`
- `LLMMidiProvider` registered at highest priority in `ProviderRegistry` when an LLM callable is configured
- Orchestration order extended to: drums → bass → guitar → lead guitar → keys → strings → brass → synth → percussion

### Changed
- All configuration environment variables now require the `AUDIO_ENGINEER_` prefix (e.g. `AUDIO_ENGINEER_OUTPUT_DIR`, `AUDIO_ENGINEER_GEMINI_API_KEY`)
- `SessionOrchestrator` exposes a `provider_registry` attribute for runtime provider management
- `_INSTRUMENT_AGENTS` in `midi_provider.py` now maps all 26 `Instrument` values; unmapped instruments fall back to `KeyboardistAgent`
- `MidiProvider._get_progressions` handles all 22 `Genre` values

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
