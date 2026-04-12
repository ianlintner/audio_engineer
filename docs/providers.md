# Multi-Provider System

AI Music Studio uses a pluggable provider architecture so that different audio generation backends can be swapped or combined without changing the rest of the codebase.

---

## Overview

The `audio_engineer.providers` package defines:

| Class | Role |
| ----- | ---- |
| `AudioProvider` | Abstract base class every backend must implement |
| `ProviderCapability` | Enum of capabilities a provider can declare |
| `TrackRequest` | Pydantic model describing a single track to generate |
| `TrackResult` | Pydantic model returned by every provider |
| `ProviderRegistry` | Manages registered providers and routes requests |
| `MidiProvider` | Built-in algorithmic MIDI backend (zero extra dependencies) |
| `LLMMidiProvider` | LLM-driven MIDI backend; falls back to `MidiProvider` on parse failure |
| `GeminiLyriaProvider` | Google Lyria 3 audio backend (requires `[gemini]` extra) |

---

## Provider Capabilities

`ProviderCapability` is a string enum. Declare which capabilities your provider supports by returning them from the `capabilities` property:

| Capability | Description |
| ---------- | ----------- |
| `midi_generation` | Produces `.mid` files |
| `audio_generation` | Produces rendered audio (WAV/MP3) |
| `vocals` | Can generate or synthesise vocals |
| `sound_design` | Sound effects and SFX |
| `audio_analysis` | Transcription, genre/mood detection |
| `source_separation` | Stem separation |
| `effects_processing` | DSP / FX chains |
| `text_to_speech` | Spoken narration |

---

## Built-in Providers

### `MidiProvider`

- **Name:** `midi_engine`
- **Capabilities:** `midi_generation`
- **Availability:** always available
- **What it does:** wraps the existing `SessionOrchestrator` to generate algorithmic MIDI using the full agent pipeline (22 genres, 26 instruments)

### `LLMMidiProvider`

- **Name:** `llm_midi`
- **Capabilities:** `midi_generation`
- **Availability:** when an LLM callable is injected
- **What it does:** constructs a structured prompt from the `TrackRequest` (genre, key, tempo, instrument, style hints) and asks the LLM to return a JSON array of `{pitch, velocity, start_beat, duration_beats}` objects. Falls back to `MidiProvider` if the response is unparseable.
- **Priority:** registered at highest priority in `ProviderRegistry` when configured; use `preferred_provider="llm_midi"` to force it.

```python
from audio_engineer.providers.llm_midi_provider import LLMMidiProvider
from audio_engineer.providers.base import TrackRequest

provider = LLMMidiProvider(llm=lambda prompt: openai_client.complete(prompt))

request = TrackRequest(
    track_name="jazz_piano",
    description="Comping jazz piano chords",
    instrument="keys",
    genre="jazz",
    tempo=140,
)
result = provider.generate_track(request)
# result.provider_used == "llm_midi"  or  "midi_engine_fallback" if LLM failed
```

`core/llm_prompts.py` provides the underlying helpers:

| Helper | Description |
| ------ | ----------- |
| `build_midi_prompt(request)` | Builds the canonical MIDI generation prompt including JSON schema |
| `parse_midi_json(text)` | Tolerant JSON parser — strips Markdown fences, returns `None` on failure |
| `validate_midi_events(events)` | Guards against out-of-range pitches/velocities and beat positions |
| `events_to_note_events(events, channel, ticks_per_beat, bar_offset_ticks)` | Converts validated dicts to `NoteEvent` objects |

### `GeminiLyriaProvider`

- **Name:** `gemini_lyria`
- **Capabilities:** `audio_generation`
- **Availability:** requires `AUDIO_ENGINEER_GEMINI_API_KEY` and `pip install -e ".[gemini]"`
- **What it does:** calls Google Lyria 3 to produce full-length AI-generated audio

---

## ProviderRegistry

`ProviderRegistry` manages a collection of providers and selects the best one for each request.

### Routing Priority

1. If `TrackRequest.preferred_provider` is set and available, use it.
2. If `TrackRequest.required_capabilities` are set, find the first available provider that supports all of them.
3. Fall back to the first available provider.

### API

```python
from audio_engineer.providers import ProviderRegistry, MidiProvider

registry = ProviderRegistry()
registry.register(MidiProvider())

# List all registered providers
print(registry.list_providers())    # ['midi_engine']
print(registry.list_available())    # ['midi_engine']

# Find providers by capability
from audio_engineer.providers import ProviderCapability
midi_providers = registry.find_by_capability(ProviderCapability.MIDI_GENERATION)

# Generate a track
from audio_engineer.providers import TrackRequest
request = TrackRequest(
    track_name="rhythm_guitar",
    description="Driving rhythm guitar for a blues track",
    genre="blues",
    key="A",
    tempo=100,
    required_capabilities=[ProviderCapability.MIDI_GENERATION],
)
result = registry.generate(request)
print(result.success, result.provider_used, result.track)
```

---

## Writing a Custom Provider

Subclass `AudioProvider` and implement the four required methods:

```python
from audio_engineer.providers.base import AudioProvider, ProviderCapability, TrackRequest, TrackResult

class MyCustomProvider(AudioProvider):
    @property
    def name(self) -> str:
        return "my_provider"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.AUDIO_GENERATION]

    def is_available(self) -> bool:
        # Return False if required credentials/packages are missing
        return True

    def generate_track(self, request: TrackRequest) -> TrackResult:
        # ... your generation logic ...
        return TrackResult(success=True, provider_used=self.name, track=audio_track)
```

Then register it:

```python
from audio_engineer.providers import ProviderRegistry

registry = ProviderRegistry()
registry.register(MyCustomProvider())
```

You can also inject a registry into `SessionOrchestrator`:

```python
from audio_engineer.agents.orchestrator import SessionOrchestrator

orchestrator = SessionOrchestrator(output_dir="./output")
orchestrator.provider_registry.register(MyCustomProvider())
```

---

## Configuration

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_DEFAULT_AUDIO_PROVIDER` | Provider used when no preference is specified | `midi_engine` |
| `AUDIO_ENGINEER_DEFAULT_MIDI_PROVIDER` | Provider used for MIDI-specific requests | `midi_engine` |
| `AUDIO_ENGINEER_ENABLE_GEMINI_PROVIDER` | Auto-register `GeminiLyriaProvider` on startup | `true` |

See [Configuration](configuration.md) for the full settings reference.
