"""Persistence helpers for immutable run artifacts."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from runner import paths


def run_dir(config_id: int, task_id: str, repeat_index: int) -> Path:
    return paths.RUNS / str(config_id) / task_id / str(repeat_index)


def raw_dir(config_id: int, task_id: str, repeat_index: int) -> Path:
    return run_dir(config_id, task_id, repeat_index) / "raw"


def home_dir(config_id: int, task_id: str, repeat_index: int) -> Path:
    return run_dir(config_id, task_id, repeat_index) / "home"


def trace_path(config_id: int, task_id: str, repeat_index: int) -> Path:
    return paths.REPO / "traces" / str(config_id) / task_id / f"{repeat_index}.json"


def private_audit_path(config_id: int, task_id: str, repeat_index: int) -> Path:
    return paths.PRIVATE_AUDITS / str(config_id) / task_id / f"{repeat_index}.md"


def ensure_trace_writable(config_id: int, task_id: str, repeat_index: int, overwrite: bool = False) -> None:
    path = trace_path(config_id, task_id, repeat_index)
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"trace already exists: {path}; use a unique --repeat or pass --overwrite intentionally"
        )


def save_raw(config_id: int, task_id: str, repeat_index: int, artifacts: dict[str, Path]) -> dict[str, str]:
    dst_dir = raw_dir(config_id, task_id, repeat_index)
    dst_dir.mkdir(parents=True, exist_ok=True)
    saved: dict[str, str] = {}
    used_names: set[str] = set()

    for name, src in artifacts.items():
        if not src:
            continue
        src = Path(src)
        if not src.exists() or not src.is_file():
            continue
        dst_name = src.name
        if dst_name in used_names:
            dst_name = f"{name}{src.suffix}"
        used_names.add(dst_name)
        dst = dst_dir / dst_name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        saved[name] = str(dst)
    return saved


def save_private_audit(trace: dict, content: str) -> Path:
    path = private_audit_path(trace["config_id"], trace["task_id"], trace["repeat_index"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def save_trace(trace: dict, overwrite: bool = False) -> Path:
    path = trace_path(trace["config_id"], trace["task_id"], trace["repeat_index"])
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"trace already exists: {path}; use a unique --repeat or pass --overwrite intentionally"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return path
