"""MCP Server for Audio Engineer - Music generation for game projects and coding assistants.

Exposes MIDI backing track generation as MCP tools so that AI coding assistants
(GitHub Copilot, Claude Code, etc.) can generate game music, prototypes, and
backing tracks directly from the editor.

Usage:
    python -m audio_engineer.mcp_server
    # or via the installed script:
    audio-engineer-mcp
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from audio_engineer.agents.orchestrator import SessionOrchestrator
from audio_engineer.core.models import (
    BandConfig,
    BandMemberConfig,
    Genre,
    Instrument,
    KeySignature,
    Mode,
    NoteName,
    SectionDef,
    SessionConfig,
    TimeSignature,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output directory - resolved from env var, server cwd, or package location
# ---------------------------------------------------------------------------
_output_env = os.environ.get("AUDIO_ENGINEER_OUTPUT")
if _output_env:
    _DEFAULT_OUTPUT = Path(_output_env)
else:
    # Walk up from this file to find the project root (contains pyproject.toml)
    _pkg_root = Path(__file__).parent
    _project_root = _pkg_root
    for _ in range(5):
        if (_project_root / "pyproject.toml").exists():
            break
        _project_root = _project_root.parent
    _DEFAULT_OUTPUT = _project_root / "output"

_DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="audio-engineer",
    instructions=(
        "AI Music Studio - Generate MIDI backing tracks for games, apps, and creative projects. "
        "Use generate_game_music for quick game-ready loops by mood (battle, exploration, town…). "
        "Use generate_track for full control over genre, key, tempo, and instrumentation. "
        "All tools return absolute paths to .mid files ready for import into any DAW or game engine."
    ),
)

# Single orchestrator instance (thread-safe for sequential MCP calls)
_orchestrator = SessionOrchestrator(output_dir=_DEFAULT_OUTPUT)

# ---------------------------------------------------------------------------
# Game mood presets
# ---------------------------------------------------------------------------
_GAME_MOODS: dict[str, dict] = {
    "battle": {
        "description": "Intense combat music - heavy, driving, aggressive",
        "genre": "hard_rock", "tempo": 155, "root": "E", "mode": "minor",
        "instruments": ["drums", "bass", "electric_guitar"],
        "sections": ["intro", "verse", "chorus", "verse", "chorus"],
        "hints": ["driving", "aggressive", "heavy"],
    },
    "exploration": {
        "description": "Open-world exploration - adventurous, melodic, upbeat",
        "genre": "classic_rock", "tempo": 105, "root": "G", "mode": "major",
        "instruments": ["drums", "bass", "electric_guitar", "keys"],
        "sections": ["intro", "verse", "chorus", "verse", "outro"],
        "hints": ["adventurous", "open", "melodic"],
    },
    "mystery": {
        "description": "Dark mystery/thriller - moody, sparse, atmospheric",
        "genre": "blues", "tempo": 75, "root": "A", "mode": "blues",
        "instruments": ["drums", "bass", "electric_guitar"],
        "sections": ["intro", "verse", "chorus", "verse"],
        "hints": ["dark", "moody", "sparse"],
    },
    "town": {
        "description": "Village/town ambience - cheerful, folk-like, inviting",
        "genre": "folk", "tempo": 100, "root": "C", "mode": "major",
        "instruments": ["drums", "bass", "acoustic_guitar", "keys"],
        "sections": ["intro", "verse", "chorus", "verse", "chorus", "outro"],
        "hints": ["upbeat", "cheerful", "simple"],
    },
    "boss": {
        "description": "Boss fight - intense, fast-paced, high-energy punk",
        "genre": "punk", "tempo": 175, "root": "D", "mode": "minor",
        "instruments": ["drums", "bass", "electric_guitar"],
        "sections": ["intro", "chorus", "verse", "chorus"],
        "hints": ["intense", "fast", "powerful"],
    },
    "peaceful": {
        "description": "Calm/ambient scenes - gentle, soft, relaxing",
        "genre": "folk", "tempo": 80, "root": "F", "mode": "major",
        "instruments": ["drums", "bass", "acoustic_guitar", "keys"],
        "sections": ["intro", "verse", "chorus", "verse", "outro"],
        "hints": ["calm", "gentle", "ambient"],
    },
    "victory": {
        "description": "Victory/celebration - triumphant, uplifting pop",
        "genre": "pop", "tempo": 128, "root": "C", "mode": "major",
        "instruments": ["drums", "bass", "electric_guitar", "keys"],
        "sections": ["intro", "chorus", "chorus"],
        "hints": ["triumphant", "uplifting", "energetic"],
    },
    "sad": {
        "description": "Sad/tragic moments - melancholic, slow blues",
        "genre": "blues", "tempo": 65, "root": "A", "mode": "minor",
        "instruments": ["drums", "bass", "acoustic_guitar"],
        "sections": ["intro", "verse", "chorus", "verse", "outro"],
        "hints": ["melancholic", "slow", "emotional"],
    },
    "dungeon": {
        "description": "Dungeon/cave crawl - dark, ominous, dorian mode",
        "genre": "blues", "tempo": 80, "root": "D", "mode": "dorian",
        "instruments": ["drums", "bass", "electric_guitar"],
        "sections": ["intro", "verse", "verse"],
        "hints": ["dark", "ominous", "repetitive"],
    },
    "chase": {
        "description": "Chase sequence - urgent, frantic, high-tempo",
        "genre": "punk", "tempo": 168, "root": "G", "mode": "minor",
        "instruments": ["drums", "bass", "electric_guitar"],
        "sections": ["verse", "chorus", "verse", "chorus"],
        "hints": ["urgent", "frantic", "driving"],
    },
    "stealth": {
        "description": "Stealth/espionage - tense, minimal, dorian groove",
        "genre": "blues", "tempo": 90, "root": "D", "mode": "dorian",
        "instruments": ["drums", "bass", "electric_guitar"],
        "sections": ["intro", "verse", "verse", "outro"],
        "hints": ["tense", "minimal", "repetitive"],
    },
    "menu": {
        "description": "Main menu / title screen - welcoming, memorable",
        "genre": "pop", "tempo": 100, "root": "C", "mode": "major",
        "instruments": ["drums", "bass", "electric_guitar", "keys"],
        "sections": ["intro", "verse", "chorus", "outro"],
        "hints": ["memorable", "polished", "inviting"],
    },
}

# Section intensity defaults
_SECTION_INTENSITY: dict[str, float] = {
    "intro": 0.5, "verse": 0.65, "pre_chorus": 0.75,
    "chorus": 0.9, "bridge": 0.8, "outro": 0.4, "solo": 0.85,
}

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_genres() -> list[str]:
    """List all available music genres for track generation."""
    return [g.value for g in Genre]


@mcp.tool()
def list_instruments() -> list[str]:
    """List all available instruments for band configuration."""
    return [i.value for i in Instrument]


@mcp.tool()
def list_modes() -> list[str]:
    """List all available musical modes/scales (major, minor, dorian, etc.)."""
    return [m.value for m in Mode]


@mcp.tool()
def list_root_notes() -> list[str]:
    """List all valid musical root notes (chromatic scale, C through B)."""
    return [n.value for n in NoteName]


@mcp.tool()
def list_game_moods() -> dict[str, str]:
    """List all game music mood presets with descriptions.

    These moods map to optimised genre/tempo/key combinations for common
    game scenarios and can be passed directly to generate_game_music.
    """
    return {name: data["description"] for name, data in _GAME_MOODS.items()}


@mcp.tool()
def list_sessions() -> list[dict]:
    """List all previously generated MIDI sessions in the output directory.

    Returns session IDs, config summaries, and file paths for each session.
    """
    sessions: list[dict] = []
    if not _DEFAULT_OUTPUT.exists():
        return sessions

    for session_dir in sorted(_DEFAULT_OUTPUT.iterdir()):
        if not session_dir.is_dir():
            continue
        config_file = session_dir / f"{session_dir.name}_config.json"
        midi_files = sorted(session_dir.glob("*.mid"))
        info: dict = {
            "session_id": session_dir.name,
            "directory": str(session_dir),
            "midi_files": [str(f) for f in midi_files],
        }
        if config_file.exists():
            try:
                info["config"] = json.loads(config_file.read_text())
            except Exception:
                pass
        sessions.append(info)

    return sessions


@mcp.tool()
def get_session(session_id: str) -> dict:
    """Get details and file paths for a specific generated session.

    Args:
        session_id: The 8-character hex session ID (e.g. 'a08616a6').
    """
    session_dir = _DEFAULT_OUTPUT / session_id
    if not session_dir.exists():
        return {"error": f"Session '{session_id}' not found. Use list_sessions to see available sessions."}

    config_file = session_dir / f"{session_id}_config.json"
    midi_files = sorted(session_dir.glob("*.mid"))

    result: dict = {
        "session_id": session_id,
        "directory": str(session_dir),
        "midi_files": [str(f) for f in midi_files],
        "full_mix": str(session_dir / f"{session_id}_full.mid"),
    }
    if config_file.exists():
        try:
            result["config"] = json.loads(config_file.read_text())
        except Exception:
            pass
    return result


@mcp.tool()
def generate_track(
    genre: str = "classic_rock",
    tempo: int = 120,
    root_note: str = "C",
    mode: str = "major",
    bars_per_section: int = 8,
    time_signature_numerator: int = 4,
    instruments: Optional[list[str]] = None,
    sections: Optional[list[str]] = None,
    style_hints: Optional[list[str]] = None,
) -> dict:
    """Generate a complete MIDI backing track with a full band.

    Produces individual instrument .mid files plus a merged full-mix .mid,
    all saved to the output directory. Returns the session ID and file paths.

    Args:
        genre: Music genre. Options: classic_rock, blues, pop, folk, country, punk, hard_rock.
        tempo: Beats per minute (40–300). Default 120.
        root_note: Root / tonic note. Options: C, C#, D, D#, E, F, F#, G, G#, A, A#, B.
        mode: Scale mode. Options: major, minor, dorian, mixolydian, pentatonic_major,
              pentatonic_minor, blues.
        bars_per_section: Number of bars in verse/chorus sections (1–64). Default 8.
                          Use 4 for short game loops, 16 for longer compositions.
        time_signature_numerator: Beats per bar (3 for waltz, 4 for common time, 6 for 6/8).
        instruments: Instruments to include in the band. Drums and bass are always generated.
                     Options: drums, bass, electric_guitar, acoustic_guitar, keys.
                     Default: ["drums", "bass", "electric_guitar"].
        sections: Ordered list of song sections.
                  Default: ["intro", "verse", "chorus", "verse", "chorus", "outro"].
                  Options: intro, verse, pre_chorus, chorus, bridge, solo, outro.
        style_hints: Free-text style suggestions (e.g. ["palm muted", "fingerstyle", "driving"]).
    """
    # --- Validate inputs ---
    try:
        genre_enum = Genre(genre)
    except ValueError:
        return {"error": f"Invalid genre '{genre}'. Options: {[g.value for g in Genre]}"}

    try:
        note_enum = NoteName(root_note)
    except ValueError:
        return {"error": f"Invalid root note '{root_note}'. Options: {[n.value for n in NoteName]}"}

    try:
        mode_enum = Mode(mode)
    except ValueError:
        return {"error": f"Invalid mode '{mode}'. Options: {[m.value for m in Mode]}"}

    if not 40 <= tempo <= 300:
        return {"error": f"Tempo must be 40–300 BPM, got {tempo}."}

    if not 1 <= bars_per_section <= 64:
        return {"error": f"bars_per_section must be 1–64, got {bars_per_section}."}

    # --- Band config ---
    if instruments is None:
        instruments = ["drums", "bass", "electric_guitar"]

    # Ensure drums and bass are always present (orchestrator always generates them)
    for required in ("drums", "bass"):
        if required not in instruments:
            instruments = [required] + instruments

    members: list[BandMemberConfig] = []
    for instr_str in instruments:
        try:
            instr = Instrument(instr_str)
        except ValueError:
            return {"error": f"Invalid instrument '{instr_str}'. Options: {[i.value for i in Instrument]}"}
        members.append(BandMemberConfig(
            instrument=instr,
            enabled=True,
            style_hints=style_hints or [],
        ))

    # --- Song structure ---
    if sections is None:
        sections = ["intro", "verse", "chorus", "verse", "chorus", "outro"]

    structure: list[SectionDef] = []
    for sec_name in sections:
        intensity = _SECTION_INTENSITY.get(sec_name.lower(), 0.7)
        bars = 4 if sec_name in ("intro", "outro") else bars_per_section
        structure.append(SectionDef(name=sec_name, bars=bars, intensity=intensity))

    config = SessionConfig(
        genre=genre_enum,
        tempo=tempo,
        key=KeySignature(root=note_enum, mode=mode_enum),
        time_signature=TimeSignature(
            numerator=time_signature_numerator,
            denominator=4,
        ),
        structure=structure,
        band=BandConfig(members=members),
    )

    try:
        session = _orchestrator.create_session(config)
        session = _orchestrator.run_session(session, render_audio=False, backend_name="export")
    except Exception as exc:
        logger.exception("Session generation failed")
        return {"error": f"Generation failed: {exc}"}

    midi_files = [f for f in session.output_files if f.endswith(".mid")]
    full_mix = next((f for f in midi_files if "_full" in f), None)

    return {
        "session_id": session.id,
        "status": session.status.value,
        "directory": str(_DEFAULT_OUTPUT / session.id),
        "full_mix_midi": full_mix,
        "track_midi_files": [f for f in midi_files if "_full" not in f],
        "all_files": session.output_files,
        "config_summary": {
            "genre": genre,
            "tempo_bpm": tempo,
            "key": f"{root_note} {mode}",
            "time_signature": f"{time_signature_numerator}/4",
            "instruments": instruments,
            "sections": sections,
            "bars_per_section": bars_per_section,
        },
        "usage_tip": (
            "Import the full_mix_midi file into any DAW or game engine. "
            "Individual track files allow per-instrument mixing. "
            "MIDI files can be converted to audio using FluidSynth or a soundfont."
        ),
    }


@mcp.tool()
def generate_game_music(
    mood: str,
    bars_per_section: int = 8,
    custom_tempo: Optional[int] = None,
    custom_root: Optional[str] = None,
    custom_mode: Optional[str] = None,
    extra_instruments: Optional[list[str]] = None,
) -> dict:
    """Generate MIDI music optimised for game use with a mood/theme preset.

    Returns session ID and absolute paths to .mid files ready for import into
    Unity, Godot, Unreal, or any DAW. Use list_game_moods to see all presets.

    Args:
        mood: Game music mood. Options: battle, exploration, mystery, town, boss,
              peaceful, victory, sad, dungeon, chase, stealth, menu.
        bars_per_section: Bars per loopable section (4 = short loop, 8 = standard,
                          16 = long). Default 8.
        custom_tempo: Override the preset BPM (40–300).
        custom_root: Override the preset root note (C, C#, D, … B).
        custom_mode: Override the preset mode (major, minor, dorian, …).
        extra_instruments: Additional instruments on top of the preset defaults
                           (e.g. ["keys"] to add keys to a battle preset).
    """
    if mood not in _GAME_MOODS:
        return {
            "error": f"Unknown mood '{mood}'.",
            "available_moods": list(_GAME_MOODS.keys()),
            "tip": "Call list_game_moods to see descriptions of each mood.",
        }

    preset = _GAME_MOODS[mood]
    instruments = list(preset["instruments"])
    if extra_instruments:
        for instr in extra_instruments:
            if instr not in instruments:
                instruments.append(instr)

    result = generate_track(
        genre=preset["genre"],
        tempo=custom_tempo if custom_tempo is not None else preset["tempo"],
        root_note=custom_root or preset["root"],
        mode=custom_mode or preset["mode"],
        bars_per_section=bars_per_section,
        instruments=instruments,
        sections=preset["sections"],
        style_hints=preset["hints"],
    )

    if "error" not in result:
        result["mood"] = mood
        result["mood_description"] = preset["description"]

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server over stdio (default for VS Code / Claude Code)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
