"""每題開乾淨 workdir：複製 baseline、套用 setup_patch（若非空）。隱藏測試一律排除。"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
import yaml
from runner import paths

REGISTRY = paths.REPO / "tasks" / "registry.yaml"


def load_tasks() -> list[dict]:
    data = yaml.safe_load(REGISTRY.read_text())
    return data["tasks"]


def _patch_is_effective(patch_path: Path) -> bool:
    """僅含註解/空白的 patch 視為 no-op。"""
    for line in patch_path.read_text().splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return True
    return False


def provision_task(task: dict, dest: Path) -> Path:
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    baseline = paths.REPO / task["repo_baseline"] if not str(task["repo_baseline"]).startswith("/") \
        else Path(task["repo_baseline"])
    shutil.copytree(baseline, dest)
    # 安全網：絕不把 graders/ 帶進 workdir
    for g in dest.rglob("*_test.py"):
        if "graders" in g.parts:
            g.unlink()
    sp = task.get("setup_patch")
    if sp:
        patch_path = paths.REPO / sp
        if patch_path.exists() and _patch_is_effective(patch_path):
            subprocess.run(["git", "apply", str(patch_path)], cwd=dest, check=True)
    return dest
