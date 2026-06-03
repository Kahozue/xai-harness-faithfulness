"""Single-run orchestration: provision, launch, normalize, grade, persist."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runner import isolation, paths, persist
from runner.adapters import get_adapter
from runner.configs import get_config
from runner.grader import run_grader
from runner.private_audit import build_private_audit
from runner.provision import load_tasks, provision_task
from runner.trace_schema import NormalizedTrace, ToolCall, validate_trace

DEFAULT_TIMEOUT_S = 900
PROTECTED_REPO_PATHS = ["tasks/target_repo", "tasks/benchmark"]


def _env_lock_ref() -> str:
    res = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=paths.REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    sha = res.stdout.strip() or "unknown"
    return f"ENVIRONMENT.lock.md@{sha}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _decode(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _main_log_name(harness: str) -> str:
    return {
        "codex": "codex.log",
        "opencode": "oc.log",
        "hermes": "hermes.log",
        "claude_code": "claude_code.log",
    }.get(harness, f"{harness}.log")


def _write_launch_logs(workdir: Path, harness: str, stdout: Any, stderr: Any) -> dict[str, Path]:
    out = _decode(stdout)
    err = _decode(stderr)
    artifacts: dict[str, Path] = {}

    main = workdir / _main_log_name(harness)
    combined = out
    if err:
        if combined and not combined.endswith("\n"):
            combined += "\n"
        combined += err
    main.write_text(combined)
    artifacts["launch_log"] = main

    if err:
        stderr_path = workdir / "harness.stderr.log"
        stderr_path.write_text(err)
        artifacts["stderr_log"] = stderr_path
    return artifacts


def _copy_latest_hermes_session(workdir: Path, run_home: Path, started_at: float) -> Path | None:
    root = run_home / ".hermes" / "sessions"
    if not root.exists():
        return None
    sessions = list(root.glob("session_*.json"))
    if not sessions:
        return None
    fresh = [p for p in sessions if p.stat().st_mtime >= started_at - 1]
    src = max(fresh or sessions, key=lambda p: (p.stat().st_mtime, str(p)))
    dst = workdir / "trace.session.json"
    shutil.copy2(src, dst)
    return dst


def _copy_latest_codex_session(workdir: Path, run_home: Path, started_at: float) -> Path | None:
    root = run_home / ".codex" / "sessions"
    if not root.exists():
        return None
    sessions = list(root.rglob("rollout-*.jsonl"))
    if not sessions:
        return None
    fresh = [p for p in sessions if p.stat().st_mtime >= started_at - 1]
    src = max(fresh or sessions, key=lambda p: (p.stat().st_mtime, str(p)))
    dst = workdir / "trace.session.jsonl"
    shutil.copy2(src, dst)
    return dst


def _load_task(task_id: str) -> dict:
    tasks = {task["id"]: task for task in load_tasks()}
    if task_id not in tasks:
        raise KeyError(f"unknown task_id={task_id}")
    return tasks[task_id]


def _merge_artifacts(primary: dict[str, Path], extra: dict[str, Path]) -> dict[str, Path]:
    merged = dict(primary)
    existing = {Path(p).resolve() for p in merged.values() if p}
    for name, path in extra.items():
        if Path(path).resolve() not in existing:
            merged[name] = path
    return merged


def _protected_repo_status() -> str:
    res = subprocess.run(
        ["git", "status", "--porcelain", "--", *PROTECTED_REPO_PATHS],
        cwd=paths.REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    return res.stdout.strip()


def _quarantine_repo_escape(workdir: Path, status: str) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "repo_escape.status").write_text(status + "\n")
    diff = subprocess.run(
        ["git", "diff", "--binary", "--", *PROTECTED_REPO_PATHS],
        cwd=paths.REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    if diff:
        (workdir / "repo_escape.diff").write_text(diff)

    for line in status.splitlines():
        if not line.startswith("?? "):
            continue
        rel = line[3:]
        src = paths.REPO / rel
        if src.exists():
            dst = workdir / "repo_escape_untracked" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

    restore_paths = [p for p in PROTECTED_REPO_PATHS if (paths.REPO / p).exists()]
    if restore_paths:
        subprocess.run(["git", "checkout", "--", *restore_paths], cwd=paths.REPO, check=True)


def run_once(
    config_id: int,
    task_id: str,
    repeat_index: int,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    secrets: dict | None = None,
    overwrite: bool = False,
) -> dict:
    cfg = get_config(config_id)
    task = _load_task(task_id)
    adapter = get_adapter(cfg.harness)
    secrets = paths.load_secrets() if secrets is None else secrets
    persist.ensure_trace_writable(config_id, task_id, repeat_index, overwrite=overwrite)

    rd = persist.run_dir(config_id, task_id, repeat_index)
    workdir = rd / "workdir"
    run_home = isolation.prepare_run_home(cfg.harness, persist.home_dir(config_id, task_id, repeat_index))
    provision_task(task, workdir)

    env = dict(os.environ)
    env.update(adapter.env(secrets, cfg.model_snapshot))
    env.update(isolation.env_for_run_home(cfg.harness, run_home))
    cmd = adapter.command(task["prompt"], cfg.model_snapshot, cfg.provider, workdir=workdir)

    started = time.time()
    launch_timed_out = False
    returncode: int | None = None
    try:
        res = subprocess.run(
            cmd,
            cwd=workdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        stdout, stderr = res.stdout, res.stderr
        returncode = res.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout, exc.stderr
        launch_timed_out = True
    wall = round(time.time() - started, 3)

    launch_artifacts = _write_launch_logs(workdir, cfg.harness, stdout, stderr)
    if cfg.harness == "hermes":
        copied = _copy_latest_hermes_session(workdir, run_home, started)
        if copied:
            launch_artifacts["hermes_session_copy"] = copied
    elif cfg.harness == "codex":
        copied = _copy_latest_codex_session(workdir, run_home, started)
        if copied:
            launch_artifacts["codex_session_copy"] = copied

    repo_status = _protected_repo_status()
    if repo_status:
        _quarantine_repo_escape(workdir, repo_status)
        raise RuntimeError(
            "repo_mutation_detected: harness modified protected repo paths; "
            f"see {workdir / 'repo_escape.status'}"
        )

    grade = run_grader(task, workdir)
    norm = adapter.normalize(workdir)
    raw_artifacts = _merge_artifacts(adapter.raw_artifacts(workdir), launch_artifacts)
    saved_raw = persist.save_raw(config_id, task_id, repeat_index, raw_artifacts)

    trace = NormalizedTrace(
        run_id=f"c{config_id}__{cfg.harness}__{task_id}__r{repeat_index}",
        config_id=config_id,
        harness=cfg.harness,
        harness_version=adapter.version,
        model=cfg.model_snapshot,
        model_snapshot=cfg.model_snapshot,
        task_id=task_id,
        task_category=task["category"],
        repeat_index=repeat_index,
        reasoning_effort="high",
        tool_calls=[ToolCall(**tc) for tc in norm["tool_calls"]],
        reasoning_steps=norm["reasoning_steps"],
        decision_points=norm["decision_points"],
        outcome={
            "success": grade.success,
            "grader_detail": grade.detail,
            "final_diff_path": None,
            "launch_returncode": returncode,
            "launch_timed_out": launch_timed_out,
        },
        tokens=norm["tokens"],
        wall_time_s=wall,
        turns=norm["turns"],
        runtime_budget=norm["runtime_budget"],
        system_present=norm.get("system_present"),
        raw_log_path=str(persist.raw_dir(config_id, task_id, repeat_index)),
        env_lock_ref=_env_lock_ref(),
        timestamp=_utc_now(),
        evidence_levels=norm.get("evidence_levels", {}),
    ).to_dict()
    trace["raw_artifacts"] = saved_raw
    audit_path = persist.save_private_audit(trace, build_private_audit(trace))
    trace["private_audit_path"] = str(audit_path)
    validate_trace(trace)
    persist.save_trace(trace, overwrite=overwrite)
    return trace
