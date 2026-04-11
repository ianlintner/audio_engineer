# MCP Server

AI Music Studio ships an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes backing-track generation as tools for AI coding assistants — GitHub Copilot, Claude Code, Cursor, and any other MCP-compatible client.

---

## Quick Start

The MCP server entry point is installed automatically with the package:

```bash
pip install -e "."

# Run the MCP server (stdio transport — standard for AI assistant integrations)
audio-engineer-mcp
# or equivalently:
python -m audio_engineer.mcp_server
```

### GitHub Copilot / Claude Code

Add the server to your assistant's MCP configuration. For example, in a `.mcp.json` or `settings.json`:

```json
{
  "mcpServers": {
    "audio-engineer": {
      "command": "audio-engineer-mcp"
    }
  }
}
```

After connecting, the tools listed below are available directly in your editor.

---

## Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `AUDIO_ENGINEER_OUTPUT` | Directory where the MCP server writes generated files | auto-detected project `output/` |

---

## Available Tools

### `generate_track`

Generate a complete MIDI backing track with a full band.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `genre` | string | `classic_rock` | Genre preset (see `list_genres`) |
| `tempo` | int | `120` | BPM (40–300) |
| `root_note` | string | `C` | Root/tonic note (C, C#, D … B) |
| `mode` | string | `major` | Scale mode (major, minor, dorian, mixolydian, pentatonic_major, pentatonic_minor, blues) |
| `bars_per_section` | int | `8` | Bars per section (1–64); use 4 for short game loops |
| `time_signature_numerator` | int | `4` | Beats per bar (3, 4, 6, …) |
| `instruments` | list | `["drums","bass","electric_guitar"]` | Instruments to include; drums and bass are always present |
| `sections` | list | `["intro","verse","chorus","verse","chorus","outro"]` | Ordered song sections |
| `style_hints` | list | `[]` | Free-text hints, e.g. `["palm muted", "driving"]` |

**Returns:** `session_id`, `full_mix_midi` path, `track_midi_files` list, `directory`, and a `config_summary`.

---

### `generate_game_music`

Generate game-ready MIDI loops from a mood preset — no musical knowledge required.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `mood` | string | — | Game mood (see `list_game_moods`) |
| `bars_per_section` | int | `8` | Loop length (4 = short, 8 = standard, 16 = long) |
| `custom_tempo` | int | _(preset)_ | Override the preset BPM |
| `custom_root` | string | _(preset)_ | Override the preset root note |
| `custom_mode` | string | _(preset)_ | Override the preset scale mode |
| `extra_instruments` | list | `[]` | Add instruments on top of the preset defaults |

**Available moods:** `battle`, `exploration`, `mystery`, `town`, `boss`, `peaceful`, `victory`, `sad`, `dungeon`, `chase`, `stealth`, `menu`

**Returns:** same shape as `generate_track`.

---

### `generate_audio_track`

Route a track request through the provider registry. Use this when you want to target a specific provider (e.g. Gemini Lyria) or let the registry pick the best available backend.

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `track_name` | string | Identifier for the track |
| `description` | string | Natural-language description of the desired sound |
| `genre` | string | Optional genre hint |
| `key` | string | Optional key hint |
| `tempo` | int | Optional BPM |
| `duration_seconds` | float | Requested duration |
| `style_hints` | list | Free-text style hints |
| `provider` | string | Force a specific provider by name (e.g. `midi_engine`, `gemini_lyria`) |

**Returns:** `provider_used`, `success`, `output_path` (if applicable), and any error message.

---

### `list_genres`

Returns the list of all supported genre presets.

---

### `list_game_moods`

Returns all game music mood presets with descriptions, default genre, tempo, root note, and mode.

---

### `list_providers`

Returns all registered audio providers with their capabilities and availability status.

---

## Output Files

All generated MIDI files are written to the output directory and absolute paths are returned in every tool response. Files follow the naming convention:

```
<output_dir>/
└── <session-id>/
    ├── <session-id>_drums.mid
    ├── <session-id>_bass.mid
    ├── <session-id>_guitar.mid
    └── <session-id>_full.mid   ← combined full-mix file
```

Import the `_full.mid` file into any DAW (GarageBand, Logic Pro, Ableton, etc.) or game engine (Unity, Godot, Unreal) directly.
