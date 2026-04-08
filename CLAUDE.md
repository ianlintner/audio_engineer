# CLAUDE.md

Guidance for Claude Code and related coding agents working in this repository.

## Mission

Build and maintain an AI-assisted MIDI backing-track generator with clear orchestration, testability, and predictable output.

## Repository map

- `src/audio_engineer/agents/`: musician/engineer agents and orchestrator.
- `src/audio_engineer/core/`: MIDI engine, theory helpers, models.
- `src/audio_engineer/daw/`: backend integrations and exports.
- `tests/`: behavior and regression coverage.
- `scripts/`: local runner scripts.

## Development rules

1. Keep changes narrow and task-focused.
2. Preserve public APIs unless asked to change them.
3. Add/update tests with logic changes.
4. Never commit generated artifacts from `output/`.
5. Prefer pure functions in music-theory logic where practical.

## Local validation

- `ruff check src tests scripts`
- `pytest -v`

## Safety and robustness

- Validate all external inputs.
- Avoid shelling out unless needed by DAW/audio backends.
- When adding subprocess logic, use explicit argument lists and error handling.

## Collaboration style

- Explain intent before major edits.
- Document tradeoffs when changing musical heuristics.
- Keep commit messages specific and review-friendly.
