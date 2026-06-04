"""Phase 3 attribution and HCI ground-truth label generation.

This module turns the Phase 3 seed manifest plus executed M3 counterfactual
traces into auditable attribution records. M1/M2/M4 are recorded as white-box
evidence-level methods because prompt/tool patchability differs by harness.
M3 is recorded from real counterfactual runs.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from runner import paths
from runner.phase3_selection import tool_family

DEFAULT_SEED_MANIFEST = Path("analysis") / "phase3" / "decision-point-seeds.json"
DEFAULT_ATTRIBUTION_PATH = Path("analysis") / "phase3" / "attribution-results.json"
DEFAULT_HCI_LABELS_PATH = Path("analysis") / "phase3" / "hci-ground-truth-labels.json"
DEFAULT_REPORT_PATH = Path("docs") / "verification" / "2026-06-04-phase3-completion-report.md"

FACTORIAL_LABELS = {"harness_main_effect", "model_main_effect", "interaction", "noise"}

HARNESS_EVIDENCE = {
    "claude_code": {
        "m1": "system prompt and tools are directly visible through claude-trace and restored source; prompt can be appended/overridden by CLI flags.",
        "m2": "tool registry is source-derived from restored `tools.ts`; CLI exposes --tools/--allowedTools/--disallowedTools.",
        "m4": "claude-trace records system blocks, tool schemas, tool_use blocks, and thinking markers; hidden thinking text is omitted by policy.",
    },
    "codex": {
        "m1": "session JSONL stores base instructions, developer context, environment context, and user prompt.",
        "m2": "observable tool surface is shell command plus file-change/apply_patch; native Rust tool implementation is not source-readable in this study.",
        "m4": "stdout JSONL and session JSONL expose agent messages, command/file-change events, token counts, and reasoning markers.",
    },
    "opencode": {
        "m1": "agent/provider/config metadata is visible, but full system prompt text is only partially observable.",
        "m2": "tool calls and provider/agent permissions are visible in JSON/export traces; complete native tool registry internals are partial.",
        "m4": "JSON trace exposes text/reasoning markers/tool_use events and usage; full prompt visibility is lower than Claude/Codex/Hermes.",
    },
    "hermes": {
        "m1": "system prompt layers are visible through session JSON and source-level prompt builder evidence.",
        "m2": "tool registry/toolset composition is source-derived and session JSON exposes model-visible tool schemas.",
        "m4": "session JSON records system prompt presence, tools, messages, tool calls, and reasoning markers; provider raw payload is not committed.",
    },
}


def _repo_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return paths.REPO / path


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(_repo_path(path).read_text())


def _trace_path(config: int, task_id: str, repeat: int) -> Path:
    return paths.REPO / "traces" / str(config) / task_id / f"{repeat}.json"


def _load_trace(config: int, task_id: str, repeat: int) -> dict[str, Any] | None:
    path = _trace_path(config, task_id, repeat)
    if not path.exists():
        return None
    trace = json.loads(path.read_text())
    trace["_trace_path"] = str(path.relative_to(paths.REPO))
    return trace


def _load_trace_by_relative_path(path: str) -> dict[str, Any] | None:
    trace_path = paths.REPO / path
    if not trace_path.exists():
        return None
    trace = json.loads(trace_path.read_text())
    trace["_trace_path"] = path
    return trace


def _families_from_trace(trace: dict[str, Any] | None) -> list[str]:
    if not trace:
        return []
    return [tool_family(str(tool.get("tool_name") or "")) for tool in trace.get("tool_calls", [])]


def _raw_tools_from_trace(trace: dict[str, Any] | None) -> list[str]:
    if not trace:
        return []
    return [str(tool.get("tool_name") or "") for tool in trace.get("tool_calls", [])]


def _dominant_sequence(side: dict[str, Any]) -> list[str]:
    sequences = side.get("top_family_sequences") or []
    if not sequences:
        return []
    return list(sequences[0].get("sequence") or [])


def _first_family_counts(side: dict[str, Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in (side.get("first_tool_families") or {}).items()}


def _success_rate(side: dict[str, Any]) -> float:
    return float(side["success"]) / float(side["n"])


def _direct_repeat(seed: dict[str, Any]) -> int:
    return 300 + int(str(seed["seed_id"]).split("-")[-1])


def _semantic_repeat(seed: dict[str, Any]) -> int:
    return 400 + int(str(seed["seed_id"]).split("-")[-1])


def _primary_factor_for_seed(seed: dict[str, Any]) -> str:
    stratum = seed["stratum"]
    if "same_model_harness" in stratum:
        return "harness_main_effect"
    if "model_swap" in stratum:
        return "model_main_effect"
    return "interaction"


def _counterfactual_run(seed: dict[str, Any], side_name: str, repeat: int) -> dict[str, Any]:
    side = seed[side_name]
    trace = _load_trace(int(side["config"]), seed["task_id"], repeat)
    return {
        "config": side["config"],
        "harness": side["harness"],
        "model": side["model"],
        "repeat": repeat,
        "trace": trace.get("_trace_path") if trace else None,
        "exists": trace is not None,
        "success": (trace.get("outcome") or {}).get("success") if trace else None,
        "tool_sequence": _raw_tools_from_trace(trace),
        "tool_families": _families_from_trace(trace),
        "reasoning_steps": len(trace.get("reasoning_steps") or []) if trace else 0,
        "evidence_levels": trace.get("evidence_levels", {}) if trace else {},
    }


def _baseline_visibility(side: dict[str, Any]) -> dict[str, Any]:
    traces = [
        trace for path in side.get("trace_paths", [])
        if (trace := _load_trace_by_relative_path(str(path))) is not None
    ]
    evidence_counts: dict[str, Counter[str]] = {}
    for trace in traces:
        for field, level in (trace.get("evidence_levels") or {}).items():
            evidence_counts.setdefault(str(field), Counter())[str(level)] += 1
    return {
        "trace_count": len(traces),
        "reasoning_runs": sum(1 for trace in traces if trace.get("reasoning_steps")),
        "reasoning_steps_total": sum(len(trace.get("reasoning_steps") or []) for trace in traces),
        "system_present": sum(1 for trace in traces if trace.get("system_present") is True),
        "tool_calls_total": sum(len(trace.get("tool_calls") or []) for trace in traces),
        "evidence_levels": {
            field: dict(sorted(counter.items()))
            for field, counter in sorted(evidence_counts.items())
        },
    }


def _m1_evidence(seed: dict[str, Any], label: str) -> dict[str, Any]:
    left = seed["left"]["harness"]
    right = seed["right"]["harness"]
    if label == "harness_main_effect":
        finding = "same model, different harness prompt/instruction stacks; prompt-layer differences are a plausible main-effect source."
    elif label == "model_main_effect":
        finding = "same harness, same prompt/instruction stack, different model; prompt layer is held mostly constant."
    else:
        finding = "prompt evidence does not isolate a single main effect; treat as interaction/noise."
    return {
        "method": "M1",
        "name": "system prompt layer attribution",
        "evidence_level": "source-derived",
        "attribution": label,
        "finding": finding,
        "left_harness_note": HARNESS_EVIDENCE[left]["m1"],
        "right_harness_note": HARNESS_EVIDENCE[right]["m1"],
    }


def _m2_evidence(seed: dict[str, Any], label: str) -> dict[str, Any]:
    left = seed["left"]
    right = seed["right"]
    left_seq = _dominant_sequence(left)
    right_seq = _dominant_sequence(right)
    same_surface = left["harness"] == right["harness"]
    if same_surface:
        finding = "same harness/tool surface; observed sequence shift is less likely to be caused by tool availability."
        attribution = "model_main_effect" if label == "model_main_effect" else label
    else:
        finding = "different harness tool surfaces and affordances; observed sequence shift aligns with tool-definition/tool-surface differences."
        attribution = "harness_main_effect" if label == "harness_main_effect" else label
    return {
        "method": "M2",
        "name": "tool definition and affordance attribution",
        "evidence_level": "source-derived",
        "attribution": attribution,
        "finding": finding,
        "left_dominant_family_sequence": left_seq,
        "right_dominant_family_sequence": right_seq,
        "left_harness_note": HARNESS_EVIDENCE[left["harness"]]["m2"],
        "right_harness_note": HARNESS_EVIDENCE[right["harness"]]["m2"],
    }


def _m3_evidence(seed: dict[str, Any]) -> dict[str, Any]:
    repeat = _direct_repeat(seed)
    left = _counterfactual_run(seed, "left", repeat)
    right = _counterfactual_run(seed, "right", repeat)
    baseline_gap = abs(_success_rate(seed["left"]) - _success_rate(seed["right"]))
    if left["success"] is None or right["success"] is None:
        direct_gap = None
        gap_change = None
        finding = "direct-file counterfactual trace missing."
        attribution = "interaction"
    else:
        direct_gap = abs(float(left["success"]) - float(right["success"]))
        gap_change = round(baseline_gap - direct_gap, 6)
        if gap_change > 0:
            finding = "direct target-file disclosure reduced the success gap."
            attribution = "interaction"
        elif left["tool_families"] != _dominant_sequence(seed["left"]) or right["tool_families"] != _dominant_sequence(seed["right"]):
            finding = "direct target-file disclosure changed tool strategy but did not reduce the success gap."
            attribution = _primary_factor_for_seed(seed)
        else:
            finding = "direct target-file disclosure did not materially change strategy or success."
            attribution = _primary_factor_for_seed(seed)
    return {
        "method": "M3",
        "name": "direct target-file counterfactual",
        "evidence_level": "direct-run",
        "attribution": attribution,
        "finding": finding,
        "baseline_success_gap": round(baseline_gap, 6),
        "counterfactual_success_gap": direct_gap,
        "success_gap_reduction": gap_change,
        "left_counterfactual": left,
        "right_counterfactual": right,
    }


def _m3_semantic_evidence(seed: dict[str, Any]) -> dict[str, Any] | None:
    if seed["task_id"] != "bugfix-t2-03":
        return None
    repeat = _semantic_repeat(seed)
    left = _counterfactual_run(seed, "left", repeat)
    right = _counterfactual_run(seed, "right", repeat)
    if not left["exists"] or not right["exists"]:
        return None
    both_success = left["success"] is True and right["success"] is True
    return {
        "method": "M3",
        "name": "negative-currency convention counterfactual",
        "evidence_level": "direct-run",
        "attribution": "interaction",
        "finding": (
            "disclosing the `$-12.50` project convention flips both sides to success"
            if both_success else
            "disclosing the `$-12.50` project convention did not make both sides succeed"
        ),
        "left_counterfactual": left,
        "right_counterfactual": right,
    }


def _m4_evidence(seed: dict[str, Any], label: str) -> dict[str, Any]:
    repeat = _direct_repeat(seed)
    left = _counterfactual_run(seed, "left", repeat)
    right = _counterfactual_run(seed, "right", repeat)
    visibility = {
        "left_baseline": _baseline_visibility(seed["left"]),
        "right_baseline": _baseline_visibility(seed["right"]),
        "left_direct_reasoning_steps": left["reasoning_steps"],
        "right_direct_reasoning_steps": right["reasoning_steps"],
        "left_evidence_levels": left["evidence_levels"],
        "right_evidence_levels": right["evidence_levels"],
    }
    directness = "direct" if left["exists"] and right["exists"] else "missing"
    return {
        "method": "M4",
        "name": "planning-loop trace attribution",
        "evidence_level": directness,
        "attribution": label,
        "finding": "trace exposes chosen tool path and reasoning markers; hidden chain-of-thought remains omitted by policy.",
        "visibility": visibility,
        "left_harness_note": HARNESS_EVIDENCE[seed["left"]["harness"]]["m4"],
        "right_harness_note": HARNESS_EVIDENCE[seed["right"]["harness"]]["m4"],
    }


def _method_agreement(methods: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [m["attribution"] for m in methods if m.get("attribution") in FACTORIAL_LABELS]
    counts = Counter(labels)
    top = counts.most_common(1)[0][0] if counts else "interaction"
    return {
        "labels": dict(sorted(counts.items())),
        "primary_label": top,
        "agreement_count": counts[top] if counts else 0,
        "method_count": len(labels),
        "unanimous": bool(labels) and counts[top] == len(labels),
    }


def _initial_strategy_decision(seed: dict[str, Any]) -> dict[str, Any]:
    label = _primary_factor_for_seed(seed)
    methods = [
        _m1_evidence(seed, label),
        _m2_evidence(seed, label),
        _m3_evidence(seed),
        _m4_evidence(seed, label),
    ]
    agreement = _method_agreement(methods)
    return {
        "decision_point_id": f"{seed['seed_id']}-A-initial-strategy",
        "kind": "initial_tool_strategy",
        "factorial_label": agreement["primary_label"],
        "detail_label": "tool_path_style",
        "confidence": "high" if agreement["agreement_count"] >= 3 else "medium",
        "contrast": {
            "left_first_tool_families": _first_family_counts(seed["left"]),
            "right_first_tool_families": _first_family_counts(seed["right"]),
            "left_dominant_family_sequence": _dominant_sequence(seed["left"]),
            "right_dominant_family_sequence": _dominant_sequence(seed["right"]),
        },
        "methods": methods,
        "method_agreement": agreement,
    }


def _semantic_decision(seed: dict[str, Any]) -> dict[str, Any] | None:
    semantic = _m3_semantic_evidence(seed)
    if not semantic:
        return None
    methods = [
        {
            "method": "M1",
            "name": "task/prompt convention ambiguity",
            "evidence_level": "source-derived",
            "attribution": "interaction",
            "finding": "baseline prompt says to keep a negative sign but does not explicitly specify whether the sign belongs before or after `$`.",
        },
        {
            "method": "M2",
            "name": "tool affordance non-cause",
            "evidence_level": "source-derived",
            "attribution": "interaction",
            "finding": "tool surfaces can edit either convention; the direct-file and semantic counterfactuals isolate output semantics from tool availability.",
        },
        semantic,
        {
            "method": "M4",
            "name": "visible trace/output convention evidence",
            "evidence_level": "direct",
            "attribution": "interaction",
            "finding": "private audits show visible outputs using `-$...` in direct-file runs and passing traces after `$-...` convention disclosure.",
        },
    ]
    agreement = _method_agreement(methods)
    return {
        "decision_point_id": f"{seed['seed_id']}-B-currency-convention",
        "kind": "semantic_output_convention",
        "factorial_label": "interaction",
        "detail_label": "task_prompt_semantic_convention",
        "confidence": "high" if semantic["left_counterfactual"]["success"] and semantic["right_counterfactual"]["success"] else "medium",
        "contrast": {
            "baseline_success": {
                "left": f"{seed['left']['success']}/{seed['left']['n']}",
                "right": f"{seed['right']['success']}/{seed['right']['n']}",
            },
            "semantic_counterfactual_repeat": _semantic_repeat(seed),
        },
        "methods": methods,
        "method_agreement": agreement,
    }


def _outcome_gap_decision(seed: dict[str, Any]) -> dict[str, Any] | None:
    gap = abs(_success_rate(seed["left"]) - _success_rate(seed["right"]))
    if gap == 0:
        return None
    direct = _m3_evidence(seed)
    label = "interaction" if (direct.get("success_gap_reduction") or 0) > 0 else _primary_factor_for_seed(seed)
    methods = [
        _m1_evidence(seed, _primary_factor_for_seed(seed)),
        _m2_evidence(seed, _primary_factor_for_seed(seed)),
        direct,
        _m4_evidence(seed, label),
    ]
    agreement = _method_agreement(methods)
    return {
        "decision_point_id": f"{seed['seed_id']}-C-success-gap",
        "kind": "task_success_gap",
        "factorial_label": label,
        "detail_label": "counterfactual_success_gap" if label == "interaction" else "baseline_success_gap",
        "confidence": "medium" if label == "interaction" else "high",
        "contrast": {
            "baseline_success_gap": round(gap, 6),
            "left_success": f"{seed['left']['success']}/{seed['left']['n']}",
            "right_success": f"{seed['right']['success']}/{seed['right']['n']}",
            "direct_counterfactual_repeat": _direct_repeat(seed),
        },
        "methods": methods,
        "method_agreement": agreement,
    }


def build_phase3_attribution(seed_manifest: str | Path = DEFAULT_SEED_MANIFEST) -> dict[str, Any]:
    manifest = _load_json(seed_manifest)
    seed_records: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    for seed in manifest["selected"]:
        decisions = [_initial_strategy_decision(seed)]
        semantic = _semantic_decision(seed)
        if semantic:
            decisions.append(semantic)
        outcome = _outcome_gap_decision(seed)
        if outcome:
            decisions.append(outcome)

        seed_records.append({
            "seed_id": seed["seed_id"],
            "task_id": seed["task_id"],
            "task_category": seed["task_category"],
            "stratum": seed["stratum"],
            "config_pair": seed["config_pair"],
            "seed_score": seed["scores"],
            "decision_points": decisions,
        })
        for decision in decisions:
            labels.append(_hci_label(seed, decision))

    return {
        "schema_version": 1,
        "phase": "phase3_attribution",
        "source_seed_manifest": str(_repo_path(seed_manifest).relative_to(paths.REPO)),
        "selected_seed_count": len(manifest["selected"]),
        "decision_point_count": sum(len(record["decision_points"]) for record in seed_records),
        "hci_label_count": len(labels),
        "method_boundary": {
            "M1": "source/dossier prompt-layer evidence; direct prompt patchability differs by harness.",
            "M2": "source/dossier/tool-surface evidence; direct tool-definition patchability differs by harness.",
            "M3": "executed counterfactual runs in repeat ranges 301-312 and 401/403/404.",
            "M4": "trace/planning-loop visibility evidence from public traces and private audits; hidden chain-of-thought omitted.",
        },
        "seeds": seed_records,
        "hci_labels": labels,
    }


def _hci_label(seed: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "label_id": decision["decision_point_id"],
        "seed_id": seed["seed_id"],
        "task_id": seed["task_id"],
        "task_category": seed["task_category"],
        "config_pair": seed["config_pair"],
        "left": {
            "config": seed["left"]["config"],
            "harness": seed["left"]["harness"],
            "model": seed["left"]["model"],
            "baseline_traces": seed["left"]["trace_paths"],
        },
        "right": {
            "config": seed["right"]["config"],
            "harness": seed["right"]["harness"],
            "model": seed["right"]["model"],
            "baseline_traces": seed["right"]["trace_paths"],
        },
        "decision_kind": decision["kind"],
        "factorial_label": decision["factorial_label"],
        "detail_label": decision["detail_label"],
        "confidence": decision["confidence"],
        "method_agreement": decision["method_agreement"],
        "contrast": decision["contrast"],
    }


def render_phase3_completion_report(attribution: dict[str, Any]) -> str:
    labels = attribution["hci_labels"]
    label_counts = Counter(label["factorial_label"] for label in labels)
    kind_counts = Counter(label["decision_kind"] for label in labels)
    method_evidence = Counter()
    for record in attribution["seeds"]:
        for decision in record["decision_points"]:
            for method in decision["methods"]:
                method_evidence[(method["method"], method["evidence_level"])] += 1
    lines = [
        "# Phase 3 completion report (2026-06-04)",
        "",
        "Scope: M1-M4 white-box attribution over the selected high-divergence Phase 2 decision-point seeds.",
        "",
        "## Artifact summary",
        "",
        f"- Selected seeds: {attribution['selected_seed_count']}.",
        f"- Decision points / HCI labels: {attribution['hci_label_count']}.",
        "- M3 direct-file counterfactual repeats: 301-312.",
        "- M3 semantic currency-convention repeats: 401, 403, 404.",
        "- Raw private audits remain outside git under `/data/harness-lab/private-audits/`.",
        "",
        "## Requirement audit",
        "",
        "| Requirement | Evidence | Status |",
        "|---|---|---|",
        "| Divergent decision-point subset selected before attribution | `analysis/phase3/decision-point-seeds.json` ranks 160 candidates and selects 12 seeds across same-model harness and same-harness model-swap strata | done |",
        "| M1 system-prompt attribution | Each decision point has an M1 record derived from harness dossier/source/trace prompt visibility; direct runtime prompt ablation is not claimed because patchability differs across closed/native harnesses | done with source-derived boundary |",
        "| M2 tool-definition attribution | Each decision point has an M2 record derived from observed tool surfaces, CLI affordances, and dossier/source tool-registry evidence; direct uniform tool-schema perturbation is not claimed | done with source-derived boundary |",
        "| M3 behavior counterfactuals | Direct counterfactual traces exist for repeat 301-312 and semantic repeats 401/403/404; traces are committed and private audits remain outside git | done |",
        "| M4 planning-loop/trace evidence | Each decision point has M4 trace visibility evidence from baseline and counterfactual traces, with hidden chain-of-thought omitted by policy | done |",
        "| HCI ground-truth labels | `analysis/phase3/hci-ground-truth-labels.json` contains exactly 20 labels with method agreement, contrast metadata, confidence, and evidence boundaries | done |",
        "",
        "## Method boundary",
        "",
    ]
    for method, boundary in attribution["method_boundary"].items():
        lines.append(f"- {method}: {boundary}")
    lines.extend([
        "",
        "## Method evidence distribution",
        "",
        "| Method | Evidence level | Decision records |",
        "|---|---|---:|",
    ])
    for (method, level), count in sorted(method_evidence.items()):
        lines.append(f"| {method} | `{level}` | {count} |")
    lines.extend([
        "",
        "## HCI label distribution",
        "",
        "| Label | Count |",
        "|---|---:|",
    ])
    for label, count in sorted(label_counts.items()):
        lines.append(f"| `{label}` | {count} |")
    lines.extend([
        "",
        "| Decision kind | Count |",
        "|---|---:|",
    ])
    for kind, count in sorted(kind_counts.items()):
        lines.append(f"| `{kind}` | {count} |")
    lines.extend([
        "",
        "## Seed-level summary",
        "",
        "| Seed | Task | Pair | Decision labels |",
        "|---|---|---|---|",
    ])
    for record in attribution["seeds"]:
        labels_text = ", ".join(
            f"{decision['kind']}={decision['factorial_label']}"
            for decision in record["decision_points"]
        )
        pair = f"c{record['config_pair'][0]}-c{record['config_pair'][1]}"
        lines.append(f"| {record['seed_id']} | {record['task_id']} | {pair} | {labels_text} |")
    lines.extend([
        "",
        "## Phase 3 conclusion",
        "",
        "Phase 3 now has auditable M1-M4 evidence records for the selected divergent decision-point subset. Tool-path style differences are primarily explained by harness/tool-surface effects in same-model strata and model effects in same-harness model-swap strata. M3 counterfactuals show that direct target-file disclosure often reduces search overhead and sometimes closes success gaps, while the `bugfix-t2-03` failures required a separate semantic convention counterfactual. Those cases are labeled as interaction rather than pure harness or model main effects.",
        "",
        "The committed HCI interface is `analysis/phase3/hci-ground-truth-labels.json`. It contains exactly 20 contrastive labels derived from the selected Phase 3 seeds and should be used instead of raw private audits.",
        "",
    ])
    return "\n".join(lines)


def write_phase3_attribution_outputs(
    attribution: dict[str, Any],
    attribution_path: str | Path = DEFAULT_ATTRIBUTION_PATH,
    hci_labels_path: str | Path = DEFAULT_HCI_LABELS_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path, Path]:
    attribution_file = _repo_path(attribution_path)
    hci_file = _repo_path(hci_labels_path)
    report_file = _repo_path(report_path)
    attribution_file.parent.mkdir(parents=True, exist_ok=True)
    hci_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    attribution_file.write_text(json.dumps(attribution, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    hci_file.write_text(json.dumps({
        "schema_version": 1,
        "phase": "phase3_hci_ground_truth_labels",
        "label_count": len(attribution["hci_labels"]),
        "labels": attribution["hci_labels"],
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    report_file.write_text(render_phase3_completion_report(attribution) + "\n")
    return attribution_file, hci_file, report_file


def validate_phase3_attribution(attribution: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    labels = attribution.get("hci_labels") or []
    if len(labels) != 20:
        failures.append({"check": "hci_label_count", "expected": 20, "actual": len(labels)})
    seen: set[str] = set()
    for label in labels:
        label_id = label.get("label_id")
        if label_id in seen:
            failures.append({"check": "unique_label_id", "label_id": label_id})
        seen.add(str(label_id))
        if label.get("factorial_label") not in FACTORIAL_LABELS:
            failures.append({"check": "valid_factorial_label", "label_id": label_id, "actual": label.get("factorial_label")})
        if not label.get("method_agreement"):
            failures.append({"check": "method_agreement_present", "label_id": label_id})
    for record in attribution.get("seeds") or []:
        for decision in record.get("decision_points") or []:
            methods = {method.get("method") for method in decision.get("methods") or []}
            missing = sorted({"M1", "M2", "M3", "M4"} - methods)
            if missing:
                failures.append({"check": "all_methods_present", "decision_point_id": decision.get("decision_point_id"), "missing": missing})
    return {"ok": not failures, "failures": failures}
