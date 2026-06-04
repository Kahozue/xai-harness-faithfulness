from __future__ import annotations

import json
from pathlib import Path

from runner import paths
from runner.configs import CONFIGS
from runner.phase4_analysis import build_phase4_analysis, write_phase4_outputs
import runner.provision as provision


def _trace(
    config_id: int,
    task_id: str,
    category: str,
    repeat: int,
    tools: list[str],
    success: bool,
) -> dict:
    config = next(config for config in CONFIGS if config.id == config_id)
    return {
        "run_id": f"c{config_id}__{task_id}__r{repeat}",
        "config_id": config_id,
        "harness": config.harness,
        "harness_version": f"{config.harness}-test",
        "model": config.model_snapshot,
        "model_snapshot": config.model_snapshot,
        "task_id": task_id,
        "task_category": category,
        "repeat_index": repeat,
        "reasoning_effort": "high",
        "tool_calls": [
            {"step": index, "tool_name": tool, "args_summary": "", "ts": None}
            for index, tool in enumerate(tools, start=1)
        ],
        "reasoning_steps": [],
        "decision_points": [],
        "outcome": {
            "success": success,
            "grader_detail": "ok" if success else "failed",
            "final_diff_path": None,
        },
        "tokens": {"input": 1, "cached_input": 0, "output": 2},
        "wall_time_s": 10.0 + config_id,
        "turns": len(tools),
        "runtime_budget": {
            "max_output_tokens": 64000 if config_id == 1 else None,
            "thinking_budget_tokens": 63999 if config_id == 1 else None,
            "context_window_tokens": 200000 if config_id == 1 else None,
            "effort_source": "test",
        },
        "system_present": None,
        "raw_log_path": f"/data/harness-lab/runs/{config_id}/{task_id}/{repeat}/raw",
        "private_audit_path": f"/data/harness-lab/private-audits/{config_id}/{task_id}/{repeat}.md",
        "env_lock_ref": "ENVIRONMENT.lock.md",
        "timestamp": "2026-06-04T00:00:00Z",
        "evidence_levels": {"tool_calls": "direct"},
        "_trace_path": f"traces/{config_id}/{task_id}/{repeat}.json",
    }


def _write_repo_fixture(tmp_path: Path, monkeypatch) -> list[dict]:
    monkeypatch.setattr(paths, "REPO", tmp_path)
    registry = tmp_path / "tasks" / "registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        """
tasks:
  - id: bugfix-t2-01
    category: bug_fix
    tier: 2
    source: controlled
    repo_baseline: tasks/target_repo
    prompt: Fix parse_amount.
    grader: {type: pytest}
    provenance: controlled test
  - id: bench-grade-school
    category: benchmark
    tier: 1
    source: aider_polyglot
    repo_baseline: tasks/benchmark/grade-school/baseline
    prompt: Implement the grade school roster.
    grader: {type: pytest}
    provenance: benchmark test
