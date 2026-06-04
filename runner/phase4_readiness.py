"""Phase 4 readiness validation.

This gate is intentionally read-only: it validates committed Phase 2/3 public
artifacts plus VPS private/raw links before downstream metric/HCI analysis.
It must not launch harnesses or mutate traces.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from runner import paths
from runner.phase2_validation import validate_phase2
from runner.phase3_attribution import FACTORIAL_LABELS

FORMAL_REPEATS = (1, 2, 3)
EXPECTED_CONFIGS = (1, 2, 3, 4, 5, 6)
EXPECTED_TASKS = 20
EXPECTED_FORMAL_TRACES = len(EXPECTED_CONFIGS) * EXPECTED_TASKS * len(FORMAL_REPEATS)
EXPECTED_SEEDS = 12
EXPECTED_HCI_LABELS = 20
EXPECTED_CANDIDATES = 160
PILOT_REPEAT = 0
DIRECT_COUNTERFACTUAL_REPEATS = set(range(301, 313))
SEMANTIC_COUNTERFACTUAL_REPEATS = {401, 403, 404}
ALLOWED_NONFORMAL_REPEATS = {PILOT_REPEAT} | DIRECT_COUNTERFACTUAL_REPEATS | SEMANTIC_COUNTERFACTUAL_REPEATS

PUBLIC_SCAN_DIRS = ("tests/fixtures", "traces", "analysis")
GUARDRAILS_PATH = Path("docs") / "specs" / "2026-06-04-phase4-analysis-guardrails.md"
HCI_STUDY_PLAN_PATH = Path("docs") / "specs" / "2026-06-04-hci-human-study-plan.md"
REQUIRED_GUARDRAIL_TERMS = (
    "MIS graduate students and the instructor",
    "Do not present xAI metrics alone as HCI evaluation",
    "They do not justify broad claims about all coding-agent tasks",
    "The HCI report must include a human study",
    "participants: a small convenience sample from MIS graduate students or peers",
    "condition: compare at least two presentation styles",
    "clarity, trust calibration, verification intention",
    "voluntary participation, anonymization, no grade penalty",
    "5 categories x 4 tasks",
    "hidden graders fail on the baseline state and pass on reference solutions",
    "Analyze benchmark tasks separately from controlled software-engineering tasks",
    "programming languages beyond Python",
    "use formal Phase 2 repeats 1-3 only",
)
REQUIRED_HCI_STUDY_PLAN_TERMS = (
    "target `n=6-10`",
    "within-subject design",
    "Condition A: summary-only view",
    "Condition B: evidence + limitation + action view",
    "clarity",
    "trust calibration",
    "verification intention or action choice",
    "perceived safety/control",
    "cognitive load or effort",
    "does not prove the harness attribution itself",
)
FORBIDDEN_PUBLIC_PATTERNS = (
    "thinking_delta",
    "signature_delta",
    "encrypted_content",
    "reasoning_content",
)
ALLOWED_REASONING_SENTINELS = {"", "none", "[redacted hidden reasoning]"}


def _repo_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else paths.REPO / p


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(_repo_path(path).read_text())


def _trace_path(config: int, task_id: str, repeat: int) -> Path:
    return paths.REPO / "traces" / str(config) / task_id / f"{repeat}.json"


def _trace_ref_parts(path: str) -> tuple[int, str, int] | None:
    parts = Path(path).parts
    if len(parts) != 4 or parts[0] != "traces" or not parts[3].endswith(".json"):
        return None
    try:
        return int(parts[1]), parts[2], int(Path(parts[3]).stem)
    except ValueError:
        return None


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO))
    except ValueError:
        return str(path)


def _add(failures: list[dict[str, Any]], check: str, **detail: Any) -> None:
    failures.append({"check": check, **detail})


def _public_files() -> list[Path]:
    files: list[Path] = []
    for dirname in PUBLIC_SCAN_DIRS:
        root = paths.REPO / dirname
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(files)


def _walk_json(value: Any, path: str = "") -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}/{key}" if path else str(key)
            if key == "reasoning" and isinstance(child, str) and child.strip().lower() not in ALLOWED_REASONING_SENTINELS:
                failures.append({"json_path": child_path, "key": key})
            failures.extend(_walk_json(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_walk_json(child, f"{path}[{index}]"))
    return failures


def scan_public_hidden_reasoning_payloads() -> list[dict[str, Any]]:
    """Find public files that still expose hidden reasoning payload text."""
    failures: list[dict[str, Any]] = []
    for path in _public_files():
        text = path.read_text(errors="replace")
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            if pattern in text:
                failures.append({"file": _rel(path), "pattern": pattern, "count": text.count(pattern)})
        if path.suffix in {".json", ".jsonl"}:
            records: list[Any] = []
            try:
                if path.suffix == ".jsonl":
                    records = [json.loads(line) for line in text.splitlines() if line.strip()]
                else:
                    records = [json.loads(text)]
            except json.JSONDecodeError:
                continue
            for record_index, record in enumerate(records):
                for hit in _walk_json(record):
                    failures.append({"file": _rel(path), "record": record_index, **hit})
    return failures


def _check_baseline_trace_refs(
    refs: list[str],
    failures: list[dict[str, Any]],
    check_prefix: str,
    expected_config: int | None = None,
    expected_task: str | None = None,
) -> None:
    if len(refs) != len(FORMAL_REPEATS):
        _add(failures, f"{check_prefix}_count", expected=len(FORMAL_REPEATS), actual=len(refs), refs=refs)
    seen_repeats: set[int] = set()
    for ref in refs:
        parts = _trace_ref_parts(str(ref))
        if not parts:
            _add(failures, f"{check_prefix}_path_shape", path=ref)
            continue
        config, task_id, repeat = parts
        seen_repeats.add(repeat)
        if expected_config is not None and config != expected_config:
            _add(failures, f"{check_prefix}_config", path=ref, expected=expected_config, actual=config)
        if expected_task is not None and task_id != expected_task:
            _add(failures, f"{check_prefix}_task", path=ref, expected=expected_task, actual=task_id)
        if repeat not in FORMAL_REPEATS:
            _add(failures, f"{check_prefix}_repeat", path=ref, allowed=list(FORMAL_REPEATS), actual=repeat)
        if not (paths.REPO / ref).exists():
            _add(failures, f"{check_prefix}_exists", path=ref)
    if seen_repeats and seen_repeats != set(FORMAL_REPEATS):
        _add(failures, f"{check_prefix}_repeat_set", expected=list(FORMAL_REPEATS), actual=sorted(seen_repeats))


def _check_counterfactual_trace(
    config: int,
    task_id: str,
    repeat: int,
    failures: list[dict[str, Any]],
    check: str,
) -> None:
    allowed = DIRECT_COUNTERFACTUAL_REPEATS | SEMANTIC_COUNTERFACTUAL_REPEATS
    if repeat not in allowed:
        _add(failures, f"{check}_repeat_allowed", config=config, task_id=task_id, repeat=repeat)
    path = _trace_path(config, task_id, repeat)
    if not path.exists():
        _add(failures, f"{check}_trace_exists", path=_rel(path))
        return
    try:
        trace = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        _add(failures, f"{check}_trace_json", path=_rel(path), error=str(exc))
        return
    expected = {"config_id": config, "task_id": task_id, "repeat_index": repeat}
    for field, value in expected.items():
        if trace.get(field) != value:
            _add(failures, f"{check}_trace_metadata", path=_rel(path), field=field, expected=value, actual=trace.get(field))


def _check_method_payload(method: dict[str, Any], failures: list[dict[str, Any]], decision_id: str) -> None:
    if method.get("evidence_level") != "direct-run":
        return
    for side in ("left_counterfactual", "right_counterfactual"):
        cf = method.get(side)
        if not isinstance(cf, dict):
            _add(failures, "direct_run_counterfactual_present", decision_point_id=decision_id, method=method.get("method"), side=side)
            continue
        if cf.get("exists") is not True:
            _add(failures, "direct_run_counterfactual_exists", decision_point_id=decision_id, method=method.get("method"), side=side)
        trace_ref = cf.get("trace")
        if not trace_ref or not (paths.REPO / str(trace_ref)).exists():
            _add(failures, "direct_run_counterfactual_trace", decision_point_id=decision_id, method=method.get("method"), side=side, trace=trace_ref)


def _validate_formal_traces(failures: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    trace_files = sorted((paths.REPO / "traces").glob("*/*/*.json"))
    formal: list[dict[str, Any]] = []
    nonformal_repeats: Counter[int] = Counter()
    formal_by_cell: Counter[tuple[int, str]] = Counter()
    config_counts: Counter[int] = Counter()
    task_ids: set[str] = set()

    for path in trace_files:
        try:
            trace = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            _add(failures, "trace_json", path=_rel(path), error=str(exc))
            continue
        repeat = int(trace.get("repeat_index", -1))
        if repeat not in FORMAL_REPEATS:
            nonformal_repeats[repeat] += 1
            if repeat not in ALLOWED_NONFORMAL_REPEATS:
                _add(failures, "unexpected_nonformal_repeat", path=_rel(path), repeat=repeat)
            continue
        formal.append(trace)
        config = int(trace.get("config_id", -1))
        task_id = str(trace.get("task_id", ""))
        formal_by_cell[(config, task_id)] += 1
        config_counts[config] += 1
        task_ids.add(task_id)
        if trace.get("decision_points"):
            _add(failures, "formal_trace_decision_points_empty", path=_rel(path))
        if not trace.get("tool_calls"):
            _add(failures, "formal_trace_tool_calls_nonempty", path=_rel(path))

    if len(formal) != EXPECTED_FORMAL_TRACES:
        _add(failures, "formal_trace_count", expected=EXPECTED_FORMAL_TRACES, actual=len(formal))
    if sorted(config_counts) != list(EXPECTED_CONFIGS):
        _add(failures, "formal_configs", expected=list(EXPECTED_CONFIGS), actual=sorted(config_counts))
    for config in EXPECTED_CONFIGS:
        if config_counts[config] != EXPECTED_TASKS * len(FORMAL_REPEATS):
            _add(failures, "formal_config_trace_count", config=config, expected=EXPECTED_TASKS * len(FORMAL_REPEATS), actual=config_counts[config])
    if len(task_ids) != EXPECTED_TASKS:
        _add(failures, "formal_task_count", expected=EXPECTED_TASKS, actual=len(task_ids))
    bad_cells = [
        {"config": config, "task_id": task_id, "count": count}
        for (config, task_id), count in sorted(formal_by_cell.items())
        if count != len(FORMAL_REPEATS)
    ]
    if bad_cells:
        _add(failures, "formal_cell_repeat_count", expected=len(FORMAL_REPEATS), cells=bad_cells)
    if nonformal_repeats:
        warnings.append({"check": "nonformal_repeats_present_for_pilot_or_phase3_context_only", "counts": dict(sorted(nonformal_repeats.items()))})

    return {
        "formal_trace_count": len(formal),
        "config_counts": dict(sorted(config_counts.items())),
        "task_count": len(task_ids),
        "nonformal_repeat_counts": dict(sorted(nonformal_repeats.items())),
    }


def _validate_phase3_inputs(failures: list[dict[str, Any]]) -> dict[str, Any]:
    seed_path = paths.REPO / "analysis" / "phase3" / "decision-point-seeds.json"
    attribution_path = paths.REPO / "analysis" / "phase3" / "attribution-results.json"
    hci_path = paths.REPO / "analysis" / "phase3" / "hci-ground-truth-labels.json"
    for required in (seed_path, attribution_path, hci_path):
        if not required.exists():
            _add(failures, "phase3_input_exists", path=_rel(required))
    if any(not path.exists() for path in (seed_path, attribution_path, hci_path)):
        return {}

    seeds = _load_json(seed_path)
    attribution = _load_json(attribution_path)
    hci = _load_json(hci_path)

    selected = seeds.get("selected") or []
    if len(selected) != EXPECTED_SEEDS:
        _add(failures, "phase3_seed_count", expected=EXPECTED_SEEDS, actual=len(selected))
    source = seeds.get("source") or {}
    if source.get("formal_repeats") != list(FORMAL_REPEATS):
        _add(failures, "phase3_seed_formal_repeats", expected=list(FORMAL_REPEATS), actual=source.get("formal_repeats"))
    if source.get("trace_count") != EXPECTED_FORMAL_TRACES:
        _add(failures, "phase3_seed_trace_count", expected=EXPECTED_FORMAL_TRACES, actual=source.get("trace_count"))
    if source.get("candidate_count") != EXPECTED_CANDIDATES:
        _add(failures, "phase3_seed_candidate_count", expected=EXPECTED_CANDIDATES, actual=source.get("candidate_count"))

    seed_ids = [seed.get("seed_id") for seed in selected]
    if len(seed_ids) != len(set(seed_ids)):
        _add(failures, "phase3_seed_unique_ids", ids=seed_ids)
    stratum_counts = Counter(str(seed.get("stratum")) for seed in selected)
    for stratum, count in sorted(stratum_counts.items()):
        if count != 3:
            _add(failures, "phase3_seed_stratum_balance", stratum=stratum, expected=3, actual=count)

    for seed in selected:
        task_id = str(seed.get("task_id"))
        for side_name in ("left", "right"):
            side = seed.get(side_name) or {}
            _check_baseline_trace_refs(
                [str(path) for path in side.get("trace_paths") or []],
                failures,
                f"phase3_seed_{side_name}_baseline",
                expected_config=int(side.get("config", -1)),
                expected_task=task_id,
            )

    attribution_labels = attribution.get("hci_labels") or []
    hci_labels = hci.get("labels") or []
    if attribution.get("selected_seed_count") != EXPECTED_SEEDS:
        _add(failures, "attribution_seed_count", expected=EXPECTED_SEEDS, actual=attribution.get("selected_seed_count"))
    if attribution.get("decision_point_count") != EXPECTED_HCI_LABELS:
        _add(failures, "attribution_decision_point_count", expected=EXPECTED_HCI_LABELS, actual=attribution.get("decision_point_count"))
    if attribution.get("hci_label_count") != EXPECTED_HCI_LABELS:
        _add(failures, "attribution_hci_label_count", expected=EXPECTED_HCI_LABELS, actual=attribution.get("hci_label_count"))
    if hci.get("label_count") != EXPECTED_HCI_LABELS or len(hci_labels) != EXPECTED_HCI_LABELS:
        _add(failures, "hci_label_count", expected=EXPECTED_HCI_LABELS, actual=hci.get("label_count"), actual_labels=len(hci_labels))
    if attribution_labels != hci_labels:
        _add(failures, "hci_label_payload_matches_attribution")
    if sorted(label.get("label_id") for label in attribution_labels) != sorted(label.get("label_id") for label in hci_labels):
        _add(failures, "hci_label_ids_match_attribution")
    if sorted((attribution.get("method_boundary") or {})) != ["M1", "M2", "M3", "M4"]:
        _add(failures, "attribution_method_boundary", actual=sorted((attribution.get("method_boundary") or {})))

    seen_labels: set[str] = set()
    known_seed_ids = set(str(seed_id) for seed_id in seed_ids)
    for label in hci_labels:
        label_id = str(label.get("label_id"))
        if label_id in seen_labels:
            _add(failures, "hci_label_unique_id", label_id=label_id)
        seen_labels.add(label_id)
        if label.get("seed_id") not in known_seed_ids:
            _add(failures, "hci_label_seed_known", label_id=label_id, seed_id=label.get("seed_id"))
        if label.get("factorial_label") not in FACTORIAL_LABELS:
            _add(failures, "hci_label_factorial_label", label_id=label_id, actual=label.get("factorial_label"))
        agreement = label.get("method_agreement") or {}
        if agreement.get("method_count") != 4:
            _add(failures, "hci_label_method_count", label_id=label_id, expected=4, actual=agreement.get("method_count"))
        task_id = str(label.get("task_id"))
        for side_name in ("left", "right"):
            side = label.get(side_name) or {}
            _check_baseline_trace_refs(
                [str(path) for path in side.get("baseline_traces") or []],
                failures,
                f"hci_label_{side_name}_baseline",
                expected_config=int(side.get("config", -1)),
                expected_task=task_id,
            )
        contrast = label.get("contrast") or {}
        for key in ("direct_counterfactual_repeat", "semantic_counterfactual_repeat"):
            if key in contrast:
                repeat = int(contrast[key])
                for side_name in ("left", "right"):
                    side = label.get(side_name) or {}
                    _check_counterfactual_trace(int(side.get("config", -1)), task_id, repeat, failures, f"hci_label_{key}_{side_name}")

    for seed_record in attribution.get("seeds") or []:
        for decision in seed_record.get("decision_points") or []:
            decision_id = str(decision.get("decision_point_id"))
            methods = decision.get("methods") or []
            method_names = {method.get("method") for method in methods}
            missing = sorted({"M1", "M2", "M3", "M4"} - method_names)
            if missing:
                _add(failures, "attribution_decision_methods", decision_point_id=decision_id, missing=missing)
            for method in methods:
                _check_method_payload(method, failures, decision_id)

    return {
        "selected_seed_count": len(selected),
        "hci_label_count": len(hci_labels),
        "label_distribution": dict(sorted(Counter(label.get("factorial_label") for label in hci_labels).items())),
        "decision_kind_distribution": dict(sorted(Counter(label.get("decision_kind") for label in hci_labels).items())),
    }


def _validate_guardrails(failures: list[dict[str, Any]]) -> dict[str, Any]:
    path = paths.REPO / GUARDRAILS_PATH
    if not path.exists():
        _add(failures, "phase4_guardrails_exists", path=str(GUARDRAILS_PATH))
        return {"path": str(GUARDRAILS_PATH), "present": False}

    text = path.read_text()
    missing = [term for term in REQUIRED_GUARDRAIL_TERMS if term not in text]
    if missing:
        _add(failures, "phase4_guardrails_terms", path=str(GUARDRAILS_PATH), missing=missing)
    return {
        "path": str(GUARDRAILS_PATH),
        "present": True,
        "required_terms": len(REQUIRED_GUARDRAIL_TERMS),
        "missing_terms": missing,
    }


def _validate_hci_study_plan(failures: list[dict[str, Any]]) -> dict[str, Any]:
    path = paths.REPO / HCI_STUDY_PLAN_PATH
    if not path.exists():
        _add(failures, "hci_study_plan_exists", path=str(HCI_STUDY_PLAN_PATH))
        return {"path": str(HCI_STUDY_PLAN_PATH), "present": False}

    text = path.read_text()
    missing = [term for term in REQUIRED_HCI_STUDY_PLAN_TERMS if term not in text]
    if missing:
        _add(failures, "hci_study_plan_terms", path=str(HCI_STUDY_PLAN_PATH), missing=missing)
    return {
        "path": str(HCI_STUDY_PLAN_PATH),
        "present": True,
        "required_terms": len(REQUIRED_HCI_STUDY_PLAN_TERMS),
        "missing_terms": missing,
    }


def validate_phase4_readiness(run_phase2_gate: bool = True) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    phase2_summary: dict[str, Any] | None = None
    if run_phase2_gate:
        phase2 = validate_phase2(repeat_start=FORMAL_REPEATS[0], repeats=len(FORMAL_REPEATS))
        phase2_summary = {
            "ok": phase2.get("ok"),
            "expected_traces": phase2.get("expected_traces"),
            "found_traces": phase2.get("found_traces"),
            "failure_counts": {
                key: len(value) for key, value in (phase2.get("failures") or {}).items()
            },
        }
        if not phase2.get("ok"):
            _add(failures, "phase2_validate", summary=phase2_summary)

    formal_summary = _validate_formal_traces(failures, warnings)
    phase3_summary = _validate_phase3_inputs(failures)
    guardrail_summary = _validate_guardrails(failures)
    hci_study_summary = _validate_hci_study_plan(failures)

    for hit in scan_public_hidden_reasoning_payloads():
        _add(failures, "public_hidden_reasoning_payload", **hit)

    return {
        "ok": not failures,
        "phase": "phase4_readiness",
        "expected_inputs": {
            "formal_phase2_traces": "traces/<config>/<task>/{1,2,3}.json only",
            "phase3_hci_labels": "analysis/phase3/hci-ground-truth-labels.json",
            "phase3_attribution": "analysis/phase3/attribution-results.json",
            "phase4_guardrails": str(GUARDRAILS_PATH),
            "hci_study_plan": str(HCI_STUDY_PLAN_PATH),
            "excluded_from_factorial_statistics": "repeat 0 pilot and repeats 301-312/401/403/404 counterfactuals",
        },
        "phase2_gate": phase2_summary,
        "formal_traces": formal_summary,
        "phase3": phase3_summary,
        "guardrails": guardrail_summary,
        "hci_study_plan": hci_study_summary,
        "warnings": warnings,
        "failures": failures,
    }
