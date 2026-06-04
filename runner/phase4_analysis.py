"""Phase 4 metric and report generation.

This module is read-only with respect to Phase 2/3 inputs. It consumes formal
Phase 2 repeats 1-3 plus Phase 3 attribution/HCI labels, then writes analysis
artifacts for the final XAI report and downstream HCI materials.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from runner import paths
from runner.configs import CONFIGS
from runner.phase3_selection import tool_family
from runner.phase4_readiness import FORMAL_REPEATS, validate_phase4_readiness
from runner.provision import load_tasks

DEFAULT_ANALYSIS_PATH = Path("analysis") / "phase4" / "metrics-summary.json"
DEFAULT_HCI_CASE_PACK_PATH = Path("analysis") / "phase4" / "hci-case-pack.json"
DEFAULT_TRACEABILITY_PATH = Path("analysis") / "phase4" / "teacher-requirements-traceability.json"
DEFAULT_REPORT_PATH = Path("docs") / "verification" / "2026-06-04-phase4-analysis-report.md"
DEFAULT_SUPPORT_REPORT_PATH = Path("docs") / "verification" / "2026-06-04-phase4-report-support-pack.md"
DEFAULT_FIGURE_DIR = Path("analysis") / "phase4" / "figures"

CONTROLLED_CATEGORIES = ("bug_fix", "rename", "add_tests", "add_logging")
TASK_SPLITS = {
    "controlled": set(CONTROLLED_CATEGORIES),
    "benchmark": {"benchmark"},
}
AGENT_CARD_DIMENSIONS = (
    "fidelity",
    "stability",
    "robustness",
    "actionability",
    "governability",
)
FIGURE_FILES = {
    "jaccard_matrix": "jaccard-matrix.svg",
    "disagreement_success_scatter": "disagreement-success-scatter.svg",
    "factorial_contrast_bars": "factorial-contrast-bars.svg",
    "method_consistency": "method-consistency.svg",
    "agent_card_matrix": "agent-card-matrix.svg",
}


def _repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else paths.REPO / path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO))
    except ValueError:
        return str(path)


def _mean(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def _population_stdev(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def _success(trace: dict[str, Any]) -> bool:
    return bool((trace.get("outcome") or {}).get("success") is True)


def _family_sequence(trace: dict[str, Any]) -> list[str]:
    return [tool_family(str(call.get("tool_name", ""))) for call in trace.get("tool_calls", [])]


def _tool_set(trace: dict[str, Any]) -> set[str]:
    return set(_family_sequence(trace))


def _jaccard_similarity(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    return len(left_set & right_set) / len(left_set | right_set)


def _normalized_levenshtein(left: list[str], right: list[str]) -> float:
    previous = list(range(len(right) + 1))
    for i, left_item in enumerate(left, start=1):
        current = [i] + [0] * len(right)
        for j, right_item in enumerate(right, start=1):
            current[j] = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (left_item != right_item),
            )
        previous = current
    return previous[-1] / max(len(left), len(right), 1)


def _sequence_divergence(left: list[str], right: list[str]) -> float:
    return ((1.0 - _jaccard_similarity(left, right)) + _normalized_levenshtein(left, right)) / 2.0


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _config_lookup() -> dict[int, dict[str, Any]]:
    return {
        config.id: {
            "config_id": config.id,
            "harness": config.harness,
            "model_role": config.model_role,
            "model_snapshot": config.model_snapshot,
            "provider": config.provider,
            "role": config.role,
        }
        for config in CONFIGS
    }


def _config_label(config_id: int) -> str:
    config = _config_lookup()[config_id]
    harness = {
        "claude_code": "Claude Code",
        "opencode": "OpenCode",
        "hermes": "Hermes",
        "codex": "Codex",
    }.get(config["harness"], config["harness"])
    model = "Haiku" if config["model_role"] == "haiku" else "GPT-mini"
    return f"c{config_id} {harness} / {model}"


def _task_lookup() -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in load_tasks()}


def load_formal_traces(
    trace_root: Path | None = None,
    repeats: tuple[int, ...] = FORMAL_REPEATS,
) -> list[dict[str, Any]]:
    """Load formal Phase 2 traces and exclude pilot/counterfactual repeats."""
    root = trace_root or paths.REPO / "traces"
    traces: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*/*.json")):
        trace = json.loads(path.read_text())
        if int(trace.get("repeat_index", -1)) not in repeats:
            continue
        trace["_trace_path"] = _rel(path)
        traces.append(trace)
    return traces


def _group_by_cell(traces: list[dict[str, Any]]) -> dict[tuple[int, str], list[dict[str, Any]]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        grouped[(int(trace["config_id"]), str(trace["task_id"]))].append(trace)
    return dict(grouped)


def _trace_evidence_score(trace: dict[str, Any]) -> float:
    checks = [
        bool(trace.get("tool_calls")),
        bool((trace.get("outcome") or {}).get("grader_detail")),
        "success" in (trace.get("outcome") or {}),
        bool(trace.get("raw_log_path")),
        bool(trace.get("private_audit_path")),
        bool(trace.get("env_lock_ref")),
        bool(trace.get("runtime_budget")),
        bool(trace.get("evidence_levels")),
    ]
    return sum(1 for check in checks if check) / len(checks)


def _trace_governability_score(trace: dict[str, Any]) -> float:
    outcome = trace.get("outcome") or {}
    checks = [
        "success" in outcome,
        bool(outcome.get("grader_detail")),
        bool(trace.get("tool_calls")),
        bool(trace.get("raw_log_path")),
        bool(trace.get("private_audit_path")),
    ]
    return sum(1 for check in checks if check) / len(checks)


def _cell_stability(traces: list[dict[str, Any]]) -> float | None:
    sequences = [_family_sequence(trace) for trace in traces]
    if len(sequences) < 2:
        return None
    similarities = [
        1.0 - _sequence_divergence(left, right)
        for left, right in combinations(sequences, 2)
    ]
    return _mean(similarities)


def _summarize_cells(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for (config_id, task_id), cell_traces in sorted(_group_by_cell(traces).items()):
        cell_traces = sorted(cell_traces, key=lambda trace: int(trace["repeat_index"]))
        first = cell_traces[0]
        sequences = [_family_sequence(trace) for trace in cell_traces]
        first_tools = Counter(sequence[0] if sequence else "<none>" for sequence in sequences)
        family_counts: Counter[str] = Counter()
        raw_counts: Counter[str] = Counter()
        for trace, sequence in zip(cell_traces, sequences):
            family_counts.update(sequence)
            raw_counts.update(str(call.get("tool_name", "")) for call in trace.get("tool_calls", []))
        success_count = sum(1 for trace in cell_traces if _success(trace))
        summaries.append({
            "config_id": config_id,
            "task_id": task_id,
            "task_category": str(first["task_category"]),
            "harness": str(first["harness"]),
            "model_snapshot": str(first["model_snapshot"]),
            "n": len(cell_traces),
            "success_count": success_count,
            "success_rate": _round(success_count / len(cell_traces)),
            "mean_tool_calls": _round(_mean([len(trace.get("tool_calls", [])) for trace in cell_traces])),
            "mean_turns": _round(_mean([float(trace["turns"]) for trace in cell_traces if trace.get("turns") is not None])),
            "mean_wall_time_s": _round(_mean([float(trace["wall_time_s"]) for trace in cell_traces if trace.get("wall_time_s") is not None])),
            "repeat_stability": _round(_cell_stability(cell_traces)),
            "first_tool_families": dict(sorted(first_tools.items())),
            "tool_family_counts": dict(sorted(family_counts.items())),
            "raw_tool_counts": dict(sorted(raw_counts.items())),
            "trace_paths": [str(trace.get("_trace_path", "")) for trace in cell_traces],
        })
    return summaries


def _pair_contrast_family(left: dict[str, Any], right: dict[str, Any]) -> str:
    same_model = left["model_snapshot"] == right["model_snapshot"]
    same_harness = left["harness"] == right["harness"]
    if same_model and not same_harness:
        return "harness_same_model"
    if same_harness and not same_model:
        return "model_swap_same_harness"
    if not same_model and not same_harness:
        return "mixed_harness_model"
    return "same_config"


def _build_pair_observations(cells: list[dict[str, Any]], traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_cell = _group_by_cell(traces)
    task_ids = sorted({str(trace["task_id"]) for trace in traces})
    config_ids = sorted({int(trace["config_id"]) for trace in traces})
    config_meta = _config_lookup()
    observations: list[dict[str, Any]] = []

    for task_id in task_ids:
        category = next(str(trace["task_category"]) for trace in traces if str(trace["task_id"]) == task_id)
        for left_config, right_config in combinations(config_ids, 2):
            left = by_cell.get((left_config, task_id), [])
            right = by_cell.get((right_config, task_id), [])
            if not left or not right:
                continue
            left_sequences = [_family_sequence(trace) for trace in left]
            right_sequences = [_family_sequence(trace) for trace in right]
            jaccards = [
                _jaccard_similarity(left_seq, right_seq)
                for left_seq in left_sequences
                for right_seq in right_sequences
            ]
            sequence_divergences = [
                _sequence_divergence(left_seq, right_seq)
                for left_seq in left_sequences
                for right_seq in right_sequences
            ]
            left_success = sum(1 for trace in left if _success(trace)) / len(left)
            right_success = sum(1 for trace in right if _success(trace)) / len(right)
            left_meta = {**config_meta[left_config], "model_snapshot": left[0]["model_snapshot"]}
            right_meta = {**config_meta[right_config], "model_snapshot": right[0]["model_snapshot"]}
            observations.append({
                "task_id": task_id,
                "task_category": category,
                "task_split": "benchmark" if category == "benchmark" else "controlled",
                "config_pair": [left_config, right_config],
                "pair_label": f"c{left_config}-c{right_config}",
                "left": {
                    "config_id": left_config,
                    "harness": left[0]["harness"],
                    "model": left[0]["model_snapshot"],
                    "success_rate": _round(left_success),
                },
                "right": {
                    "config_id": right_config,
                    "harness": right[0]["harness"],
                    "model": right[0]["model_snapshot"],
                    "success_rate": _round(right_success),
                },
                "contrast_family": _pair_contrast_family(left_meta, right_meta),
                "mean_jaccard": _round(_mean(jaccards)),
                "mean_tool_set_disagreement": _round(1.0 - (_mean(jaccards) or 0.0)),
                "mean_sequence_disagreement": _round(_mean(sequence_divergences)),
                "success_gap": _round(abs(left_success - right_success)),
                "mean_failure_rate": _round(1.0 - ((left_success + right_success) / 2.0)),
                "n_repeat_pairs": len(jaccards),
            })
    return observations


def _aggregate_observations(
    observations: list[dict[str, Any]],
    group_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        grouped[tuple(observation[field] for field in group_fields)].append(observation)

    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        row = {field: value for field, value in zip(group_fields, key)}
        row.update({
            "n": len(group),
            "mean_jaccard": _round(_mean(float(item["mean_jaccard"]) for item in group)),
            "mean_tool_set_disagreement": _round(_mean(float(item["mean_tool_set_disagreement"]) for item in group)),
            "mean_sequence_disagreement": _round(_mean(float(item["mean_sequence_disagreement"]) for item in group)),
            "mean_success_gap": _round(_mean(float(item["success_gap"]) for item in group)),
            "mean_failure_rate": _round(_mean(float(item["mean_failure_rate"]) for item in group)),
        })
        rows.append(row)
    return rows


def _success_association(observations: list[dict[str, Any]]) -> dict[str, Any]:
    xs = [float(item["mean_sequence_disagreement"]) for item in observations]
    success_gaps = [float(item["success_gap"]) for item in observations]
    failure_rates = [float(item["mean_failure_rate"]) for item in observations]
    zero_gap = [item for item in observations if float(item["success_gap"]) == 0.0]
    nonzero_gap = [item for item in observations if float(item["success_gap"]) > 0.0]
    return {
        "unit": "config-pair x task observation",
        "n": len(observations),
        "pearson_sequence_disagreement_vs_success_gap": _round(_pearson(xs, success_gaps)),
        "pearson_sequence_disagreement_vs_mean_failure_rate": _round(_pearson(xs, failure_rates)),
        "mean_sequence_disagreement_when_success_gap_zero": _round(_mean(float(item["mean_sequence_disagreement"]) for item in zero_gap)),
        "mean_sequence_disagreement_when_success_gap_nonzero": _round(_mean(float(item["mean_sequence_disagreement"]) for item in nonzero_gap)),
        "success_gap_zero_n": len(zero_gap),
        "success_gap_nonzero_n": len(nonzero_gap),
    }


def _interaction_summary(pair_observations: list[dict[str, Any]]) -> dict[str, Any]:
    by_task_pair = {
        (observation["task_id"], tuple(observation["config_pair"])): observation
        for observation in pair_observations
    }
    model_swap_rows: list[dict[str, Any]] = []
    harness_swap_rows: list[dict[str, Any]] = []

    task_ids = sorted({observation["task_id"] for observation in pair_observations})
    for task_id in task_ids:
        opencode = by_task_pair.get((task_id, (2, 4)))
        hermes = by_task_pair.get((task_id, (3, 5)))
        if opencode and hermes:
            model_swap_rows.append({
                "task_id": task_id,
                "task_category": opencode["task_category"],
                "opencode_model_swap_sequence_disagreement": opencode["mean_sequence_disagreement"],
                "hermes_model_swap_sequence_disagreement": hermes["mean_sequence_disagreement"],
                "abs_difference": _round(abs(
                    float(opencode["mean_sequence_disagreement"]) - float(hermes["mean_sequence_disagreement"])
                )),
                "opencode_success_gap": opencode["success_gap"],
                "hermes_success_gap": hermes["success_gap"],
                "success_gap_abs_difference": _round(abs(float(opencode["success_gap"]) - float(hermes["success_gap"]))),
            })
        haiku_harness = by_task_pair.get((task_id, (2, 3)))
        gpt_harness = by_task_pair.get((task_id, (4, 5)))
        if haiku_harness and gpt_harness:
            harness_swap_rows.append({
                "task_id": task_id,
                "task_category": haiku_harness["task_category"],
                "haiku_opencode_hermes_sequence_disagreement": haiku_harness["mean_sequence_disagreement"],
                "gptmini_opencode_hermes_sequence_disagreement": gpt_harness["mean_sequence_disagreement"],
                "abs_difference": _round(abs(
                    float(haiku_harness["mean_sequence_disagreement"]) - float(gpt_harness["mean_sequence_disagreement"])
                )),
                "haiku_success_gap": haiku_harness["success_gap"],
                "gptmini_success_gap": gpt_harness["success_gap"],
                "success_gap_abs_difference": _round(abs(float(haiku_harness["success_gap"]) - float(gpt_harness["success_gap"]))),
            })

    return {
        "boundary": (
            "Interaction summaries use only the crossed OpenCode/Hermes cells "
            "(configs 2/3/4/5). Claude Code and Codex are anchor cells and are not "
            "available under both models."
        ),
        "model_swap_by_harness": {
            "n": len(model_swap_rows),
            "mean_abs_sequence_difference": _round(_mean(float(row["abs_difference"]) for row in model_swap_rows)),
            "mean_success_gap_abs_difference": _round(_mean(float(row["success_gap_abs_difference"]) for row in model_swap_rows)),
            "rows": model_swap_rows,
        },
        "harness_swap_by_model": {
            "n": len(harness_swap_rows),
            "mean_abs_sequence_difference": _round(_mean(float(row["abs_difference"]) for row in harness_swap_rows)),
            "mean_success_gap_abs_difference": _round(_mean(float(row["success_gap_abs_difference"]) for row in harness_swap_rows)),
            "rows": harness_swap_rows,
        },
    }


def _category_success_by_config(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        grouped[(int(trace["config_id"]), str(trace["task_category"]))].append(trace)
    rows: list[dict[str, Any]] = []
    for (config_id, category), group in sorted(grouped.items()):
        rows.append({
            "config_id": config_id,
            "category": category,
            "n": len(group),
            "success_count": sum(1 for trace in group if _success(trace)),
            "success_rate": _round(sum(1 for trace in group if _success(trace)) / len(group)),
        })
    return rows


def _category_summaries(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        grouped[str(trace["task_category"])].append(trace)
    rows: list[dict[str, Any]] = []
    for category, group in sorted(grouped.items()):
        rows.append({
            "category": category,
            "task_count": len({str(trace["task_id"]) for trace in group}),
            "n": len(group),
            "success_count": sum(1 for trace in group if _success(trace)),
            "success_rate": _round(sum(1 for trace in group if _success(trace)) / len(group)),
            "mean_tool_calls": _round(_mean(len(trace.get("tool_calls", [])) for trace in group)),
            "mean_wall_time_s": _round(_mean(float(trace["wall_time_s"]) for trace in group if trace.get("wall_time_s") is not None)),
        })
    return rows


def _task_summaries(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    tasks = _task_lookup()
    for trace in traces:
        grouped[str(trace["task_id"])].append(trace)

    rows: list[dict[str, Any]] = []
    for task_id, group in sorted(grouped.items()):
        task = tasks.get(task_id, {})
        by_config: list[dict[str, Any]] = []
        by_config_group: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for trace in group:
            by_config_group[int(trace["config_id"])].append(trace)
        for config_id, config_group in sorted(by_config_group.items()):
            by_config.append({
                "config_id": config_id,
                "success_count": sum(1 for trace in config_group if _success(trace)),
                "n": len(config_group),
                "success_rate": _round(sum(1 for trace in config_group if _success(trace)) / len(config_group)),
                "mean_tool_calls": _round(_mean(len(trace.get("tool_calls", [])) for trace in config_group)),
                "first_tool_families": dict(sorted(Counter(
                    (_family_sequence(trace)[0] if _family_sequence(trace) else "<none>")
                    for trace in config_group
                ).items())),
            })
        rows.append({
            "task_id": task_id,
            "task_category": str(group[0]["task_category"]),
            "source": task.get("source"),
            "tier": task.get("tier"),
            "provenance": task.get("provenance"),
            "n": len(group),
            "success_count": sum(1 for trace in group if _success(trace)),
            "success_rate": _round(sum(1 for trace in group if _success(trace)) / len(group)),
            "mean_tool_calls": _round(_mean(len(trace.get("tool_calls", [])) for trace in group)),
            "mean_wall_time_s": _round(_mean(float(trace["wall_time_s"]) for trace in group if trace.get("wall_time_s") is not None)),
            "success_rate_stdev_across_configs": _round(_population_stdev(float(item["success_rate"]) for item in by_config)),
            "by_config": by_config,
        })
    return rows


def _runtime_budget_key(trace: dict[str, Any]) -> str:
    budget = trace.get("runtime_budget") or {}
    fields = {
        key: budget.get(key)
        for key in ("max_output_tokens", "thinking_budget_tokens", "context_window_tokens", "effort_source")
        if key in budget
    }
    return json.dumps(fields, ensure_ascii=False, sort_keys=True)


def _environment_controls(traces: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        grouped[int(trace["config_id"])].append(trace)

    configs: list[dict[str, Any]] = []
    for config_id, group in sorted(grouped.items()):
        meta = _config_lookup()[config_id]
        runtime_budgets = Counter(_runtime_budget_key(trace) for trace in group)
        configs.append({
            "config_id": config_id,
            "harness": meta["harness"],
            "model_role": meta["model_role"],
            "provider": meta["provider"],
            "model_snapshots_observed": sorted({str(trace.get("model_snapshot")) for trace in group}),
            "harness_versions_observed": sorted({str(trace.get("harness_version")) for trace in group}),
            "reasoning_efforts_observed": sorted({str(trace.get("reasoning_effort")) for trace in group}),
            "runtime_budget_variants": [
                {"budget": json.loads(key), "count": count}
                for key, count in sorted(runtime_budgets.items())
            ],
            "env_lock_refs": sorted({str(trace.get("env_lock_ref")) for trace in group}),
            "raw_log_paths_present": sum(1 for trace in group if trace.get("raw_log_path")),
            "private_audit_paths_present": sum(1 for trace in group if trace.get("private_audit_path")),
            "n": len(group),
        })
    return {
        "host_boundary": "Validated on VPS; complete raw/private replay artifacts live under /data/harness-lab outside git.",
        "repo": str(paths.REPO),
        "configs": configs,
    }


def _agent_cards(traces: list[dict[str, Any]], cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    traces_by_config: dict[int, list[dict[str, Any]]] = defaultdict(list)
    cells_by_config: dict[int, list[dict[str, Any]]] = defaultdict(list)
    category_rates: dict[tuple[int, str], float] = {}
    for trace in traces:
        traces_by_config[int(trace["config_id"])].append(trace)
    for cell in cells:
        cells_by_config[int(cell["config_id"])].append(cell)
    for row in _category_success_by_config(traces):
        category_rates[(int(row["config_id"]), row["category"])] = float(row["success_rate"])

    cards: list[dict[str, Any]] = []
    for config_id in sorted(traces_by_config):
        group = traces_by_config[config_id]
        config = _config_lookup()[config_id]
        category_values = [
            category_rates[(config_id, category)]
            for category in sorted({trace["task_category"] for trace in group})
        ]
        failed = [trace for trace in group if not _success(trace)]
        governability_source = failed if failed else group
        values = {
            "fidelity": _mean(1.0 if _success(trace) else 0.0 for trace in group),
            "stability": _mean(
                float(cell["repeat_stability"])
                for cell in cells_by_config[config_id]
                if cell["repeat_stability"] is not None
            ),
            "robustness": min(category_values) if category_values else None,
            "actionability": _mean(_trace_evidence_score(trace) for trace in group),
            "governability": _mean(_trace_governability_score(trace) for trace in governability_source),
        }
        cards.append({
            "config_id": config_id,
            "harness": config["harness"],
            "model_role": config["model_role"],
            "model_snapshot": config["model_snapshot"],
            "n": len(group),
            "dimension_scale": "0-1; descriptive proxies for this controlled suite only",
            "dimensions": {key: _round(values[key]) for key in AGENT_CARD_DIMENSIONS},
            "category_success_rates": {
                category: _round(category_rates[(config_id, category)])
                for category in sorted({trace["task_category"] for trace in group})
            },
            "failed_trace_count": len(failed),
            "notes": {
                "robustness": "minimum category success rate within the current Python-only suite, not external robustness",
                "governability": "failed-run diagnosability coverage when failures exist; otherwise trace governance coverage",
            },
        })
    return cards


def _phase3_method_summary(attribution_path: str | Path | None = None) -> dict[str, Any]:
    path = _repo_path(attribution_path or Path("analysis") / "phase3" / "attribution-results.json")
    attribution = json.loads(path.read_text())
    labels = attribution.get("hci_labels") or []
    label_counts = Counter(str(label.get("factorial_label")) for label in labels)
    decision_counts = Counter(str(label.get("decision_kind")) for label in labels)
    confidence_counts = Counter(str(label.get("confidence")) for label in labels)
    agreement_counts = Counter(str((label.get("method_agreement") or {}).get("agreement_count")) for label in labels)
    cross: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    unanimous = 0
    for label in labels:
        factorial_label = str(label.get("factorial_label"))
        decision_kind = str(label.get("decision_kind"))
        cross[factorial_label][decision_kind] += 1
        if (label.get("method_agreement") or {}).get("unanimous") is True:
            unanimous += 1
    return {
        "source": _rel(path),
        "hci_label_count": len(labels),
        "label_distribution": dict(sorted(label_counts.items())),
        "decision_kind_distribution": dict(sorted(decision_counts.items())),
        "confidence_distribution": dict(sorted(confidence_counts.items())),
        "agreement_count_distribution": dict(sorted(agreement_counts.items())),
        "unanimous_count": unanimous,
        "unanimous_rate": _round(unanimous / len(labels) if labels else None),
        "factorial_label_by_decision_kind": {
            label: dict(sorted(row.items()))
            for label, row in sorted(cross.items())
        },
        "method_boundary": attribution.get("method_boundary"),
    }


def _load_phase3_hci_labels() -> list[dict[str, Any]]:
    path = paths.REPO / "analysis" / "phase3" / "hci-ground-truth-labels.json"
    payload = json.loads(path.read_text())
    return list(payload.get("labels") or [])


def _summarize_trace_ref(trace_ref: str) -> dict[str, Any]:
    trace = json.loads((paths.REPO / trace_ref).read_text())
    sequence = _family_sequence(trace)
    return {
        "trace": trace_ref,
        "config_id": int(trace["config_id"]),
        "repeat_index": int(trace["repeat_index"]),
        "harness": trace["harness"],
        "model_snapshot": trace["model_snapshot"],
        "success": _success(trace),
        "tool_count": len(sequence),
        "tool_family_sequence": sequence,
        "first_tool_family": sequence[0] if sequence else "<none>",
        "raw_log_path": trace.get("raw_log_path"),
        "private_audit_path": trace.get("private_audit_path"),
        "grader_detail_present": bool((trace.get("outcome") or {}).get("grader_detail")),
    }


def _summarize_label_side(side: dict[str, Any]) -> dict[str, Any]:
    traces = [_summarize_trace_ref(str(ref)) for ref in side.get("baseline_traces", [])]
    sequence_counts = Counter(tuple(trace["tool_family_sequence"]) for trace in traces)
    first_tools = Counter(trace["first_tool_family"] for trace in traces)
    return {
        "config": side.get("config"),
        "harness": side.get("harness"),
        "model": side.get("model"),
        "baseline_traces": traces,
        "success_count": sum(1 for trace in traces if trace["success"]),
        "n": len(traces),
        "success_rate": _round(sum(1 for trace in traces if trace["success"]) / len(traces) if traces else None),
        "first_tool_families": dict(sorted(first_tools.items())),
        "dominant_tool_family_sequence": list(sequence_counts.most_common(1)[0][0]) if sequence_counts else [],
    }


def _short_prompt(task_id: str, max_chars: int = 260) -> str:
    task = _task_lookup().get(task_id, {})
    prompt = " ".join(str(task.get("prompt", "")).split())
    if len(prompt) <= max_chars:
        return prompt
    return prompt[: max_chars - 3].rstrip() + "..."


def _case_selection(labels: list[dict[str, Any]], max_cases: int = 6) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    original_order = {str(label.get("label_id")): index for index, label in enumerate(labels)}

    def add_best(predicate: Any, preferred_categories: tuple[str, ...] = ()) -> None:
        candidates = [
            label for label in labels
            if str(label.get("label_id")) not in selected_ids and predicate(label)
        ]
        if not candidates:
            return
        category_counts = Counter(str(label.get("task_category")) for label in selected)
        preference = {category: index for index, category in enumerate(preferred_categories)}
        candidates.sort(key=lambda label: (
            category_counts[str(label.get("task_category"))],
            preference.get(str(label.get("task_category")), len(preference)),
            original_order[str(label.get("label_id"))],
        ))
        chosen = candidates[0]
        selected.append(chosen)
        selected_ids.add(str(chosen.get("label_id")))

    add_best(
        lambda label: label.get("factorial_label") == "harness_main_effect" and label.get("decision_kind") == "initial_tool_strategy",
        ("add_tests", "add_logging", "benchmark", "bug_fix"),
    )
    add_best(
        lambda label: label.get("factorial_label") == "model_main_effect" and label.get("decision_kind") == "initial_tool_strategy",
        ("benchmark", "add_logging", "add_tests", "bug_fix"),
    )
    add_best(
        lambda label: label.get("decision_kind") == "semantic_output_convention" or label.get("factorial_label") == "interaction",
        ("bug_fix", "add_tests", "benchmark", "add_logging"),
    )
    add_best(
        lambda label: label.get("decision_kind") == "task_success_gap",
        ("add_tests", "benchmark", "bug_fix", "add_logging"),
    )
    add_best(
        lambda label: label.get("decision_kind") == "task_success_gap",
        ("benchmark", "add_tests", "bug_fix", "add_logging"),
    )
    add_best(
        lambda label: label.get("task_category") == "add_logging",
        ("add_logging",),
    )

    for label in labels:
        if len(selected) >= max_cases:
            break
        label_id = str(label.get("label_id"))
        if label_id not in selected_ids:
            selected.append(label)
            selected_ids.add(label_id)

    return selected[:max_cases]


def _study_questions() -> list[dict[str, Any]]:
    return [
        {
            "metric": "clarity",
            "item": "I can explain what differed between the two agent runs.",
            "scale": "1-5 Likert",
        },
        {
            "metric": "trust_calibration",
            "item": "My trust in the agent result matches the evidence and limitations shown.",
            "scale": "1-5 Likert",
        },
        {
            "metric": "verification_intention_or_action_choice",
            "item": "What would you do next?",
            "scale": "choice: accept / inspect evidence / rerun / ask for more information / reject",
        },
        {
            "metric": "perceived_safety_control",
            "item": "I feel able to catch or recover from an agent mistake in this case.",
            "scale": "1-5 Likert",
        },
        {
            "metric": "cognitive_load_effort",
            "item": "This presentation was understandable without excessive effort.",
            "scale": "1-5 Likert",
        },
        {
            "metric": "qualitative_feedback",
            "item": "What evidence helped, what was confusing, and what would change your decision?",
            "scale": "open text",
        },
    ]


def build_hci_case_pack(analysis: dict[str, Any], max_cases: int = 6) -> dict[str, Any]:
    """Build HCI study-ready cases from Phase 3 labels without relabeling ground truth."""
    labels = _case_selection(_load_phase3_hci_labels(), max_cases=max_cases)
    cases: list[dict[str, Any]] = []
    for index, label in enumerate(labels, start=1):
        left = _summarize_label_side(label.get("left") or {})
        right = _summarize_label_side(label.get("right") or {})
        case_id = f"HCI-PH4-{index:02d}"
        evidence_note = (
            f"M1-M4 agreement: {(label.get('method_agreement') or {}).get('agreement_count')}/"
            f"{(label.get('method_agreement') or {}).get('method_count')} "
            f"for {label.get('factorial_label')}."
        )
        limitation_note = (
            "This case is selected from high-divergence Phase 3 labels and should be used "
            "as an HCI presentation case, not as a prevalence estimate over all tasks."
        )
        cases.append({
            "case_id": case_id,
            "label_id": label.get("label_id"),
            "seed_id": label.get("seed_id"),
            "task_id": label.get("task_id"),
            "task_category": label.get("task_category"),
            "task_prompt_excerpt": _short_prompt(str(label.get("task_id"))),
            "factorial_label": label.get("factorial_label"),
            "decision_kind": label.get("decision_kind"),
            "detail_label": label.get("detail_label"),
            "confidence": label.get("confidence"),
            "method_agreement": label.get("method_agreement"),
            "left": left,
            "right": right,
            "condition_a_summary_only": {
                "purpose": "Compact summary-only view for comparison condition A.",
                "fields": {
                    "task": label.get("task_id"),
                    "left_outcome": f"{left['success_count']}/{left['n']} successful formal repeats",
                    "right_outcome": f"{right['success_count']}/{right['n']} successful formal repeats",
                    "left_tool_sequence": left["dominant_tool_family_sequence"],
                    "right_tool_sequence": right["dominant_tool_family_sequence"],
                },
            },
            "condition_b_evidence_limitation_action": {
                "purpose": "Evidence + limitation + action view for comparison condition B.",
                "evidence": [
                    evidence_note,
                    f"Left traces: {[trace['trace'] for trace in left['baseline_traces']]}.",
                    f"Right traces: {[trace['trace'] for trace in right['baseline_traces']]}.",
                    f"Private replay refs exist on VPS for all displayed traces: left={left['n']}, right={right['n']}.",
                ],
                "limitation": limitation_note,
                "suggested_verification_action": (
                    "Inspect the listed trace summaries and, when needed, the VPS private audit/raw replay refs "
                    "before accepting the agent outcome."
                ),
            },
            "measurement_items": _study_questions(),
        })

    coverage = {
        "case_count": len(cases),
        "factorial_labels": dict(sorted(Counter(str(case["factorial_label"]) for case in cases).items())),
        "decision_kinds": dict(sorted(Counter(str(case["decision_kind"]) for case in cases).items())),
        "task_categories": dict(sorted(Counter(str(case["task_category"]) for case in cases).items())),
        "required_plan_coverage": {
            "harness_main_effect_initial_tool_strategy": any(
                case["factorial_label"] == "harness_main_effect" and case["decision_kind"] == "initial_tool_strategy"
                for case in cases
            ),
            "model_main_effect_initial_tool_strategy": any(
                case["factorial_label"] == "model_main_effect" and case["decision_kind"] == "initial_tool_strategy"
                for case in cases
            ),
            "interaction_or_semantic_case": any(
                case["factorial_label"] == "interaction" or case["decision_kind"] == "semantic_output_convention"
                for case in cases
            ),
            "task_success_gap_case": any(case["decision_kind"] == "task_success_gap" for case in cases),
        },
    }
    return {
        "schema_version": 1,
        "phase": "phase4_hci_case_pack",
        "source": {
            "hci_labels": "analysis/phase3/hci-ground-truth-labels.json",
            "phase4_metrics": DEFAULT_ANALYSIS_PATH.as_posix(),
            "selection": "Representative 4-6 case mix required by HCI human-study plan.",
        },
        "boundary": analysis["hci_boundary"],
        "procedure_support": {
            "participants": "small voluntary convenience sample, target n=6-10 MIS graduate students or peers",
            "design": "within-subject comparison, counterbalance condition order if feasible",
            "condition_a": "summary-only",
            "condition_b": "evidence + limitation + action/checkpoint cues",
            "ethics": "voluntary, anonymous/code-based, no grade penalty, raw individual responses not published",
        },
        "coverage": coverage,
        "cases": cases,
    }


def _split_summary(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, categories in TASK_SPLITS.items():
        group = [trace for trace in traces if trace["task_category"] in categories]
        if not group:
            continue
        rows.append({
            "split": split,
            "categories": sorted(categories),
            "n": len(group),
            "success_count": sum(1 for trace in group if _success(trace)),
            "success_rate": _round(sum(1 for trace in group if _success(trace)) / len(group)),
            "mean_tool_calls": _round(_mean(len(trace.get("tool_calls", [])) for trace in group)),
        })
    return rows


def _overall_summary(traces: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "formal_trace_count": len(traces),
        "formal_repeats": list(FORMAL_REPEATS),
        "config_count": len({int(trace["config_id"]) for trace in traces}),
        "task_count": len({str(trace["task_id"]) for trace in traces}),
        "success_count": sum(1 for trace in traces if _success(trace)),
        "success_rate": _round(sum(1 for trace in traces if _success(trace)) / len(traces) if traces else None),
        "mean_tool_calls": _round(_mean(len(trace.get("tool_calls", [])) for trace in traces)),
        "mean_wall_time_s": _round(_mean(float(trace["wall_time_s"]) for trace in traces if trace.get("wall_time_s") is not None)),
        "task_splits": _split_summary(traces),
    }


def build_phase4_analysis(
    traces: list[dict[str, Any]] | None = None,
    run_readiness_gate: bool = True,
) -> dict[str, Any]:
    """Build Phase 4 metrics without writing files."""
    readiness = validate_phase4_readiness() if run_readiness_gate else {"ok": True, "skipped": True}
    if not readiness.get("ok"):
        raise ValueError("Phase 4 readiness gate failed; refusing to build analysis")

    traces = traces if traces is not None else load_formal_traces()
    cells = _summarize_cells(traces)
    pair_observations = _build_pair_observations(cells, traces)
    pair_by_config = _aggregate_observations(pair_observations, ("pair_label",))
    contrast_summary = _aggregate_observations(pair_observations, ("contrast_family",))
    contrast_by_split = _aggregate_observations(pair_observations, ("contrast_family", "task_split"))
    contrast_by_category = _aggregate_observations(pair_observations, ("contrast_family", "task_category"))
    pair_by_category = _aggregate_observations(pair_observations, ("pair_label", "task_category"))
    category_config = _category_success_by_config(traces)
    phase3_summary = _phase3_method_summary()
    agent_cards = _agent_cards(traces, cells)

    return {
        "schema_version": 1,
        "phase": "phase4_metrics_analysis",
        "source": {
            "repo": str(paths.REPO),
            "trace_root": "traces",
            "formal_repeats": list(FORMAL_REPEATS),
            "phase3_attribution": "analysis/phase3/attribution-results.json",
            "phase3_hci_labels": "analysis/phase3/hci-ground-truth-labels.json",
            "readiness_gate": "runner phase4-ready",
            "data_boundary": (
                "Statistics use formal Phase 2 repeats 1-3 only. Pilot repeat 0 "
                "and Phase 3 counterfactual repeats are excluded from baseline statistics."
            ),
        },
        "readiness": readiness,
        "config_metadata": [_config_lookup()[config_id] for config_id in sorted(_config_lookup())],
        "environment_controls": _environment_controls(traces),
        "overall": _overall_summary(traces),
        "category_summaries": _category_summaries(traces),
        "task_summaries": _task_summaries(traces),
        "cell_summaries": cells,
        "category_success_by_config": category_config,
        "pairwise": {
            "unit": "config-pair x task, averaged over 3x3 repeat comparisons",
            "observations": pair_observations,
            "by_config_pair": pair_by_config,
            "contrast_summary": contrast_summary,
            "contrast_by_split": contrast_by_split,
            "contrast_by_category": contrast_by_category,
            "pair_by_category": pair_by_category,
        },
        "success_association": _success_association(pair_observations),
        "factorial_decomposition": {
            "contrast_summary": contrast_summary,
            "contrast_by_split": contrast_by_split,
            "interaction_overlap_only": _interaction_summary(pair_observations),
            "phase3_selected_decision_labels": {
                "boundary": "Selected high-divergence Phase 3 decision points; not a prevalence estimate over all Phase 2 traces.",
                "label_distribution": phase3_summary["label_distribution"],
            },
        },
        "phase3_method_consistency": phase3_summary,
        "agent_cards": agent_cards,
        "hci_boundary": {
            "human_study_status": "not_claimed_in_phase4_metrics",
            "note": (
                "These XAI metrics provide cases and evidence for HCI materials. "
                "They do not replace the required human study on understanding, "
                "trust calibration, verification behavior, safety/control, and cognitive load."
            ),
        },
    }


def build_requirements_traceability(
    analysis: dict[str, Any],
    figures: dict[str, str],
    hci_case_pack_path: str,
) -> dict[str, Any]:
    """Map teacher/HCI requirements to concrete Phase 4 artifacts."""
    rows = [
        {
            "requirement": "Explain research question, method, task sampling, environment controls, results, limitations, and implications for MIS classroom review.",
            "source": "phase4 guardrails / HCI noon requirements",
            "phase4_artifacts": [
                DEFAULT_REPORT_PATH.as_posix(),
                DEFAULT_SUPPORT_REPORT_PATH.as_posix(),
                DEFAULT_ANALYSIS_PATH.as_posix(),
            ],
            "evidence_fields": ["overall", "task_summaries", "environment_controls", "factorial_decomposition"],
            "status": "covered_by_phase4_artifacts",
        },
        {
            "requirement": "Keep XAI findings separate from HCI evaluation; do not present xAI metrics alone as HCI evaluation.",
            "source": "phase4 guardrails",
            "phase4_artifacts": [DEFAULT_REPORT_PATH.as_posix(), hci_case_pack_path],
            "evidence_fields": ["hci_boundary", "phase3_method_consistency"],
            "status": "covered_with_boundary_note",
        },
        {
            "requirement": "Required HCI human study with participants, two presentation styles, clarity/trust/verification/safety/load metrics, qualitative feedback, and ethics.",
            "source": "HCI human study plan / HCI noon requirements",
            "phase4_artifacts": [hci_case_pack_path, DEFAULT_SUPPORT_REPORT_PATH.as_posix()],
            "evidence_fields": ["hci_case_pack.procedure_support", "hci_case_pack.cases[].measurement_items"],
            "status": "materials_prepared_human_responses_still_required",
        },
        {
            "requirement": "Fixed test environment, versions, model snapshots, provider route, reasoning effort, token/thinking/context-window settings, raw logs outside git.",
            "source": "HCI noon requirements / design spec",
            "phase4_artifacts": [DEFAULT_ANALYSIS_PATH.as_posix(), "ENVIRONMENT.lock.md"],
            "evidence_fields": ["environment_controls", "readiness.phase2_gate"],
            "status": "covered_by_vps_gate_and_trace_fields",
        },
        {
            "requirement": "Use charts/tables/process evidence rather than long prose only.",
            "source": "HCI noon requirements",
            "phase4_artifacts": list(figures.values()) + [DEFAULT_SUPPORT_REPORT_PATH.as_posix()],
            "evidence_fields": ["figures", "category_summaries", "agent_cards"],
            "status": "covered_with_generated_figures",
        },
        {
            "requirement": "Non-overclaim: current data support only this controlled 20-task suite.",
            "source": "phase4 guardrails",
            "phase4_artifacts": [DEFAULT_REPORT_PATH.as_posix(), DEFAULT_SUPPORT_REPORT_PATH.as_posix()],
            "evidence_fields": ["source.data_boundary", "hci_boundary"],
            "status": "covered_with_limitations",
        },
        {
            "requirement": "Analyze benchmark tasks separately from controlled software-engineering tasks.",
            "source": "phase4 guardrails / HCI noon requirements",
            "phase4_artifacts": [DEFAULT_ANALYSIS_PATH.as_posix(), DEFAULT_REPORT_PATH.as_posix()],
            "evidence_fields": ["overall.task_splits", "pairwise.contrast_by_split", "category_summaries"],
            "status": "covered_with_split_tables",
        },
        {
            "requirement": "Task sampling, difficulty calibration, harness-affinity bias, and robustness gaps must be explicit.",
            "source": "phase4 guardrails / HCI noon requirements",
            "phase4_artifacts": [DEFAULT_REPORT_PATH.as_posix(), DEFAULT_SUPPORT_REPORT_PATH.as_posix()],
            "evidence_fields": ["task_summaries", "category_summaries", "reporting_limitations"],
            "status": "covered_with_limitations_and_task_metadata",
        },
        {
            "requirement": "Provide concrete cases so peers can understand risks and evidence dependencies.",
            "source": "XAI/HCI peer feedback",
            "phase4_artifacts": [hci_case_pack_path, DEFAULT_SUPPORT_REPORT_PATH.as_posix()],
            "evidence_fields": ["hci_case_pack.cases", "pairwise.observations"],
            "status": "covered_with_case_pack",
        },
        {
            "requirement": "Agent-card matrix across fidelity, stability, robustness, actionability, governability.",
            "source": "design spec Phase 4",
            "phase4_artifacts": [DEFAULT_ANALYSIS_PATH.as_posix(), figures.get("agent_card_matrix", "")],
            "evidence_fields": ["agent_cards"],
            "status": "covered_as_descriptive_proxy",
        },
    ]
    return {
        "schema_version": 1,
        "phase": "phase4_teacher_requirements_traceability",
        "boundary": {
            "vps_authority": str(paths.REPO),
            "public_artifacts": "Sanitized summaries and generated analysis artifacts; full private/raw replay remains on VPS.",
            "human_study": "Phase 4 prepares materials; human response collection remains a separate HCI execution step.",
        },
        "coverage_summary": {
            "requirements": len(rows),
            "covered": sum(1 for row in rows if row["status"].startswith("covered")),
            "materials_prepared_human_responses_still_required": sum(
                1 for row in rows if row["status"] == "materials_prepared_human_responses_still_required"
            ),
        },
        "rows": rows,
    }


def _slide_support_pack(analysis: dict[str, Any], hci_case_pack: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "slide": 1,
            "title": "Research question and classroom framing",
            "supports": ["phase4 guardrails audience framing", "source.data_boundary"],
        },
        {
            "slide": 2,
            "title": "Method overview before results",
            "supports": ["formal repeats 1-3", "task suite 5 categories x 4 tasks", "VPS environment controls"],
        },
        {
            "slide": 3,
            "title": "Fixed environment and trace evidence chain",
            "supports": ["environment_controls", "ENVIRONMENT.lock.md", "readiness.phase2_gate"],
        },
        {
            "slide": 4,
            "title": "Task sampling and difficulty calibration",
            "supports": ["category_summaries", "task_summaries", "hidden grader boundary"],
        },
        {
            "slide": 5,
            "title": "Overall success and tool-use overview",
            "supports": ["overall", "config summary table"],
        },
        {
            "slide": 6,
            "title": "Controlled vs benchmark split",
            "supports": ["overall.task_splits", "category_summaries"],
        },
        {
            "slide": 7,
            "title": "Tool-family Jaccard matrix",
            "supports": ["figures.jaccard_matrix", "pairwise.by_config_pair"],
        },
        {
            "slide": 8,
            "title": "Disagreement and success-gap relationship",
            "supports": ["figures.disagreement_success_scatter", "success_association"],
        },
        {
            "slide": 9,
            "title": "Factorial decomposition with anchor-cell boundary",
            "supports": ["factorial_decomposition", "figures.factorial_contrast_bars"],
        },
        {
            "slide": 10,
            "title": "Phase 3 attribution and M1-M4 consistency",
            "supports": ["phase3_method_consistency", "figures.method_consistency"],
        },
        {
            "slide": 11,
            "title": "Concrete HCI case examples",
            "supports": [case["case_id"] for case in hci_case_pack["cases"][:2]],
        },
        {
            "slide": 12,
            "title": "HCI study design",
            "supports": ["hci_case_pack.procedure_support", "measurement_items"],
        },
        {
            "slide": 13,
            "title": "Agent-card governance matrix",
            "supports": ["agent_cards", "figures.agent_card_matrix"],
        },
        {
            "slide": 14,
            "title": "Limitations and non-overclaim",
            "supports": ["Python-only suite", "benchmark split", "Phase 3 selected-case boundary"],
        },
        {
            "slide": 15,
            "title": "Implications and next steps",
            "supports": ["HCI human response collection", "cross-language robustness future work"],
        },
    ]




def _svg_escape(text: Any) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _color_lerp(start: tuple[int, int, int], end: tuple[int, int, int], value: float) -> str:
    value = max(0.0, min(1.0, value))
    rgb = [round(s + (e - s) * value) for s, e in zip(start, end)]
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


def _svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202124}.title{font-size:18px;font-weight:700}.axis{font-size:12px;fill:#5f6368}.label{font-size:12px}.value{font-size:11px;fill:#3c4043}</style>',
    ]


def _write_svg(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines + ["</svg>", ""]))


def _render_jaccard_matrix(analysis: dict[str, Any], path: Path) -> None:
    labels = [_config_label(config["config_id"]) for config in analysis["config_metadata"]]
    config_ids = [config["config_id"] for config in analysis["config_metadata"]]
    by_pair = {tuple(row["pair_label"].removeprefix("c").split("-c")): row for row in analysis["pairwise"]["by_config_pair"]}
    by_pair_int: dict[tuple[int, int], dict[str, Any]] = {}
    for row in analysis["pairwise"]["by_config_pair"]:
        left, right = row["pair_label"].replace("c", "").split("-")
        by_pair_int[(int(left), int(right))] = row
    width = 920
    height = 720
    left_pad = 210
    top_pad = 120
    cell = 78
    lines = _svg_header(width, height)
    lines.append('<text x="40" y="42" class="title">Mean tool-family Jaccard similarity by config pair</text>')
    lines.append('<text x="40" y="66" class="axis">Formal repeats 1-3 only; values average config-pair x task 3x3 repeat comparisons.</text>')
    for i, label in enumerate(labels):
        x = left_pad + i * cell + cell / 2
        lines.append(f'<text x="{x}" y="104" class="axis" text-anchor="middle">{_svg_escape("c" + str(config_ids[i]))}</text>')
        y = top_pad + i * cell + cell / 2 + 4
        lines.append(f'<text x="38" y="{y}" class="label">{_svg_escape(label)}</text>')
    for row_idx, left_id in enumerate(config_ids):
        for col_idx, right_id in enumerate(config_ids):
            x = left_pad + col_idx * cell
            y = top_pad + row_idx * cell
            if left_id == right_id:
                value = 1.0
            else:
                key = (min(left_id, right_id), max(left_id, right_id))
                value = float(by_pair_int[key]["mean_jaccard"])
            fill = _color_lerp((247, 250, 252), (37, 99, 235), value)
            text_color = "#ffffff" if value > 0.58 else "#202124"
            lines.append(f'<rect x="{x}" y="{y}" width="{cell - 4}" height="{cell - 4}" rx="4" fill="{fill}" stroke="#d8dee9"/>')
            lines.append(f'<text x="{x + cell / 2 - 2}" y="{y + cell / 2 + 4}" class="value" text-anchor="middle" fill="{text_color}">{value:.2f}</text>')
    _write_svg(path, lines)


def _render_scatter(analysis: dict[str, Any], path: Path) -> None:
    observations = analysis["pairwise"]["observations"]
    width = 920
    height = 620
    left = 90
    right = 40
    top = 70
    bottom = 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    colors = {
        "bug_fix": "#2563eb",
        "rename": "#059669",
        "add_tests": "#d97706",
        "add_logging": "#7c3aed",
        "benchmark": "#dc2626",
    }
    lines = _svg_header(width, height)
    lines.append('<text x="40" y="42" class="title">Sequence disagreement vs success gap</text>')
    lines.append('<text x="40" y="66" class="axis">Each point is one config pair on one task; y is absolute success-rate gap.</text>')
    for tick in range(0, 6):
        x = left + plot_w * tick / 5
        y = top + plot_h * tick / 5
        lines.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#edf2f7"/>')
        lines.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#edf2f7"/>')
        lines.append(f'<text x="{x}" y="{top + plot_h + 24}" class="axis" text-anchor="middle">{tick / 5:.1f}</text>')
        lines.append(f'<text x="{left - 14}" y="{top + plot_h - plot_h * tick / 5 + 4}" class="axis" text-anchor="end">{tick / 5:.1f}</text>')
    lines.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#5f6368"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#5f6368"/>')
    lines.append(f'<text x="{left + plot_w / 2}" y="{height - 28}" class="axis" text-anchor="middle">mean sequence disagreement</text>')
    lines.append(f'<text x="24" y="{top + plot_h / 2}" class="axis" transform="rotate(-90 24 {top + plot_h / 2})" text-anchor="middle">success gap</text>')
    for item in observations:
        x_value = max(0.0, min(1.0, float(item["mean_sequence_disagreement"])))
        y_value = max(0.0, min(1.0, float(item["success_gap"])))
        x = left + x_value * plot_w
        y = top + (1.0 - y_value) * plot_h
        color = colors.get(item["task_category"], "#475569")
        lines.append(f'<circle cx="{x}" cy="{y}" r="4.2" fill="{color}" fill-opacity="0.68"><title>{_svg_escape(item["pair_label"] + " " + item["task_id"])}</title></circle>')
    legend_x = width - 190
    for idx, (category, color) in enumerate(colors.items()):
        y = 100 + idx * 24
        lines.append(f'<rect x="{legend_x}" y="{y - 10}" width="12" height="12" rx="2" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 20}" y="{y}" class="axis">{_svg_escape(category)}</text>')
    _write_svg(path, lines)


def _render_factorial_bars(analysis: dict[str, Any], path: Path) -> None:
    rows = analysis["factorial_decomposition"]["contrast_summary"]
    rows = sorted(rows, key=lambda row: row["contrast_family"])
    width = 920
    height = 360
    left = 260
    top = 80
    bar_h = 28
    gap = 34
    lines = _svg_header(width, height)
    lines.append('<text x="40" y="42" class="title">Mean sequence disagreement by contrast family</text>')
    lines.append('<text x="40" y="66" class="axis">Harness/model contrast families are descriptive; mixed pairs are not interpreted causally.</text>')
    for idx, row in enumerate(rows):
        y = top + idx * gap
        value = float(row["mean_sequence_disagreement"])
        width_px = value * 560
        color = {
            "harness_same_model": "#2563eb",
            "model_swap_same_harness": "#059669",
            "mixed_harness_model": "#d97706",
        }.get(row["contrast_family"], "#64748b")
        lines.append(f'<text x="40" y="{y + 19}" class="label">{_svg_escape(row["contrast_family"])}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="560" height="{bar_h}" rx="4" fill="#f1f5f9"/>')
        lines.append(f'<rect x="{left}" y="{y}" width="{width_px}" height="{bar_h}" rx="4" fill="{color}"/>')
        lines.append(f'<text x="{left + width_px + 8}" y="{y + 19}" class="value">{value:.3f} (n={row["n"]})</text>')
    _write_svg(path, lines)


def _render_method_consistency(analysis: dict[str, Any], path: Path) -> None:
    matrix = analysis["phase3_method_consistency"]["factorial_label_by_decision_kind"]
    row_labels = sorted(matrix)
    col_labels = sorted({col for row in matrix.values() for col in row})
    width = 920
    height = 400
    left = 240
    top = 100
    cell_w = 170
    cell_h = 56
    max_value = max([value for row in matrix.values() for value in row.values()] or [1])
    lines = _svg_header(width, height)
    lines.append('<text x="40" y="42" class="title">Phase 3 method-consistency label matrix</text>')
    lines.append('<text x="40" y="66" class="axis">Counts of HCI labels by factorial attribution and decision kind.</text>')
    for idx, col in enumerate(col_labels):
        x = left + idx * cell_w + cell_w / 2
        lines.append(f'<text x="{x}" y="88" class="axis" text-anchor="middle">{_svg_escape(col)}</text>')
    for row_idx, row_label in enumerate(row_labels):
        y = top + row_idx * cell_h
        lines.append(f'<text x="40" y="{y + 34}" class="label">{_svg_escape(row_label)}</text>')
        for col_idx, col in enumerate(col_labels):
            value = int(matrix[row_label].get(col, 0))
            x = left + col_idx * cell_w
            fill = _color_lerp((248, 250, 252), (124, 58, 237), value / max_value if max_value else 0.0)
            lines.append(f'<rect x="{x}" y="{y}" width="{cell_w - 6}" height="{cell_h - 6}" rx="4" fill="{fill}" stroke="#e2e8f0"/>')
            lines.append(f'<text x="{x + cell_w / 2 - 3}" y="{y + 33}" class="value" text-anchor="middle">{value}</text>')
    summary = analysis["phase3_method_consistency"]
    lines.append(f'<text x="40" y="{height - 34}" class="axis">Unanimous M1-M4 labels: {summary["unanimous_count"]}/{summary["hci_label_count"]} ({summary["unanimous_rate"]:.2f})</text>')
    _write_svg(path, lines)


def _render_agent_card_matrix(analysis: dict[str, Any], path: Path) -> None:
    cards = analysis["agent_cards"]
    width = 980
    height = 560
    left = 230
    top = 110
    cell_w = 130
    cell_h = 58
    lines = _svg_header(width, height)
    lines.append('<text x="40" y="42" class="title">Agent-card matrix (descriptive proxies)</text>')
    lines.append('<text x="40" y="66" class="axis">Scale 0-1 within this controlled Python suite; robustness is not external robustness.</text>')
    for idx, dim in enumerate(AGENT_CARD_DIMENSIONS):
        x = left + idx * cell_w + cell_w / 2
        lines.append(f'<text x="{x}" y="92" class="axis" text-anchor="middle">{_svg_escape(dim)}</text>')
    for row_idx, card in enumerate(cards):
        y = top + row_idx * cell_h
        lines.append(f'<text x="40" y="{y + 34}" class="label">{_svg_escape(_config_label(card["config_id"]))}</text>')
        for col_idx, dim in enumerate(AGENT_CARD_DIMENSIONS):
            value = float(card["dimensions"][dim])
            x = left + col_idx * cell_w
            fill = _color_lerp((255, 247, 237), (22, 163, 74), value)
            lines.append(f'<rect x="{x}" y="{y}" width="{cell_w - 6}" height="{cell_h - 6}" rx="4" fill="{fill}" stroke="#e2e8f0"/>')
            lines.append(f'<text x="{x + cell_w / 2 - 3}" y="{y + 33}" class="value" text-anchor="middle">{value:.2f}</text>')
    _write_svg(path, lines)


def write_phase4_figures(
    analysis: dict[str, Any],
    figure_dir: str | Path = DEFAULT_FIGURE_DIR,
) -> dict[str, str]:
    figure_root = _repo_path(figure_dir)
    figure_root.mkdir(parents=True, exist_ok=True)
    paths_by_name = {name: figure_root / filename for name, filename in FIGURE_FILES.items()}
    # Publication-quality rendering is delegated to runner.figures (matplotlib).
    # The legacy hand-rolled _render_* SVG helpers are kept for reference only.
    from runner import figures as _figs
    _figs.render_phase4_figures(analysis, figure_root)
    return {name: _rel(path) for name, path in paths_by_name.items()}


def _format_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _table(rows: list[list[Any]]) -> list[str]:
    if not rows:
        return []
    header = rows[0]
    lines = [
        "| " + " | ".join(str(cell) for cell in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |")
    return lines


def render_phase4_report(analysis: dict[str, Any]) -> str:
    overall = analysis["overall"]
    assoc = analysis["success_association"]
    phase3 = analysis["phase3_method_consistency"]
    figures = analysis.get("figures", {})
    config_summary: list[list[Any]] = [["Config", "Harness", "Model", "Success", "Tool calls", "Wall time", "Stability"]]
    cells_by_config: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cell in analysis["cell_summaries"]:
        cells_by_config[int(cell["config_id"])].append(cell)
    config_meta = {config["config_id"]: config for config in analysis["config_metadata"]}
    traces_by_config_n = {card["config_id"]: card["n"] for card in analysis["agent_cards"]}
    success_by_config: dict[int, float] = {}
    for card in analysis["agent_cards"]:
        success_by_config[int(card["config_id"])] = float(card["dimensions"]["fidelity"])
    for config_id in sorted(cells_by_config):
        meta = config_meta[config_id]
        config_summary.append([
            f"c{config_id}",
            meta["harness"],
            meta["model_role"],
            f"{success_by_config[config_id]:.3f} ({traces_by_config_n[config_id]} runs)",
            _format_rate(_mean(float(cell["mean_tool_calls"]) for cell in cells_by_config[config_id])),
            _format_rate(_mean(float(cell["mean_wall_time_s"]) for cell in cells_by_config[config_id] if cell["mean_wall_time_s"] is not None)),
            _format_rate(_mean(float(cell["repeat_stability"]) for cell in cells_by_config[config_id] if cell["repeat_stability"] is not None)),
        ])

    contrast_rows = [["Contrast", "n", "Jaccard", "Seq disagreement", "Success gap", "Failure rate"]]
    for row in analysis["factorial_decomposition"]["contrast_summary"]:
        contrast_rows.append([
            row["contrast_family"],
            row["n"],
            f"{float(row['mean_jaccard']):.3f}",
            f"{float(row['mean_sequence_disagreement']):.3f}",
            f"{float(row['mean_success_gap']):.3f}",
            f"{float(row['mean_failure_rate']):.3f}",
        ])

    agent_rows = [["Config", *AGENT_CARD_DIMENSIONS]]
    for card in analysis["agent_cards"]:
        agent_rows.append([
            f"c{card['config_id']}",
            *[f"{float(card['dimensions'][dim]):.3f}" for dim in AGENT_CARD_DIMENSIONS],
        ])

    lines = [
        "# Phase 4 metrics and analysis report (2026-06-04)",
        "",
        "Scope: Phase 4 analyzes formal Phase 2 repeats 1-3 and Phase 3 attribution/HCI-label artifacts on the VPS checkout `/data/repos/xai-harness-faithfulness`.",
        "",
        "## Evidence boundary",
        "",
        "- Baseline statistics use only `traces/<config>/<task>/{1,2,3}.json`.",
        "- Pilot repeat 0 and Phase 3 counterfactual repeats 301-312 / 401 / 403 / 404 are excluded from baseline statistics.",
        "- The VPS private/raw layer remains the complete replay record; public committed traces are sanitized summaries.",
        "- HCI human-study claims are not made here. These metrics provide evidence cases and presentation material for the HCI study.",
        "",
        "## Generated artifacts",
        "",
        f"- Metrics JSON: `{DEFAULT_ANALYSIS_PATH}`.",
        f"- HCI case pack: `{DEFAULT_HCI_CASE_PACK_PATH}`.",
        f"- Teacher/requirements traceability: `{DEFAULT_TRACEABILITY_PATH}`.",
        f"- Jaccard matrix: `{figures.get('jaccard_matrix', '')}`.",
        f"- Disagreement vs success-gap scatter: `{figures.get('disagreement_success_scatter', '')}`.",
        f"- Factorial contrast bars: `{figures.get('factorial_contrast_bars', '')}`.",
        f"- Method-consistency matrix: `{figures.get('method_consistency', '')}`.",
        f"- Agent-card matrix: `{figures.get('agent_card_matrix', '')}`.",
        "",
        "## Topline",
        "",
        f"- Formal traces analyzed: {overall['formal_trace_count']} across {overall['config_count']} configs x {overall['task_count']} tasks x repeats {overall['formal_repeats']}.",
        f"- Overall success: {overall['success_count']}/{overall['formal_trace_count']} ({overall['success_rate']:.3f}).",
        f"- Mean tool calls per trace: {overall['mean_tool_calls']:.3f}; mean wall time: {overall['mean_wall_time_s']:.3f}s.",
        f"- Sequence-disagreement vs success-gap Pearson r: {_format_rate(assoc['pearson_sequence_disagreement_vs_success_gap'])} over {assoc['n']} config-pair/task observations.",
        f"- Sequence-disagreement vs mean failure-rate Pearson r: {_format_rate(assoc['pearson_sequence_disagreement_vs_mean_failure_rate'])}.",
        f"- Phase 3 HCI labels: {phase3['hci_label_count']}; unanimous M1-M4 agreement: {phase3['unanimous_count']}/{phase3['hci_label_count']} ({phase3['unanimous_rate']:.3f}).",
        "",
        "## Config summary",
        "",
        *_table(config_summary),
        "",
        "## Controlled vs benchmark split",
        "",
        *_table([
            ["Split", "Categories", "n", "Success", "Mean tool calls"],
            *[
                [
                    row["split"],
                    ", ".join(row["categories"]),
                    row["n"],
                    f"{row['success_count']}/{row['n']} ({float(row['success_rate']):.3f})",
                    f"{float(row['mean_tool_calls']):.3f}",
                ]
                for row in overall["task_splits"]
            ],
        ]),
        "",
        "## Category summary",
        "",
        *_table([
            ["Category", "Tasks", "n", "Success", "Mean tools", "Mean wall time"],
            *[
                [
                    row["category"],
                    row["task_count"],
                    row["n"],
                    f"{row['success_count']}/{row['n']} ({float(row['success_rate']):.3f})",
                    f"{float(row['mean_tool_calls']):.3f}",
                    f"{float(row['mean_wall_time_s']):.3f}",
                ]
                for row in analysis["category_summaries"]
            ],
        ]),
        "",
        "## Factorial contrast summary",
        "",
        "The 6-cell matrix is partly anchored: Claude Code appears only with Haiku, and Codex appears only with GPT-mini. Causal interaction summaries therefore use the crossed OpenCode/Hermes cells only.",
        "",
        *_table(contrast_rows),
        "",
        "## Phase 3 method consistency",
        "",
        f"- Factorial labels: {phase3['label_distribution']}.",
        f"- Decision kinds: {phase3['decision_kind_distribution']}.",
        f"- Confidence: {phase3['confidence_distribution']}.",
        f"- Agreement counts: {phase3['agreement_count_distribution']}.",
        "",
        "## Agent-card matrix",
        "",
        "Dimension definitions are descriptive proxies for this controlled Python suite: fidelity=success rate, stability=repeat sequence similarity, robustness=minimum category success rate, actionability=trace evidence completeness, governability=failed-run diagnosability or trace governance coverage.",
        "",
        *_table(agent_rows),
        "",
        "## Reporting limitations",
        "",
        "- The task suite is 20 controlled Python tasks, not a random sample of all coding-agent work.",
        "- Benchmark tasks should be interpreted separately from controlled software-engineering tasks.",
        "- Robustness across languages, frameworks, large repositories, and long-horizon production work is not covered.",
        "- Phase 3 labels are selected high-divergence decision points; they are not a prevalence estimate over all Phase 2 traces.",
        "- HCI conclusions require the separate human study described in `docs/specs/2026-06-04-hci-human-study-plan.md`.",
        "",
    ]
    return "\n".join(lines)


def render_support_pack_report(
    analysis: dict[str, Any],
    hci_case_pack: dict[str, Any],
    traceability: dict[str, Any],
) -> str:
    env_rows = [["Config", "Harness", "Model", "Provider", "Versions", "Runtime budget variants", "Raw/private refs"]]
    for config in analysis["environment_controls"]["configs"]:
        budgets = "; ".join(
            f"{item['budget']} x{item['count']}"
            for item in config["runtime_budget_variants"]
        )
        env_rows.append([
            f"c{config['config_id']}",
            config["harness"],
            config["model_role"],
            config["provider"],
            ", ".join(config["harness_versions_observed"]),
            budgets,
            f"raw {config['raw_log_paths_present']}/{config['n']}; private {config['private_audit_paths_present']}/{config['n']}",
        ])

    task_rows = [["Task", "Category", "Source", "Success", "Mean tools", "Config stdev"]]
    for row in analysis["task_summaries"]:
        task_rows.append([
            row["task_id"],
            row["task_category"],
            row["source"],
            f"{row['success_count']}/{row['n']} ({float(row['success_rate']):.3f})",
            f"{float(row['mean_tool_calls']):.3f}",
            f"{float(row['success_rate_stdev_across_configs']):.3f}",
        ])

    case_rows = [["Case", "Label", "Task", "Attribution", "Decision", "Coverage role"]]
    for case in hci_case_pack["cases"]:
        role_bits = []
        if case["factorial_label"] == "harness_main_effect":
            role_bits.append("harness")
        if case["factorial_label"] == "model_main_effect":
            role_bits.append("model")
        if case["factorial_label"] == "interaction":
            role_bits.append("interaction")
        if case["decision_kind"] == "task_success_gap":
            role_bits.append("success-gap")
        if case["decision_kind"] == "semantic_output_convention":
            role_bits.append("semantic")
        case_rows.append([
            case["case_id"],
            case["label_id"],
            case["task_id"],
            case["factorial_label"],
            case["decision_kind"],
            ", ".join(role_bits) or "general",
        ])

    traceability_rows = [["Requirement", "Status", "Artifacts"]]
    for row in traceability["rows"]:
        traceability_rows.append([
            row["requirement"],
            row["status"],
            ", ".join(row["phase4_artifacts"]),
        ])

    slide_rows = [["Slide", "Title", "Supports"]]
    for slide in _slide_support_pack(analysis, hci_case_pack):
        slide_rows.append([
            slide["slide"],
            slide["title"],
            ", ".join(slide["supports"]),
        ])

    lines = [
        "# Phase 4 report support pack (2026-06-04)",
        "",
        "Purpose: collect the fine-grained Phase 4 outputs needed to answer HCI/XAI report requirements, teacher review points, and peer feedback without relying on hidden GitHub-only views.",
        "",
        "## Boundary",
        "",
        "- Authority: VPS checkout `/data/repos/xai-harness-faithfulness` plus `/data/harness-lab` raw/private artifacts.",
        "- Public artifacts are sanitized summaries and generated analysis outputs.",
        "- Human-study materials are prepared here; actual HCI claims still require human responses.",
        "",
        "## Environment control evidence",
        "",
        *_table(env_rows),
        "",
        "## Task-level evidence table",
        "",
        *_table(task_rows),
        "",
        "## HCI case pack",
        "",
        f"Coverage: {hci_case_pack['coverage']}.",
        "",
        *_table(case_rows),
        "",
        "## Teacher / requirement traceability",
        "",
        *_table(traceability_rows),
        "",
        "## 15-slide support outline",
        "",
        *_table(slide_rows),
        "",
        "## Human-study measurement items",
        "",
        *_table([
            ["Metric", "Item", "Scale"],
            *[
                [item["metric"], item["item"], item["scale"]]
                for item in _study_questions()
            ],
        ]),
        "",
        "## Use in final reporting",
        "",
        "- Use `analysis/phase4/metrics-summary.json` for numeric auditability.",
        "- Use `analysis/phase4/hci-case-pack.json` for HCI condition A/B material generation.",
        "- Use `analysis/phase4/teacher-requirements-traceability.json` as the checklist for teacher requirements.",
        "- Use generated SVGs directly in slides or as report figures.",
        "",
    ]
    return "\n".join(lines)


def write_phase4_outputs(
    analysis: dict[str, Any],
    output_path: str | Path = DEFAULT_ANALYSIS_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    figure_dir: str | Path = DEFAULT_FIGURE_DIR,
) -> dict[str, Any]:
    analysis_file = _repo_path(output_path)
    report_file = _repo_path(report_path)
    hci_case_file = _repo_path(DEFAULT_HCI_CASE_PACK_PATH)
    traceability_file = _repo_path(DEFAULT_TRACEABILITY_PATH)
    support_report_file = _repo_path(DEFAULT_SUPPORT_REPORT_PATH)
    analysis_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    hci_case_file.parent.mkdir(parents=True, exist_ok=True)
    traceability_file.parent.mkdir(parents=True, exist_ok=True)
    support_report_file.parent.mkdir(parents=True, exist_ok=True)
    figures = write_phase4_figures(analysis, figure_dir)
    hci_case_pack = build_hci_case_pack(analysis)
    traceability = build_requirements_traceability(analysis, figures, _rel(hci_case_file))
    analysis = {**analysis, "figures": figures}
    analysis_file.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    hci_case_file.write_text(json.dumps(hci_case_pack, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    traceability_file.write_text(json.dumps(traceability, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    report_file.write_text(render_phase4_report(analysis).rstrip() + "\n")
    support_report_file.write_text(render_support_pack_report(analysis, hci_case_pack, traceability).rstrip() + "\n")
    return {
        "analysis": analysis_file,
        "report": report_file,
        "figures": figures,
        "hci_case_pack": hci_case_file,
        "traceability": traceability_file,
        "support_report": support_report_file,
    }
