from pathlib import Path


def test_maintainer_workflow_includes_workflows_write_permission() -> None:
    workflow_file = Path(".github/workflows/maintainer.yml")
    workflow_text = workflow_file.read_text(encoding="utf-8")

    assert "workflows: write" in workflow_text
