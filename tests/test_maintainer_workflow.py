from pathlib import Path


def test_maintainer_workflow_has_workflows_write_permission() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "maintainer.yml"
    )
    workflow_text = workflow_path.read_text()

    assert "permissions:" in workflow_text
    assert "  workflows: write" in workflow_text
