"""Guardrails for the caretaker-maintained ``maintainer.yml`` workflow.

The 2026-04-22 outage traced back to a ``workflows: write`` key that was
added to the permissions block. ``workflows`` is NOT a valid GITHUB_TOKEN
permission scope — GitHub's workflow validator rejects the YAML at parse
time and no jobs are ever scheduled, so the run fails in 0 seconds with a
bare "workflow file issue". This test enforces the valid scope set and
explicitly forbids the bad key so the outage cannot recur.
"""

import re
from pathlib import Path


_WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "maintainer.yml"


def test_maintainer_workflow_declares_permissions_block() -> None:
    text = _WORKFLOW.read_text()
    assert "permissions:" in text, "maintainer.yml must declare a permissions block"


def test_maintainer_workflow_grants_valid_write_scopes() -> None:
    """The three scopes caretaker actually needs must be granted.

    * ``contents: write`` — commit upgrade PRs, edit the state issue.
    * ``issues: write``   — create / comment on escalation issues.
    * ``pull-requests: write`` — open PRs, review, auto-merge.
    """
    text = _WORKFLOW.read_text()
    for line in ("contents: write", "issues: write", "pull-requests: write"):
        assert re.search(rf"^\s*{re.escape(line)}\s*$", text, re.MULTILINE), (
            f"expected {line!r} in permissions block"
        )


def test_maintainer_workflow_rejects_invalid_workflows_scope() -> None:
    """``workflows`` is not a valid GITHUB_TOKEN permission.

    Declaring it causes GitHub's workflow validator to reject the YAML at
    parse time, so no jobs are ever scheduled. This test is the tripwire
    that prevents the 2026-04-22 outage from recurring.
    """
    text = _WORKFLOW.read_text()
    assert not re.search(r"^\s*workflows:\s*write\s*$", text, re.MULTILINE), (
        "maintainer.yml must NOT declare 'workflows: write' — this key is "
        "rejected by GitHub's workflow validator and causes every run to fail "
        "at parse time."
    )
