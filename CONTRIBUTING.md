# Contributing to audio_engineer

Thanks for contributing! This project values small, testable, well-documented changes.

## Dev setup

1. Install Python 3.11+
2. Install dependencies: `pip install -e ".[dev]"`
3. Run checks:
   - `ruff check src tests scripts`
   - `pytest -v`

## Development guidelines

- Keep orchestration order stable unless intentionally changed: drums → bass → guitar → keys.
- Prefer deterministic defaults and explicit seeds/parameters when randomness is needed.
- Add or update tests for non-trivial behavior changes.
- Keep PRs focused; avoid unrelated refactors.

## Pull requests

- Fill out the PR template.
- Include a short rationale and validation notes.
- Mention behavior changes and migration notes when applicable.
