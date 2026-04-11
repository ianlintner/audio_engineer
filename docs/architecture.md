# Architecture

## System Overview

AI Music Studio is a multi-agent system that generates MIDI backing tracks by simulating a session band. LLM-powered musician agents collaborate under a session orchestrator to produce genre-appropriate parts, which are then processed by audio engineering agents for mixing and mastering.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Tool]
        API_CLIENT[REST Client / curl]
    end

    subgraph "API Layer"
        API[FastAPI REST API]
    end

    subgraph "Orchestration Layer"
        SO[SessionOrchestrator]
        SC[SessionContext]
    end

    subgraph "Musician Agents"
        DR[DrummerAgent]
        BA[BassistAgent]
        GU[GuitaristAgent]
        KY[KeyboardistAgent]
    end

    subgraph "Engineering Agents"
        MX[MixerAgent]
        MA[MasteringAgent]
    end

    subgraph "Core Engine"
        ME[MidiEngine]
        MT[MusicTheory]
        DM[Pydantic Models]
        PR[Pattern Library]
    end

    subgraph "DAW Integration"
        T1[FluidSynth / TiMidity]
        T2[GarageBand / Logic Pro]
        T3[MIDI / WAV Export]
    end

    subgraph "LLM Layer"
        LLM[OpenAI / Anthropic / Local]
    end

    CLI --> SO
    API_CLIENT --> API
    API --> SO
    SO --> DR
    SO --> BA
    SO --> GU
    SO --> KY
    SO --> MX
    SO --> MA
    DR --> ME
    BA --> ME
    GU --> ME
    KY --> ME
    ME --> MT
    ME --> PR
    ME --> DM
    MX --> T3
    MA --> T3
    T3 --> T1
    T3 --> T2
    DR -.->|optional| LLM
    BA -.->|optional| LLM
    GU -.->|optional| LLM
    KY -.->|optional| LLM
```

---

## Orchestration Order

Agents run **sequentially** so each can react to what came before:

```
1. DrummerAgent    → establishes the groove
2. BassistAgent    → locks to the kick drum + chord root
3. GuitaristAgent  → fills harmonic space around bass
4. KeyboardistAgent (optional) → adds pads/voicings in remaining space
5. MixerAgent      → assigns levels, pan, EQ to all tracks
6. MasteringAgent  → applies final loudness metadata
```

This order is **intentional and stable**. Do not change it unless the task explicitly requires it.

---

## Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant Orchestrator
    participant Agents
    participant MidiEngine
    participant DAW

    Client->>Orchestrator: SessionRequest(genre, key, mode, tempo)
    Orchestrator->>Orchestrator: build chord_progression per section
    loop For each agent
        Orchestrator->>Agents: generate(context, chord_progression)
        Agents->>MidiEngine: build_track(notes, velocities, durations)
        MidiEngine-->>Agents: MidiTrackData
        Agents-->>Orchestrator: MidiTrackData
    end
    Orchestrator->>MidiEngine: merge_tracks()
    MidiEngine-->>Orchestrator: combined MidiFile
    Orchestrator->>DAW: export(session_id, midi_file)
    DAW-->>Client: file paths
```

---

## Module Map

```
src/audio_engineer/
├── agents/
│   ├── base.py              BaseMusician, BaseEngineer, SessionContext
│   ├── orchestrator.py      SessionOrchestrator
│   ├── musician/
│   │   ├── drummer.py       DrummerAgent
│   │   ├── bassist.py       BassistAgent
│   │   ├── guitarist.py     GuitaristAgent
│   │   └── keyboardist.py   KeyboardistAgent
│   └── engineer/
│       ├── mixer.py         MixerAgent
│       └── mastering.py     MasteringAgent
├── core/
│   ├── models.py            Pydantic models
│   ├── music_theory.py      Scales, chords, progressions
│   ├── midi_engine.py       MIDI file construction (mido)
│   ├── patterns.py          Genre-specific pattern library
│   ├── rhythm.py            Rhythmic utilities
│   └── constants.py         TICKS_PER_BEAT, MIDI note maps
├── daw/
│   ├── base.py              AbstractDAWBackend
│   ├── export.py            Raw MIDI / WAV file export
│   ├── fluidsynth.py        FluidSynth rendering
│   ├── timidity.py          TiMidity rendering
│   ├── garageband.py        GarageBand AppleScript integration
│   └── logic_pro.py         Logic Pro AppleScript integration
├── api/
│   ├── app.py               FastAPI application factory
│   └── routes/              Sessions, tracks, exports
└── config/
    ├── settings.py          pydantic-settings configuration
    └── logging.py           Logging setup
```

---

## Key Design Decisions

### Why Sequential Generation?

Each instrument in a real session band listens to what has already been played. The drummer sets the groove; the bassist locks to the kick; the guitarist fills harmonic space around the bass. Sequential generation naturally models this dependency chain.

### Why Pydantic Models?

All external boundaries (API requests/responses, agent outputs, config) use Pydantic v2 models. This gives us:
- Validated inputs at runtime
- Clear, serializable data contracts between agents
- Auto-generated OpenAPI schema for the REST API

### Why mido?

[mido](https://mido.readthedocs.io/) is a lightweight, pure-Python MIDI library. It provides direct control over MIDI message construction without heavyweight abstractions, which keeps the MIDI engine deterministic and testable.

### DAW Integration Tiers

| Tier | Backends | Method |
| ---- | -------- | ------ |
| 1 | FluidSynth, TiMidity | Subprocess call — automated, cross-platform |
| 2 | GarageBand, Logic Pro | AppleScript / OSA — macOS only, semi-automated |
| 3 | MIDI export, WAV export | Manual import — universal fallback |
