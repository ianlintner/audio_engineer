# Contributing

Thank you for your interest in contributing to AI Music Studio! This document covers everything you need to get started.

---

## Code of Conduct

Be respectful, constructive, and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

---

## Ways to Contribute

- 🐛 **Bug reports** — open a GitHub issue using the bug template
- 💡 **Feature requests** — open a GitHub issue using the feature template
- 📝 **Documentation** — fix typos, add examples, improve clarity
- 🎵 **New genre presets** — add patterns to `core/patterns.py`
- 🤖 **New agents** — add a musician or engineer agent
- 🎛️ **DAW backends** — integrate a new DAW or audio tool
- 🧪 **Tests** — improve coverage, add regression tests

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/audio_engineer.git
cd audio_engineer

# 2. Create a feature branch
git checkout -b feat/my-feature

# 3. Install all dev dependencies
pip install -e ".[dev]"

# 4. Verify tests pass
pytest -v

# 5. Verify lint passes
ruff check src tests scripts
```

---

## Development Guidelines

### Orchestration Order

Keep the generation order **drums → bass → guitar → keys** stable unless the task explicitly changes it. This order models real session-band dependencies.

### Determinism

- Prefer deterministic defaults for all musical parameters.
- Isolate randomness behind explicit `seed` or `random_state` parameters.
- Tests should be reproducible across runs.

### Pure Functions

Music theory helpers in `core/music_theory.py` and pattern functions in `core/patterns.py` should be **pure functions** with no side effects.

### Testing

- Add or update tests for every non-trivial behavior change.
- Tests live in `tests/` mirroring the `src/` structure.
- Use `pytest` fixtures from `tests/conftest.py`.

```bash
pytest -v                      # run all tests
pytest tests/agents/ -v        # run agent tests only
pytest -k test_drummer -v      # run a specific test
```

### Linting

```bash
ruff check src tests scripts       # check
ruff check --fix src tests scripts # auto-fix safe issues
```

---

## Pull Request Guidelines

1. Fill out the PR template completely.
2. Include a short rationale: _why_ this change, not just _what_.
3. Mention behavior changes and migration notes.
4. Keep PRs focused — avoid unrelated refactors in the same PR.
5. Ensure CI passes (lint + tests) before requesting review.

---

## Adding a Genre Preset

1. Open `src/audio_engineer/core/patterns.py`.
2. Add a new entry to the `GENRE_PATTERNS` dict:

```python
"my_genre": GenrePattern(
    kick_pattern=[0, 480, 960, 1440],
    snare_pattern=[480, 1440],
    hihat_pattern=[0, 240, 480, 720, 960, 1200, 1440, 1680],
    velocity_map={0: 100, 480: 90, 960: 100, 1440: 90},
    default_tempo=120,
),
```

3. Add the genre name to the CLI `--genre` choices in `scripts/generate_demo.py`.
4. Add a test in `tests/core/test_patterns.py`.

---

## Docs Site

The documentation is built with [MkDocs + Material](https://squidfunk.github.io/mkdocs-material/).

```bash
# Install docs extras
pip install -e ".[docs]"

# Serve locally with live reload
mkdocs serve

# Build static site
mkdocs build
```

The site is auto-deployed to GitHub Pages on every push to `main` via `.github/workflows/docs.yml`.

---

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add reggae genre preset
fix: correct bass octave in blues pattern
docs: add DAW integration guide
test: add KeyboardistAgent regression test
chore: upgrade ruff to 0.4
```