""".strip()
        + "\n"
    )
    monkeypatch.setattr(provision, "REGISTRY", registry)

    traces: list[dict] = []
    for config_id in range(1, 7):
        for task_id, category in (("bugfix-t2-01", "bug_fix"), ("bench-grade-school", "benchmark")):
            for repeat in (1, 2, 3):
                if config_id in {1, 3, 5}:
                    tools = ["Read", "Edit", "Bash"]
                elif config_id in {2, 4}:
                    tools = ["Bash", "Read", "Edit"]
                else:
                    tools = ["read_file", "apply_patch"]
                success = not (task_id == "bench-grade-school" and config_id in {4, 6})
                trace = _trace(config_id, task_id, category, repeat, tools, success)
                trace_path = tmp_path / trace["_trace_path"]
                trace_path.parent.mkdir(parents=True, exist_ok=True)
                trace_path.write_text(json.dumps({k: v for k, v in trace.items() if k != "_trace_path"}))
                traces.append(trace)

    labels = [
        {
            "label_id": "PH3-DP-001-A",
            "seed_id": "PH3-DP-001",
            "task_id": "bugfix-t2-01",
            "task_category": "bug_fix",
            "factorial_label": "harness_main_effect",
            "decision_kind": "initial_tool_strategy",
            "detail_label": "tool_path_style",
            "confidence": "high",
            "config_pair": [1, 2],
            "left": {
                "config": 1,
                "harness": "claude_code",
                "model": CONFIGS[0].model_snapshot,
                "baseline_traces": [f"traces/1/bugfix-t2-01/{repeat}.json" for repeat in (1, 2, 3)],
            },
            "right": {
                "config": 2,
                "harness": "opencode",
                "model": CONFIGS[1].model_snapshot,
                "baseline_traces": [f"traces/2/bugfix-t2-01/{repeat}.json" for repeat in (1, 2, 3)],
            },
            "method_agreement": {
                "agreement_count": 4,
                "method_count": 4,
                "primary_label": "harness_main_effect",
                "unanimous": True,
            },
        },
        {
            "label_id": "PH3-DP-002-A",
            "seed_id": "PH3-DP-002",
            "task_id": "bench-grade-school",
            "task_category": "benchmark",
            "factorial_label": "model_main_effect",
            "decision_kind": "task_success_gap",
            "detail_label": "success_gap",
            "confidence": "medium",
            "config_pair": [4, 6],
            "left": {
                "config": 4,
                "harness": "opencode",
                "model": CONFIGS[3].model_snapshot,
                "baseline_traces": [f"traces/4/bench-grade-school/{repeat}.json" for repeat in (1, 2, 3)],
            },
            "right": {
                "config": 6,
                "harness": "codex",
                "model": CONFIGS[5].model_snapshot,
                "baseline_traces": [f"traces/6/bench-grade-school/{repeat}.json" for repeat in (1, 2, 3)],
            },
            "method_agreement": {
                "agreement_count": 3,
                "method_count": 4,
                "primary_label": "model_main_effect",
                "unanimous": False,
            },
        },
    ]
    phase3 = tmp_path / "analysis" / "phase3"
    phase3.mkdir(parents=True)
    (phase3 / "attribution-results.json").write_text(json.dumps({
        "hci_label_count": len(labels),
        "hci_labels": labels,
        "method_boundary": {"M1": "source", "M2": "source", "M3": "direct", "M4": "trace"},
    }))
    (phase3 / "hci-ground-truth-labels.json").write_text(json.dumps({
        "label_count": len(labels),
        "labels": labels,
    }))
    return traces


def test_phase4_analysis_builds_fine_grained_metrics(monkeypatch, tmp_path):
    traces = _write_repo_fixture(tmp_path, monkeypatch)

    analysis = build_phase4_analysis(traces=traces, run_readiness_gate=False)

    assert analysis["overall"]["formal_trace_count"] == 36
    assert len(analysis["category_summaries"]) == 2
    assert len(analysis["task_summaries"]) == 2
    assert len(analysis["cell_summaries"]) == 12
    assert len(analysis["pairwise"]["observations"]) == 30
    assert analysis["environment_controls"]["configs"][0]["private_audit_paths_present"] == 6
    assert analysis["hci_boundary"]["human_study_status"] == "not_claimed_in_phase4_metrics"


def test_write_phase4_outputs_includes_support_artifacts(monkeypatch, tmp_path):
    traces = _write_repo_fixture(tmp_path, monkeypatch)
    analysis = build_phase4_analysis(traces=traces, run_readiness_gate=False)

    outputs = write_phase4_outputs(analysis)

    assert outputs["analysis"].exists()
    assert outputs["report"].exists()
    assert outputs["support_report"].exists()
    assert outputs["hci_case_pack"].exists()
    assert outputs["traceability"].exists()
    for figure in outputs["figures"].values():
        assert (tmp_path / figure).exists()

    hci_case_pack = json.loads(outputs["hci_case_pack"].read_text())
    assert hci_case_pack["cases"][0]["condition_a_summary_only"]
    assert hci_case_pack["cases"][0]["condition_b_evidence_limitation_action"]
    assert hci_case_pack["procedure_support"]["design"].startswith("within-subject")

    traceability = json.loads(outputs["traceability"].read_text())
    assert traceability["coverage_summary"]["requirements"] >= 8
    assert any(row["status"] == "materials_prepared_human_responses_still_required" for row in traceability["rows"])
    assert "15-slide support outline" in outputs["support_report"].read_text()
