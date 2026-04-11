"""LLM prompt engineering helpers for MIDI generation."""
from __future__ import annotations

import json
import re
from typing import Any

from audio_engineer.providers.base import TrackRequest
from audio_engineer.core.constants import TICKS_PER_BEAT

_MIDI_JSON_SCHEMA = """[
  {
    "pitch": <int 0-127>,
    "velocity": <int 1-127>,
    "start_beat": <float, 1-indexed, e.g. 1.0 = first beat>,
    "duration_beats": <float, e.g. 0.5 = eighth note>
  },
  ...
]"""

_PROMPT_TEMPLATE = """\
You are a MIDI composer. Generate a one-bar MIDI pattern for a {instrument} track.

Musical context:
- Genre: {genre}
- Key: {key}
- Tempo: {tempo} BPM
- Time signature: {time_sig}
- Style hints: {style_hints}

Rules:
- Output ONLY valid JSON — no prose, no markdown fences.
- The JSON must be an array of note objects matching this schema:
{schema}
- All start_beat values must be in range [1, {beats_per_bar}+1).
- All pitch values must be in range 0-127.
- All velocity values must be in range 1-127.
- Include between 4 and 32 notes.

Output the JSON array now:"""


def build_midi_prompt(request: TrackRequest, beats_per_bar: int = 4) -> str:
    """Build a structured MIDI generation prompt from a TrackRequest."""
    genre = request.genre or "pop"
    key = request.key or "C major"
    tempo = request.tempo or 120
    instrument = request.instrument or "piano"
    style_hints = ", ".join(request.style_hints) if request.style_hints else "standard"
    time_sig = request.time_signature or "4/4"

    return _PROMPT_TEMPLATE.format(
        instrument=instrument,
        genre=genre.replace("_", " "),
        key=key,
        tempo=tempo,
        time_sig=time_sig,
        style_hints=style_hints,
        schema=_MIDI_JSON_SCHEMA,
        beats_per_bar=beats_per_bar,
    )


def parse_midi_json(response_text: str) -> list[dict[str, Any]] | None:
    """Parse LLM response into a list of note dicts.

    Tolerantly strips markdown code fences before parsing.
    Returns None if the response cannot be parsed.
    """
    text = response_text.strip()

    # Strip markdown code fences  ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Find first '[' and last ']' to isolate the array
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(data, list):
        return None
    return data


def validate_midi_events(
    events: list[dict[str, Any]],
    beats_per_bar: int = 4,
    max_notes: int = 128,
) -> list[dict[str, Any]]:
    """Validate and sanitise raw event dicts from LLM output.

    Removes events that are out-of-range or structurally invalid.
    Clamps numeric fields to safe MIDI ranges.
    Returns the cleaned list (may be empty).
    """
    valid: list[dict[str, Any]] = []
    seen_count = 0

    for item in events:
        if not isinstance(item, dict):
            continue
        if seen_count >= max_notes:
            break

        try:
            pitch = int(item.get("pitch", -1))
            velocity = int(item.get("velocity", -1))
            start_beat = float(item.get("start_beat", -1))
            duration_beats = float(item.get("duration_beats", -1))
        except (TypeError, ValueError):
            continue

        if not (0 <= pitch <= 127):
            continue
        if not (1 <= velocity <= 127):
            continue
        if not (1.0 <= start_beat < beats_per_bar + 1):
            continue
        if not (0.0 < duration_beats <= beats_per_bar):
            continue

        valid.append({
            "pitch": pitch,
            "velocity": velocity,
            "start_beat": start_beat,
            "duration_beats": duration_beats,
        })
        seen_count += 1

    return valid


def events_to_note_events(
    events: list[dict[str, Any]],
    channel: int = 0,
    ticks_per_beat: int = TICKS_PER_BEAT,
    bar_offset_ticks: int = 0,
) -> list[Any]:
    """Convert validated event dicts to NoteEvent objects."""
    from audio_engineer.core.models import NoteEvent

    result: list[NoteEvent] = []
    for ev in events:
        start_tick = bar_offset_ticks + int((ev["start_beat"] - 1.0) * ticks_per_beat)
        duration_ticks = max(1, int(ev["duration_beats"] * ticks_per_beat))
        result.append(NoteEvent(
            pitch=ev["pitch"],
            velocity=ev["velocity"],
            start_tick=start_tick,
            duration_ticks=duration_ticks,
            channel=channel,
        ))
    return result
