from __future__ import annotations

import json
from pathlib import Path

from runner import paths
from runner.phase4_readiness import scan_public_hidden_reasoning_payloads, validate_phase4_readiness


TASKS = [f"task-{index:02d}" for index in range(1, 21)]
CONFIG_HARNESS = {
    1: "claude_code",
    2: "opencode",
    3: "hermes",
    4: "opencode",
    5: "hermes",
    6: "codex",
}
CONFIG_MODEL = {
    1: "claude-haiku-4-5-20251001",
    2: "claude-haiku-4-5-20251001",
    3: "claude-haiku-4-5-20251001",
    4: "gpt-5.4-mini-2026-03-17",
    5: "gpt-5.4-mini-2026-03-17",
    6: "gpt-5.4-mini-2026-03-17",
}


def _write_trace(root: Path, config: int, task_id: str, repeat: int) -> str:
    path = root / "traces" / str(config) / task_id / f"{repeat}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "config_id": config,
        "harness": CONFIG_HARNESS[config],
        "model_snapshot": CONFIG_MODEL[config],
        "task_id": task_id,
        "task_category": "bug_fix",
        "repeat_index": repeat,
        "decision_points": [],
        "tool_calls": [{"step": 1, "tool_name": "read", "args_summary": "path=x.py", "ts": None}],
        "outcome": {"success": True},
    }))
    return str(path.relative_to(root))


def _seed(index: int, task_id: str, pair: tuple[int, int], stratum: str) -> dict:
    left, right = pair
    return {
        "seed_id": f"PH3-DP-{index:03d}",
        "task_id": task_id,
        "task_category": "bug_fix",
        "stratum": stratum,
        "config_pair": [left, right],
        "scores": {"selection_score": 1, "sequence_divergence": 1, "success_gap": 0},
        "left": {
            "config": left,
            "harness": CONFIG_HARNESS[left],
            "model": CONFIG_MODEL[left],
            "success": 3,
            "n": 3,
            "trace_paths": [f"traces/{left}/{task_id}/{repeat}.json" for repeat in (1, 2, 3)],
        },
        "right": {
            "config": right,
            "harness": CONFIG_HARNESS[right],
            "model": CONFIG_MODEL[right],
            "success": 3,
            "n": 3,
            "trace_paths": [f"traces/{right}/{task_id}/{repeat}.json" for repeat in (1, 2, 3)],
        },
    }


def _label(seed: dict, suffix: str) -> dict:
    return {
        "label_id": f"{seed['seed_id']}-{suffix}",
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
        "decision_kind": "initial_tool_strategy",
        "factorial_label": "harness_main_effect",
        "detail_label": "tool_path_style",
        "confidence": "high",
        "method_agreement": {
            "labels": {"harness_main_effect": 4},
            "primary_label": "harness_main_effect",
            "agreement_count": 4,
            "method_count": 4,
            "unanimous": True,
        },
        "contrast": {},
    }


def _decision(seed: dict, suffix: str) -> dict:
    repeat = 300 + int(seed["seed_id"].split("-")[-1])
    left_cfg, right_cfg = seed["config_pair"]
    return {
        "decision_point_id": f"{seed['seed_id']}-{suffix}",
        "methods": [
            {"method": "M1", "evidence_level": "source-derived", "attribution": "harness_main_effect"},
            {"method": "M2", "evidence_level": "source-derived", "attribution": "harness_main_effect"},
            {
                "method": "M3",
                "evidence_level": "direct-run",
                "attribution": "harness_main_effect",
                "left_counterfactual": {
                    "config": left_cfg,
                    "repeat": repeat,
                    "exists": True,
                    "trace": f"traces/{left_cfg}/{seed['task_id']}/{repeat}.json",
                },
                "right_counterfactual": {
                    "config": right_cfg,
                    "repeat": repeat,
                    "exists": True,
                    "trace": f"traces/{right_cfg}/{seed['task_id']}/{repeat}.json",
                },
            },
            {"method": "M4", "evidence_level": "direct", "attribution": "harness_main_effect"},
        ],
    }


