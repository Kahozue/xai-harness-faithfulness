"""Phase 2 trace readiness validation.

This is a post-run gate. It does not launch harnesses or mutate artifacts.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from runner import paths, persist
from runner.configs import CONFIGS
from runner.provision import load_tasks
from runner.trace_schema import validate_trace

LIMIT_PATTERNS = (
    "specified api usage limits",
    "you have reached your specified api usage limits",
    "insufficient_quota",
    "rate_limit_error",
    "billing hard limit",
)


def _phase2_plan(
    repeat_start: int,
    repeats: int,
    config_ids: list[int] | None,
    task_ids: list[str] | None,
) -> list[dict[str, int | str]]:
    if repeats < 1:
        raise ValueError("--repeats must be >= 1")
    if repeat_start < 0:
        raise ValueError("--repeat-start must be >= 0")

    known_configs = {cfg.id for cfg in CONFIGS}
    selected_configs = config_ids or [cfg.id for cfg in CONFIGS]
    unknown_configs = sorted(set(selected_configs) - known_configs)
    if unknown_configs:
        raise ValueError(f"unknown config id(s): {unknown_configs}")

    all_task_ids = [task["id"] for task in load_tasks()]
    selected_tasks = task_ids or all_task_ids
    unknown_tasks = sorted(set(selected_tasks) - set(all_task_ids))
    if unknown_tasks:
        raise ValueError(f"unknown task id(s): {unknown_tasks}")

    return [
        {"config": config_id, "task": task_id, "repeat": repeat_index}
        for config_id in selected_configs
        for task_id in selected_tasks
        for repeat_index in range(repeat_start, repeat_start + repeats)
    ]


def _cfg_by_id() -> dict[int, Any]:
    return {cfg.id: cfg for cfg in CONFIGS}


def _exists(path: str | None) -> bool:
    return bool(path) and Path(path).exists()


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _contains_limit_pattern(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    patterns = [p.encode("utf-8") for p in LIMIT_PATTERNS]
    try:
        with path.open("rb") as fh:
            while chunk := fh.read(1024 * 1024):
                lower = chunk.lower()
                for pattern in patterns:
                    if pattern in lower:
                        return pattern.decode("utf-8")
    except OSError:
        return None
    return None


def _short(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO))
    except ValueError:
        return str(path)


def validate_phase2(
    repeat_start: int = 1,
    repeats: int = 3,
    config_ids: list[int] | None = None,
    task_ids: list[str] | None = None,
) -> dict[str, Any]:
    planned = _phase2_plan(repeat_start, repeats, config_ids, task_ids)
    cfgs = _cfg_by_id()

    missing_traces: list[str] = []
    invalid_json: list[dict[str, str]] = []
    invalid_schema: list[dict[str, str]] = []
    metadata_mismatches: list[dict[str, str]] = []
    missing_private_audits: list[str] = []
    private_audit_mismatches: list[dict[str, str]] = []
    missing_raw_dirs: list[str] = []
    missing_raw_artifacts: list[dict[str, str]] = []
    raw_artifact_outside_raw_dir: list[dict[str, str]] = []
    missing_run_homes: list[str] = []
    nonisolated_run_homes: list[str] = []
    infra_failure_flags: list[dict[str, str]] = []

    config_counts: Counter[int] = Counter()
    config_success: Counter[int] = Counter()
    config_zero_tools: Counter[int] = Counter()
    config_tool_totals: Counter[int] = Counter()
    config_reasoning: Counter[int] = Counter()
    config_decision_points: Counter[int] = Counter()
    config_tool_names: dict[int, Counter[str]] = defaultdict(Counter)

    for item in planned:
        config_id = int(item["config"])
        task_id = str(item["task"])
        repeat_index = int(item["repeat"])
        trace_file = persist.trace_path(config_id, task_id, repeat_index)
        if not trace_file.exists():
            missing_traces.append(_short(trace_file))
            continue

        try:
            trace = json.loads(trace_file.read_text())
        except Exception as exc:  # pragma: no cover - defensive on corrupt files
            invalid_json.append({"trace": _short(trace_file), "error": type(exc).__name__, "detail": str(exc)})
            continue

        try:
            validate_trace(trace)
        except Exception as exc:
            invalid_schema.append({"trace": _short(trace_file), "error": type(exc).__name__, "detail": str(exc)})

        cfg = cfgs[config_id]
        expected_run_id = f"c{config_id}__{cfg.harness}__{task_id}__r{repeat_index}"
        expected = {
            "config_id": config_id,
            "task_id": task_id,
            "repeat_index": repeat_index,
            "harness": cfg.harness,
            "model_snapshot": cfg.model_snapshot,
            "run_id": expected_run_id,
        }
        for key, expected_value in expected.items():
            if trace.get(key) != expected_value:
                metadata_mismatches.append({
                    "trace": _short(trace_file),
                    "field": key,
                    "expected": str(expected_value),
                    "actual": str(trace.get(key)),
                })

        config_counts[config_id] += 1
        if (trace.get("outcome") or {}).get("success") is True:
            config_success[config_id] += 1
        tool_calls = trace.get("tool_calls") or []
        if not tool_calls:
            config_zero_tools[config_id] += 1
        config_tool_totals[config_id] += len(tool_calls)
        for tc in tool_calls:
            config_tool_names[config_id][str(tc.get("tool_name") or "?")] += 1
        if trace.get("reasoning_steps"):
            config_reasoning[config_id] += 1
        if trace.get("decision_points"):
            config_decision_points[config_id] += 1

        expected_audit = persist.private_audit_path(config_id, task_id, repeat_index)
        audit_path = trace.get("private_audit_path")
        if not _exists(audit_path):
            missing_private_audits.append(_short(trace_file))
        elif Path(audit_path).resolve() != expected_audit.resolve():
            private_audit_mismatches.append({
                "trace": _short(trace_file),
                "expected": str(expected_audit),
                "actual": str(audit_path),
            })

        expected_raw_dir = persist.raw_dir(config_id, task_id, repeat_index)
        raw_log_path = Path(str(trace.get("raw_log_path") or ""))
        if not raw_log_path.exists() or not expected_raw_dir.exists():
            missing_raw_dirs.append(_short(trace_file))

        raw_artifacts = trace.get("raw_artifacts") or {}
        if not raw_artifacts:
            missing_raw_artifacts.append({"trace": _short(trace_file), "artifact": "<none>"})
        for name, artifact in sorted(raw_artifacts.items()):
            artifact_path = Path(str(artifact))
            if not artifact_path.exists():
                missing_raw_artifacts.append({"trace": _short(trace_file), "artifact": name, "path": str(artifact_path)})
                continue
            if not _is_under(artifact_path, expected_raw_dir):
                raw_artifact_outside_raw_dir.append({
                    "trace": _short(trace_file),
                    "artifact": name,
                    "path": str(artifact_path),
                    "expected_raw_dir": str(expected_raw_dir),
                })
            pattern = _contains_limit_pattern(artifact_path)
            if pattern:
                infra_failure_flags.append({"trace": _short(trace_file), "artifact": name, "pattern": pattern})

        run_home = persist.home_dir(config_id, task_id, repeat_index)
        if not run_home.exists():
            missing_run_homes.append(str(run_home))
        elif run_home.resolve() == paths.LAB_HOME.resolve() or not _is_under(run_home, paths.RUNS):
            nonisolated_run_homes.append(str(run_home))

    selected_config_ids = sorted({int(item["config"]) for item in planned})
    all_zero_tool_configs = [
        config_id for config_id in selected_config_ids
        if config_counts[config_id] and config_tool_totals[config_id] == 0
    ]

    config_summary = []
    for config_id in selected_config_ids:
        cfg = cfgs[config_id]
        n = config_counts[config_id]
        config_summary.append({
            "config": config_id,
            "harness": cfg.harness,
            "model": cfg.model_snapshot,
            "n": n,
            "success": config_success[config_id],
            "fail": n - config_success[config_id],
            "zero_tool_runs": config_zero_tools[config_id],
            "tool_calls_total": config_tool_totals[config_id],
            "reasoning_trace_runs": config_reasoning[config_id],
            "decision_point_runs": config_decision_points[config_id],
            "top_tools": config_tool_names[config_id].most_common(10),
        })

    failures = {
        "missing_traces": missing_traces,
        "invalid_json": invalid_json,
        "invalid_schema": invalid_schema,
        "metadata_mismatches": metadata_mismatches,
        "missing_private_audits": missing_private_audits,
        "private_audit_mismatches": private_audit_mismatches,
        "missing_raw_dirs": missing_raw_dirs,
        "missing_raw_artifacts": missing_raw_artifacts,
        "raw_artifact_outside_raw_dir": raw_artifact_outside_raw_dir,
        "missing_run_homes": missing_run_homes,
        "nonisolated_run_homes": nonisolated_run_homes,
        "infra_failure_flags": infra_failure_flags,
        "all_zero_tool_configs": all_zero_tool_configs,
    }
    ok = not any(failures.values())
    return {
        "ok": ok,
        "expected_traces": len(planned),
        "found_traces": len(planned) - len(missing_traces),
        "repeat_start": repeat_start,
        "repeats": repeats,
        "configs": selected_config_ids,
        "tasks": sorted({str(item["task"]) for item in planned}),
        "config_summary": config_summary,
        "failures": failures,
    }
