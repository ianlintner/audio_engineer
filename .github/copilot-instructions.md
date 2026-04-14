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

<!-- Added by caretaker -->

## Caretaker System

This repository uses the [caretaker](https://github.com/ianlintner/caretaker) system for automated maintenance.

### How it works

- An orchestrator runs weekly via GitHub Actions
- It creates issues and assigns them to @copilot for execution
- When @copilot opens PRs, the orchestrator monitors them through CI, review, and merge
- The orchestrator communicates with @copilot via structured issue/PR comments

### When assigned an issue by caretaker

- Read the full issue body carefully — it contains structured instructions
- Follow the instructions exactly as written
- If unclear, comment on the issue asking for clarification
- Always ensure CI passes before considering work complete
- Reference the agent file for your role: `.github/agents/maintainer-pr.md` or `.github/agents/maintainer-issue.md`

### Pre-push checklist

Before pushing any commits, **always** run the full CI validation locally and confirm every step passes:

1. `ruff check src/ tests/` — lint
2. `pytest -v` — tests

If any step fails, fix it before committing/pushing. Do not push code that has not passed all checks.

### Caretaker conventions

- Branch naming: `maintainer/{type}-{description}`
- Commit messages: `chore(maintainer): {description}`
- Always run existing tests before pushing
- Do not modify `.github/maintainer/` files unless explicitly instructed