def _write_ready_repo(root: Path) -> None:
    for config in range(1, 7):
        for task_id in TASKS:
            for repeat in (1, 2, 3):
                _write_trace(root, config, task_id, repeat)
    _write_trace(root, 1, TASKS[0], 0)

    strata = [
        ("haiku_same_model_harness", (1, 2)),
        ("gptmini_same_model_harness", (4, 5)),
        ("opencode_model_swap", (2, 4)),
        ("hermes_model_swap", (3, 5)),
    ]
    seeds = []
    for index in range(1, 13):
        stratum, pair = strata[(index - 1) // 3]
        task_id = TASKS[index - 1]
        seed = _seed(index, task_id, pair, stratum)
        seeds.append(seed)
        repeat = 300 + index
        _write_trace(root, pair[0], task_id, repeat)
        _write_trace(root, pair[1], task_id, repeat)

    labels = []
    seed_records = []
    for index, seed in enumerate(seeds, start=1):
        count = 2 if index <= 8 else 1
        decisions = []
        for suffix_index in range(count):
            suffix = chr(ord("A") + suffix_index)
            labels.append(_label(seed, suffix))
            decisions.append(_decision(seed, suffix))
        seed_records.append({
            "seed_id": seed["seed_id"],
            "task_id": seed["task_id"],
            "config_pair": seed["config_pair"],
            "decision_points": decisions,
        })

    phase3 = root / "analysis" / "phase3"
    phase3.mkdir(parents=True, exist_ok=True)
    (phase3 / "decision-point-seeds.json").write_text(json.dumps({
        "source": {"formal_repeats": [1, 2, 3], "trace_count": 360, "candidate_count": 160},
        "selected": seeds,
    }))
    attribution = {
        "selected_seed_count": 12,
        "decision_point_count": 20,
        "hci_label_count": 20,
        "method_boundary": {"M1": "", "M2": "", "M3": "", "M4": ""},
        "seeds": seed_records,
        "hci_labels": labels,
    }
    (phase3 / "attribution-results.json").write_text(json.dumps(attribution))
    (phase3 / "hci-ground-truth-labels.json").write_text(json.dumps({
        "label_count": 20,
        "labels": labels,
    }))
    fixtures = root / "tests" / "fixtures"
    fixtures.mkdir(parents=True)
    (fixtures / "safe.json").write_text('{"messages":[{"role":"assistant","reasoning":"[redacted hidden reasoning]"}]}')
    guardrails = root / "docs" / "specs" / "2026-06-04-phase4-analysis-guardrails.md"
    guardrails.parent.mkdir(parents=True, exist_ok=True)
    guardrails.write_text(
        "\n".join([
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
        ])
    )
    hci_study_plan = root / "docs" / "specs" / "2026-06-04-hci-human-study-plan.md"
    hci_study_plan.write_text(
        "\n".join([
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
        ])
    )


def test_phase4_readiness_accepts_complete_phase2_phase3_inputs(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "REPO", tmp_path)
    _write_ready_repo(tmp_path)
    monkeypatch.setattr(
        "runner.phase4_readiness.validate_phase2",
        lambda repeat_start, repeats: {
            "ok": True,
            "expected_traces": 360,
            "found_traces": 360,
            "failures": {},
        },
    )

    report = validate_phase4_readiness()

    assert report["ok"] is True
    assert report["formal_traces"]["formal_trace_count"] == 360
    assert report["phase3"]["hci_label_count"] == 20
    assert report["guardrails"]["present"] is True
    assert report["hci_study_plan"]["present"] is True
    assert report["warnings"][0]["check"] == "nonformal_repeats_present_for_pilot_or_phase3_context_only"


def test_phase4_readiness_rejects_missing_hci_study_plan(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "REPO", tmp_path)
    _write_ready_repo(tmp_path)
    (tmp_path / "docs" / "specs" / "2026-06-04-hci-human-study-plan.md").unlink()
    monkeypatch.setattr(
        "runner.phase4_readiness.validate_phase2",
        lambda repeat_start, repeats: {
            "ok": True,
            "expected_traces": 360,
            "found_traces": 360,
            "failures": {},
        },
    )

    report = validate_phase4_readiness()

    assert report["ok"] is False
    checks = {failure["check"] for failure in report["failures"]}
    assert "hci_study_plan_exists" in checks


def test_phase4_readiness_rejects_hci_label_that_points_to_pilot_repeat(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "REPO", tmp_path)
    _write_ready_repo(tmp_path)
    hci_path = tmp_path / "analysis" / "phase3" / "hci-ground-truth-labels.json"
    hci = json.loads(hci_path.read_text())
    hci["labels"][0]["left"]["baseline_traces"][0] = "traces/1/task-01/0.json"
    hci_path.write_text(json.dumps(hci))
    attribution_path = tmp_path / "analysis" / "phase3" / "attribution-results.json"
    attribution = json.loads(attribution_path.read_text())
    attribution["hci_labels"] = hci["labels"]
    attribution_path.write_text(json.dumps(attribution))
    monkeypatch.setattr(
        "runner.phase4_readiness.validate_phase2",
        lambda repeat_start, repeats: {"ok": True, "expected_traces": 360, "found_traces": 360, "failures": {}},
    )

    report = validate_phase4_readiness()

    assert report["ok"] is False
    checks = {failure["check"] for failure in report["failures"]}
    assert "hci_label_left_baseline_repeat" in checks


def test_public_hygiene_scan_flags_hidden_reasoning_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "REPO", tmp_path)
    fixtures = tmp_path / "tests" / "fixtures"
    fixtures.mkdir(parents=True)
    (fixtures / "bad.jsonl").write_text('{"delta":{"type":"thinking_delta","thinking":"raw"}}\n')

    failures = scan_public_hidden_reasoning_payloads()

    assert failures
    assert failures[0]["pattern"] == "thinking_delta"
