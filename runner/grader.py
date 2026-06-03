"""統一 grader：把隱藏測試複製進 workdir 後跑 pytest，全綠才 success。
Tier-2（calckit）以 PYTHONPATH=workdir import，不污染共享 venv；
Tier-1 若需安裝才能 import，於 registry 的 grader.install 指定（如 "-e ."）。"""
from __future__ import annotations
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from runner import paths


@dataclass
class GradeResult:
    success: bool
    detail: str  # pytest summary 尾段（sanitized：不含 secrets）


def run_grader(task: dict, workdir: Path, timeout_s: int = 300) -> GradeResult:
    workdir = Path(workdir)
    g = task["grader"]
    if g["type"] != "pytest":
        raise ValueError(f"unsupported grader type: {g['type']}")
    hidden_src = paths.REPO / g["hidden_tests"]
    hidden_dst = workdir / "_hidden_grader_test.py"
    shutil.copy(hidden_src, hidden_dst)
    py = str(paths.RUNNER_VENV / "bin" / "python")
    install = g.get("install")  # 預設 None；Tier-1 才指定
    if install:
        subprocess.run([py, "-m", "pip", "install", "-q", *install.split()],
                       cwd=workdir, capture_output=True, text=True)
    env = {**os.environ, "PYTHONPATH": str(workdir)}
    try:
        r = subprocess.run([py, "-m", "pytest", "_hidden_grader_test.py", "-q"],
                           cwd=workdir, capture_output=True, text=True, timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired:
        return GradeResult(False, f"grader timeout after {timeout_s}s")
    finally:
        hidden_dst.unlink(missing_ok=True)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-8:])
    return GradeResult(r.returncode == 0, tail)
