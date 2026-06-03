import os
import shutil
import subprocess
from pathlib import Path
from runner.provision import load_tasks, provision_task
from runner import paths


def test_registry_loads():
    tasks = load_tasks()
    assert any(t["id"] == "bugfix-t2-01" for t in tasks)


def test_provision_creates_clean_workdir_without_hidden_tests(tmp_path):
    tasks = {t["id"]: t for t in load_tasks()}
    wd = provision_task(tasks["bugfix-t2-01"], tmp_path / "wd")
    assert (wd / "calckit" / "money.py").exists()
    # 隱藏測試絕不可出現在 agent workdir
    assert not (wd / "graders").exists()
    assert not any(p.name == "bugfix-t2-01_test.py" for p in wd.rglob("*.py"))


def test_baseline_fails_hidden_test_before_fix(tmp_path):
    """難度校準前置：未修狀態下隱藏測試必須 fail（D3）。
    以 PYTHONPATH=workdir 讓 calckit 可 import，不污染共享 venv。"""
    tasks = {t["id"]: t for t in load_tasks()}
    wd = provision_task(tasks["bugfix-t2-01"], tmp_path / "wd")
    shutil.copy(paths.REPO / "tasks/graders/bugfix-t2-01_test.py", wd / "hidden_test.py")
    py = str(paths.RUNNER_VENV / "bin" / "python")
    env = {**os.environ, "PYTHONPATH": str(wd)}
    r = subprocess.run([py, "-m", "pytest", "hidden_test.py", "-q"],
                       cwd=wd, capture_output=True, text=True, env=env)
    assert r.returncode != 0, "baseline 應未通過隱藏測試（否則任務無區辨力）"
