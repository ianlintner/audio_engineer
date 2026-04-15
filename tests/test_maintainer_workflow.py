from pathlib import Path


def test_maintainer_workflow_includes_workflows_write_permission() -> None:
    workflow_file = Path(".github/workflows/maintainer.yml")
    workflow_lines = workflow_file.read_text(encoding="utf-8").splitlines()

    permissions_block: list[str] = []
    in_permissions = False
    for line in workflow_lines:
        if line.startswith("permissions:"):
            in_permissions = True
            continue
        if in_permissions and line and not line.startswith(" "):
            break
        if in_permissions:
            permissions_block.append(line)

    assert "  workflows: write" in permissions_block
