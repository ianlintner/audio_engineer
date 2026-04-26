"""Guardrails for the caretaker-maintained ``maintainer.yml`` workflow.

The 2026-04-22 outage traced back to a ``workflows: write`` key that was
added to the job-level ``permissions`` block. ``workflows`` is NOT a
valid GITHUB_TOKEN permission scope — GitHub's workflow validator
rejects the YAML at parse time and no jobs are ever scheduled, so the
run fails in 0 seconds with a bare "workflow file issue". This test
enforces the valid scope set and explicitly forbids the bad key so the
outage cannot recur.

The 2026-04-26 config error was caused by two bootstrap-check FAILs:
1. ``fleet_registry.secret_env`` defaulting to ``"CARETAKER_FLEET_SECRET"``
   while that env var is not provisioned (OAuth2 is used instead).
2. ``llm.provider`` defaulting to ``"anthropic"``, requiring
   ``ANTHROPIC_API_KEY`` which is not set; the workflow uses Azure AI via
   LiteLLM instead.
Additionally, the ``self-heal-on-failure`` job used ``--mode self-heal``
which is not a valid RunMode in the caretaker CLI.

See ``docs/plans/2026-04-22-audio_engineer-bootstrap.md`` in the
caretaker repo for the full post-mortem.
"""

import re
from pathlib import Path


_WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "maintainer.yml"
_CONFIG = Path(__file__).resolve().parents[1] / ".github" / "maintainer" / "config.yml"


def test_maintainer_workflow_declares_permissions_block() -> None:
    text = _WORKFLOW.read_text()
    assert "permissions:" in text, "maintainer.yml must declare a permissions block"


def test_maintainer_workflow_grants_valid_write_scopes() -> None:
    """The three scopes caretaker actually needs must be granted.

    These are the minimum scopes declared by the caretaker-shipped
    ``setup-templates/templates/workflows/maintainer.yml``:

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

    Declaring it causes the workflow to fail at YAML-parse time. The
    valid set is the table at
    https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication#permissions-for-the-github_token
    — ``workflows`` is not on it.

    This test is the tripwire that caught the 2026-04-22 bootstrap
    outage and the one that prevents it from ever coming back.
    """
    text = _WORKFLOW.read_text()
    assert not re.search(r"^\s*workflows:\s*write\s*$", text, re.MULTILINE), (
        "maintainer.yml must NOT declare 'workflows: write' — this key is "
        "rejected by GitHub's workflow validator and causes every run to fail "
        "at parse time. See docs/plans/2026-04-22-audio_engineer-bootstrap.md "
        "in the caretaker repo."
    )


def test_self_heal_job_uses_event_mode() -> None:
    """``self-heal`` is not a valid RunMode in the caretaker CLI.

    The self-heal-on-failure job must invoke ``--mode event`` so that
    caretaker dispatches the workflow_run event payload through its
    existing event router. Using ``--mode self-heal`` raises
    ``click.BadParameter`` and the job exits with code 1.
    """
    text = _WORKFLOW.read_text()
    assert "--mode self-heal" not in text, (
        "maintainer.yml self-heal job must NOT use '--mode self-heal' — "
        "'self-heal' is not a supported RunMode. Use '--mode event' instead."
    )
    assert re.search(r"--mode event", text), (
        "maintainer.yml self-heal job must use '--mode event' for the "
        "self-heal-on-failure step."
    )


def test_fleet_registry_hmac_secret_env_disabled() -> None:
    """``fleet_registry.secret_env`` must be set to empty string.

    When ``fleet_registry.enabled: true`` and ``secret_env`` is left at
    its default (``"CARETAKER_FLEET_SECRET"``), the bootstrap-check
    reports FAIL because the env var is not provisioned. This repo uses
    OAuth2 for fleet registry auth, so the HMAC secret must be disabled
    by setting ``secret_env: ""``.
    """
    text = _CONFIG.read_text()
    assert re.search(r'secret_env:\s*""', text) or re.search(r"secret_env:\s*''", text), (
        "config.yml fleet_registry.secret_env must be set to empty string "
        "to disable HMAC auth. The repo uses OAuth2 instead."
    )


def test_llm_provider_is_litellm() -> None:
    """``llm.provider`` must be ``litellm``, not ``anthropic``.

    When ``provider: anthropic`` (the default), the bootstrap-check
    requires ``ANTHROPIC_API_KEY`` as a hard FAIL. This repo routes
    through Azure AI via LiteLLM (``AZURE_AI_API_KEY`` /
    ``AZURE_AI_API_BASE``), so the provider must be ``litellm``.
    """
    text = _CONFIG.read_text()
    assert re.search(r"^\s*provider:\s*litellm\s*(?:#.*)?$", text, re.MULTILINE), (
        "config.yml llm.provider must be 'litellm' to avoid requiring "
        "ANTHROPIC_API_KEY. The workflow uses Azure AI credentials instead."
    )
