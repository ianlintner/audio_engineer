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
- **What it does:** wraps the existing `SessionOrchestrator` to generate algorithmic MIDI using the full agent pipeline

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
