# Gemini Integration

AI Music Studio integrates with [Google GenAI](https://ai.google.dev/) to provide three AI-powered audio capabilities via the `audio_engineer.gemini` package.

---

## Installation

```bash
pip install -e ".[gemini]"
```

Set your API key:

```bash
export AUDIO_ENGINEER_GEMINI_API_KEY=AIza...
```

Or add it to your `.env` file:

```dotenv
AUDIO_ENGINEER_GEMINI_API_KEY=AIza...
```

---

## Agents

### `MusicGenerationAgent` — Google Lyria 3

Generates full-length music using Google's [Lyria 3](https://deepmind.google/technologies/lyria/) models.

Two model tiers are available:

| Model | Constant | Best for |
| ----- | -------- | -------- |
| `lyria-3-clip-preview` | `LYRIA_CLIP_MODEL` | 30-second clips, fast iteration |
| `lyria-3-pro-preview` | `LYRIA_PRO_MODEL` | Full-length songs with structure |

#### Generate a 30-second clip

```python
from audio_engineer.gemini import MusicGenerationAgent

agent = MusicGenerationAgent()
result = agent.generate_clip(
    "Upbeat blues guitar riff in A minor, 100 BPM",
    instrumental=True,
)
result.save("output/my_clip.wav")
print(result.mime_type, len(result.audio_data))
```

#### Generate a full song

```python
result = agent.generate_song(
    "Classic rock anthem in E minor, driving drums and guitar, 130 BPM",
    instrumental=True,
)
result.save("output/my_song.wav")
```

#### `MusicGenResult`

| Attribute | Type | Description |
| --------- | ---- | ----------- |
| `audio_data` | `bytes` | Raw audio bytes |
| `mime_type` | `str` | MIME type (e.g. `audio/wav`) |
| `lyrics` | `str \| None` | Generated lyrics, if any |
| `.save(path)` | method | Write to disk and return the `Path` |

---

### `AudioAnalysisAgent`

Analyse existing audio files using Gemini's multimodal capabilities.

```python
from audio_engineer.gemini import AudioAnalysisAgent

agent = AudioAnalysisAgent()

# Transcribe audio
transcript = agent.transcribe("output/my_song.wav")

# Detect genre and mood
info = agent.detect_genre_mood("output/my_song.wav")
print(info)  # {'genre': 'blues', 'mood': 'melancholic', ...}

# Ask a free-form question about the audio
answer = agent.ask("output/my_song.wav", "What instruments can you hear?")
```

---

### `TTSAgent`

Generate spoken narration or vocal scratch tracks.

```python
from audio_engineer.gemini import TTSAgent

agent = TTSAgent()
audio_bytes = agent.synthesise("Intro riff — four bars of E minor blues")
with open("output/narration.wav", "wb") as f:
    f.write(audio_bytes)
```

---

## GeminiClient

All three agents share a singleton `GeminiClient`. You can access it directly for advanced use cases:

```python
from audio_engineer.gemini import get_gemini_client

client = get_gemini_client()
raw = client.raw          # google.genai.Client
types = client.types      # google.genai.types
```

Pass a custom client to any agent:

```python
from audio_engineer.gemini import GeminiClient, MusicGenerationAgent

client = GeminiClient(api_key="AIza...")
agent = MusicGenerationAgent(client=client)
```

---

## Provider Integration

`GeminiLyriaProvider` wraps `MusicGenerationAgent` as a pluggable `AudioProvider` so it can be used through the standard `ProviderRegistry`:

```python
from audio_engineer.providers import ProviderRegistry, TrackRequest, ProviderCapability
from audio_engineer.providers.gemini_provider import GeminiLyriaProvider

registry = ProviderRegistry()
registry.register(GeminiLyriaProvider())

request = TrackRequest(
    track_name="main_theme",
    description="Epic orchestral battle theme",
    duration_seconds=60,
    required_capabilities=[ProviderCapability.AUDIO_GENERATION],
)
result = registry.generate(request)
```

See [Multi-Provider System](providers.md) for full details on the provider registry.

---

## Configuration

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_GEMINI_API_KEY` | Google Gemini API key | _(required)_ |
| `AUDIO_ENGINEER_GEMINI_MODEL` | Gemini model for LLM reasoning | `gemini-2.5-flash` |
| `AUDIO_ENGINEER_ENABLE_GEMINI_PROVIDER` | Auto-register `GeminiLyriaProvider` at startup | `true` |

See [Configuration](configuration.md) for the complete settings reference.
