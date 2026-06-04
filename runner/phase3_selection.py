"""Phase 3 decision-point seed selection from formal Phase 2 traces.

The baseline traces record chosen tool sequences, not hidden alternatives.
Phase 3 starts by selecting high-divergence chosen-tool sequence pairs as
auditable seeds for M1-M4 attribution experiments.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from runner import paths

FORMAL_REPEATS = (1, 2, 3)
SUCCESS_GAP_WEIGHT = 0.25
DEFAULT_PER_STRATUM = 3
DEFAULT_MANIFEST_PATH = paths.REPO / "analysis" / "phase3" / "decision-point-seeds.json"
DEFAULT_REPORT_PATH = paths.REPO / "docs" / "verification" / "2026-06-04-phase3-seed-selection.md"

TOOL_FAMILIES = {
    "bash": "shell",
    "command_execution": "shell",
    "execute_code": "shell",
    "terminal": "shell",
    "edit": "edit",
    "apply_patch": "edit",
    "file_change": "edit",
    "multiedit": "edit",
    "patch": "edit",
    "write": "edit",
    "write_file": "edit",
    "glob": "search",
    "grep": "search",
    "search_files": "search",
    "read": "read",
    "read_file": "read",
    "todo_write": "plan",
    "todowrite": "plan",
}

STRATA = [
    {
        "name": "haiku_same_model_harness",
        "purpose": "Harness attribution under Haiku 4.5",
        "pairs": [(1, 2), (1, 3), (2, 3)],
    },
    {
        "name": "gptmini_same_model_harness",
        "purpose": "Harness attribution under GPT-5.4-mini",
        "pairs": [(4, 5), (4, 6), (5, 6)],
    },
    {
        "name": "opencode_model_swap",
        "purpose": "Model attribution within OpenCode",
        "pairs": [(2, 4)],
    },
    {
        "name": "hermes_model_swap",
        "purpose": "Model attribution within Hermes",
        "pairs": [(3, 5)],
    },
]


def tool_family(tool_name: str) -> str:
    """Map harness-specific tool names to a cross-harness family."""
    normalized = tool_name.replace("-", "_").lower()
    return TOOL_FAMILIES.get(normalized, normalized)


def _jaccard_similarity(a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> float:
    left = set(a)
    right = set(b)
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def _normalized_levenshtein(a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> float:
    previous = list(range(len(b) + 1))
    for i, left_item in enumerate(a, start=1):
        current = [i] + [0] * len(b)
        for j, right_item in enumerate(b, start=1):
            current[j] = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (left_item != right_item),
            )
        previous = current
    return previous[-1] / max(len(a), len(b), 1)


def _sequence_divergence(a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]) -> float:
    """Blend set disagreement and order disagreement into a 0-1 score."""
    return ((1.0 - _jaccard_similarity(a, b)) + _normalized_levenshtein(a, b)) / 2.0


def _short(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO))
    except ValueError:
        return str(path)


def load_formal_phase2_traces(
    trace_root: Path | None = None,
    repeats: tuple[int, ...] = FORMAL_REPEATS,
) -> list[dict[str, Any]]:
    root = trace_root or paths.REPO / "traces"
    traces: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*/*.json")):
        trace = json.loads(path.read_text())
        if int(trace.get("repeat_index", -1)) not in repeats:
            continue
        trace["_trace_path"] = _short(path)
        traces.append(trace)
    return traces


def _cell_summary(traces: list[dict[str, Any]]) -> dict[str, Any]:
    traces = sorted(traces, key=lambda trace: int(trace["repeat_index"]))
    family_sequences = [
        [tool_family(str(tool["tool_name"])) for tool in trace.get("tool_calls", [])]
        for trace in traces
    ]
    raw_sequences = [
        [str(tool["tool_name"]) for tool in trace.get("tool_calls", [])]
        for trace in traces
    ]
    first_families = Counter(seq[0] if seq else "<none>" for seq in family_sequences)
    sequence_counts = Counter(tuple(seq) for seq in family_sequences)
    tool_family_counts: Counter[str] = Counter()
    for seq in family_sequences:
        tool_family_counts.update(seq)

    first = traces[0]
    return {
        "config": int(first["config_id"]),
        "harness": first["harness"],
        "model": first["model_snapshot"],
        "n": len(traces),
        "success": sum(1 for trace in traces if (trace.get("outcome") or {}).get("success") is True),
        "family_sequences": family_sequences,
        "raw_sequences": raw_sequences,
        "first_tool_families": dict(sorted(first_families.items())),
        "top_family_sequences": [
            {"sequence": list(sequence), "count": count}
            for sequence, count in sequence_counts.most_common(3)
        ],
        "tool_family_counts": dict(sorted(tool_family_counts.items())),
        "trace_paths": [str(trace.get("_trace_path", "")) for trace in traces],
    }


def _candidate_for_pair(
    stratum: dict[str, Any],
    task_id: str,
    task_category: str,
    left: dict[str, Any],
    right: dict[str, Any],
) -> dict[str, Any]:
    pair_scores = [
        _sequence_divergence(left_seq, right_seq)
        for left_seq in left["family_sequences"]
        for right_seq in right["family_sequences"]
    ]
    sequence_divergence = sum(pair_scores) / len(pair_scores)
    left_success_rate = left["success"] / left["n"]
    right_success_rate = right["success"] / right["n"]
    success_gap = abs(left_success_rate - right_success_rate)
    score = sequence_divergence + (SUCCESS_GAP_WEIGHT * success_gap)
    first_signal = f"c{left['config']} {left['first_tool_families']} vs c{right['config']} {right['first_tool_families']}"

    return {
        "stratum": stratum["name"],
        "purpose": stratum["purpose"],
        "task_id": task_id,
        "task_category": task_category,
        "config_pair": [left["config"], right["config"]],
        "left": {
            "config": left["config"],
            "harness": left["harness"],
            "model": left["model"],
            "success": left["success"],
            "n": left["n"],
            "first_tool_families": left["first_tool_families"],
            "top_family_sequences": left["top_family_sequences"],
            "trace_paths": left["trace_paths"],
        },
        "right": {
            "config": right["config"],
            "harness": right["harness"],
            "model": right["model"],
            "success": right["success"],
            "n": right["n"],
            "first_tool_families": right["first_tool_families"],
            "top_family_sequences": right["top_family_sequences"],
            "trace_paths": right["trace_paths"],
        },
        "scores": {
            "sequence_divergence": round(sequence_divergence, 6),
            "success_gap": round(success_gap, 6),
            "success_gap_weight": SUCCESS_GAP_WEIGHT,
            "selection_score": round(score, 6),
        },
        "rationale": (
            f"{first_signal}; success {left['success']}/{left['n']} "
            f"vs {right['success']}/{right['n']}"
        ),
    }


def rank_phase3_candidates(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_cell: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    categories: dict[str, str] = {}
    for trace in traces:
        config_id = int(trace["config_id"])
        task_id = str(trace["task_id"])
        by_cell[(config_id, task_id)].append(trace)
        categories[task_id] = str(trace["task_category"])

    summaries = {key: _cell_summary(cell_traces) for key, cell_traces in by_cell.items()}
    candidates: list[dict[str, Any]] = []
    for stratum in STRATA:
        for task_id in sorted(categories):
            for left_config, right_config in stratum["pairs"]:
                left = summaries.get((left_config, task_id))
                right = summaries.get((right_config, task_id))
                if not left or not right:
                    continue
                candidates.append(
                    _candidate_for_pair(
                        stratum=stratum,
                        task_id=task_id,
                        task_category=categories[task_id],
                        left=left,
                        right=right,
                    )
                )

    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate["scores"]["selection_score"],
            -candidate["scores"]["sequence_divergence"],
            -candidate["scores"]["success_gap"],
            candidate["stratum"],
            candidate["task_id"],
            candidate["config_pair"],
        ),
    )


def _select_by_stratum(candidates: list[dict[str, Any]], per_stratum: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for stratum in STRATA:
        stratum_candidates = [candidate for candidate in candidates if candidate["stratum"] == stratum["name"]]
        selected.extend(stratum_candidates[:per_stratum])

    for index, seed in enumerate(selected, start=1):
        seed["seed_id"] = f"PH3-DP-{index:03d}"
    return selected


def build_phase3_seed_manifest(
    traces: list[dict[str, Any]] | None = None,
    per_stratum: int = DEFAULT_PER_STRATUM,
) -> dict[str, Any]:
    if per_stratum < 1:
        raise ValueError("per_stratum must be >= 1")

    traces = traces if traces is not None else load_formal_phase2_traces()
    candidates = rank_phase3_candidates(traces)
    selected = _select_by_stratum(candidates, per_stratum)
    return {
        "schema_version": 1,
        "phase": "phase3_decision_point_seed_selection",
        "source": {
            "trace_root": "traces",
            "formal_repeats": list(FORMAL_REPEATS),
            "trace_count": len(traces),
            "candidate_count": len(candidates),
        },
        "scoring": {
            "sequence_divergence": "mean pairwise blend of 1-Jaccard(tool families) and normalized Levenshtein(tool-family sequences)",
            "selection_score": f"sequence_divergence + {SUCCESS_GAP_WEIGHT} * success_gap",
            "note": "These are chosen-tool-sequence seeds; hidden alternatives are measured in Phase 3 perturbation and trace review.",
        },
        "strata": STRATA,
        "per_stratum": per_stratum,
        "selected": selected,
        "candidates": candidates,
    }


def render_phase3_seed_report(manifest: dict[str, Any]) -> str:
    selected = manifest["selected"]
    lines = [
        "# Phase 3 decision-point seed selection (2026-06-04)",
        "",
        "Scope: select auditable high-divergence Phase 2 chosen-tool sequence pairs for Phase 3 M1-M4 white-box attribution.",
        "",
        "## Method",
        "",
        f"- Source traces: formal Phase 2 repeats {manifest['source']['formal_repeats']} only.",
        f"- Candidate count: {manifest['source']['candidate_count']}; selected seeds: {len(selected)}.",
        f"- Score: `selection_score = sequence_divergence + {SUCCESS_GAP_WEIGHT} * success_gap`.",
        "- `sequence_divergence` is the mean pairwise blend of tool-family Jaccard disagreement and normalized edit distance across the 3x3 repeat pairs.",
        "- Tool names are canonicalized into families (`read`, `search`, `edit`, `shell`, `plan`) so harness vocabulary differences do not dominate the score.",
        "",
        "## Selected seeds",
        "",
        "| Seed | Stratum | Task | Pair | Score | Seq div | Success gap | First-tool signal |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for seed in selected:
        pair = f"c{seed['config_pair'][0]}-c{seed['config_pair'][1]}"
        signal = seed["rationale"].replace("|", "/")
        lines.append(
            "| {seed_id} | {stratum} | {task_id} | {pair} | {score:.3f} | {div:.3f} | {gap:.3f} | {signal} |".format(
                seed_id=seed["seed_id"],
                stratum=seed["stratum"],
                task_id=seed["task_id"],
                pair=pair,
                score=seed["scores"]["selection_score"],
                div=seed["scores"]["sequence_divergence"],
                gap=seed["scores"]["success_gap"],
                signal=signal,
            )
        )
    lines.extend([
        "",
        "## Phase 3 usage",
        "",
        "Use these seeds as the initial M1-M4 queue. For each seed, Phase 3 should inspect the referenced private audit/raw traces, define the concrete observable decision point, then run the relevant system-prompt ablation, tool-definition perturbation, task counterfactual, and planning-trace review where the harness supports it.",
        "",
        "Boundary: Phase 2 traces have `decision_points=[]`; this file does not invent hidden alternatives. It records chosen-tool divergence seeds that Phase 3 must validate through perturbation and white-box evidence.",
        "",
    ])
    return "\n".join(lines)


def _resolve_repo_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return paths.REPO / path


def write_phase3_seed_outputs(
    manifest: dict[str, Any],
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    manifest_file = _resolve_repo_path(manifest_path)
    report_file = _resolve_repo_path(report_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    report_file.write_text(render_phase3_seed_report(manifest) + "\n")
    return manifest_file, report_file
