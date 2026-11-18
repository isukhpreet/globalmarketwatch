"""Guards for the Codespaces setup, which can't be exercised by CI directly."""

import json

from app.core.config import PROJECT_ROOT


def test_devcontainer_forwards_port_and_allows_auto_tasks():
    d = json.loads((PROJECT_ROOT / ".devcontainer" / "devcontainer.json").read_text())
    assert 8000 in d["forwardPorts"]
    assert d["portsAttributes"]["8000"]["onAutoForward"] == "openPreview"
    assert d["customizations"]["vscode"]["settings"]["task.allowAutomaticTasks"] == "on"
    # The app is started by the VS Code task, not a detached postStartCommand
    assert "postStartCommand" not in d


def test_run_task_starts_app_on_folder_open():
    tasks = json.loads((PROJECT_ROOT / ".vscode" / "tasks.json").read_text())["tasks"]
    run = next(t for t in tasks if t["label"] == "Run GlobalMarketWatch")
    assert run["runOptions"]["runOn"] == "folderOpen"
    assert "uvicorn app.main:app" in run["command"]
    assert "--host 0.0.0.0" in run["command"] and "--port 8000" in run["command"]
