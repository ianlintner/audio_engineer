# GitHub Copilot Instructions

You are assisting with the `audio_engineer` Python project.

## Project context
- Python package in `src/audio_engineer`.
- Tests in `tests/`.
- Entry scripts in `scripts/`.
- Primary goals: deterministic MIDI generation, clear agent orchestration, and maintainable APIs.

## Coding conventions
- Target Python 3.11+.
- Keep functions small and composable.
- Prefer explicit types and Pydantic models for external boundaries.
- Avoid hidden side effects; keep music generation steps traceable.

## Quality gates
- Run lint: `ruff check src tests scripts`.
- Run tests: `pytest -v`.
- Add or update tests for non-trivial behavior changes.
- Avoid broad refactors unrelated to the task.

## Agent-aware implementation guidance
- Preserve orchestration order (drums → bass → guitar → keys) unless task explicitly changes it.
- Keep output file naming stable (session-id-prefixed artifacts).
- Favor deterministic defaults and isolate randomness behind explicit parameters/seeds.

## PR expectations
- Include a short rationale and validation notes.
- Mention behavior changes and migration notes when applicable.
