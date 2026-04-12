# Quick Start

This guide walks you through generating your first backing track in under five minutes.

---

## 1. Install

```bash
git clone https://github.com/ianlintner/audio_engineer.git
cd audio_engineer
pip install -e ".[dev]"
```

---

## 2. Generate a Backing Track

Run the demo script with a genre, key, and mode:

```bash
python scripts/generate_demo.py \
  --genre classic_rock \
  --key E \
  --mode minor \
  --tempo 120 \
  -v
```

Output files appear in `./output/`:

```
output/
├── <session-id>_drums.mid
├── <session-id>_bass.mid
├── <session-id>_guitar.mid
└── <session-id>_full.mid   ← combined multi-track MIDI
```

---

## 3. Try Different Genres

```bash
# Blues in A minor
python scripts/generate_demo.py --genre blues --key A --mode minor -v

# Pop with keyboard
python scripts/generate_demo.py --genre pop --key C --mode major --with-keys

# Hard rock in D minor
python scripts/generate_demo.py --genre hard_rock --key D --mode minor --tempo 140 -v

# Folk in G major
python scripts/generate_demo.py --genre folk --key G --mode major --tempo 90

# Jazz in C with full band
python scripts/generate_demo.py --genre jazz --key C --mode dorian --with-keys -v

# Funk in E minor at 105 BPM
python scripts/generate_demo.py --genre funk --key E --mode minor --tempo 105

# Metal in E minor at 200 BPM
python scripts/generate_demo.py --genre metal --key E --mode minor --tempo 200 -v

# Latin in A minor
python scripts/generate_demo.py --genre latin --key A --mode minor -v

# Hip-hop in C minor at 90 BPM
python scripts/generate_demo.py --genre hip_hop --key C --mode minor --tempo 90
```

All supported genres: `classic_rock`, `blues`, `pop`, `folk`, `country`, `punk`, `hard_rock`, `jazz`, `funk`, `reggae`, `soul`, `rnb`, `metal`, `hip_hop`, `latin`, `bossa_nova`, `electronic`, `house`, `ambient`, `gospel`, `swing`, `bebop`.

---

## 4. Render to Audio (optional)

Requires FluidSynth installed and a SoundFont — see [Installation](installation.md#audio-rendering-optional).

```bash
export SOUNDFONT_PATH=/path/to/soundfont.sf2

python scripts/generate_demo.py \
  --genre blues \
  --key A \
  --mode minor \
  --render-audio \
  --backend fluidsynth \
  -v
```

This produces a `.wav` file alongside the MIDI files.

---

## 5. Use the REST API

```bash
# Install API extras
pip install -e ".[api]"

# Start the server
python scripts/run_dev.py
```

Then in a separate terminal:

```bash
# Create a session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"genre": "classic_rock", "key": "E", "mode": "minor", "tempo": 120}'

# Run the session (replace <id> with the session ID returned above)
curl -X POST http://localhost:8000/sessions/<id>/run

# Check status
curl http://localhost:8000/sessions/<id>
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 6. LLM-Driven MIDI Generation (optional)

When you have an LLM API key, `LLMMidiProvider` will generate MIDI directly from natural language prompts and fall back to the algorithmic engine if the LLM response is unparseable.

```python
import os
from audio_engineer.providers.llm_midi_provider import LLMMidiProvider
from audio_engineer.providers.base import TrackRequest
import openai

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def call_llm(prompt: str) -> str:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content

provider = LLMMidiProvider(llm=call_llm)

result = provider.generate_track(TrackRequest(
    track_name="jazz_piano",
    description="Jazz piano comping",
    genre="jazz",
    instrument="keys",
    tempo=130,
))
print(result.success, result.provider_used)
```

---

## 7. Use the REST API

```bash
# Install API extras
pip install -e ".[api]"

# Start the server
python scripts/run_dev.py
```

Then in a separate terminal:

```bash
# Create a session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"genre": "classic_rock", "key": "E", "mode": "minor", "tempo": 120}'

# Run the session (replace <id> with the session ID returned above)
curl -X POST http://localhost:8000/sessions/<id>/run

# Check status
curl http://localhost:8000/sessions/<id>
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 8. Next Steps

- [CLI Reference](cli.md) — all command-line flags
- [REST API](api.md) — full endpoint documentation
- [Architecture](architecture.md) — how the agents work together
- [Agents](agents.md) — customizing individual musician agents
- [Music Theory](music-theory.md) — scales, chords, patterns, rudiments
- [Providers](providers.md) — LLMMidiProvider, MidiProvider, Gemini
