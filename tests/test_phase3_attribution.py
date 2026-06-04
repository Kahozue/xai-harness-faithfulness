from __future__ import annotations

import json
from pathlib import Path

from runner import paths
from runner.phase3_attribution import (
    build_phase3_attribution,
    validate_phase3_attribution,
    write_phase3_attribution_outputs,
)


def _seed(index: int, task_id: str, stratum: str, pair: tuple[int, int], success_gap: bool = False) -> dict:
    harness = {
        1: "claude_code",
        2: "opencode",
        3: "hermes",
        4: "opencode",
        5: "hermes",
        6: "codex",
    }
    model = {
        1: "claude-haiku-4-5-20251001",
        2: "claude-haiku-4-5-20251001",
        3: "claude-haiku-4-5-20251001",
        4: "gpt-5.4-mini-2026-03-17",
        5: "gpt-5.4-mini-2026-03-17",
        6: "gpt-5.4-mini-2026-03-17",
    }
    left_success = 1 if success_gap else 3
    right_success = 3
    left_config, right_config = pair
    return {
        "seed_id": f"PH3-DP-{index:03d}",
        "task_id": task_id,
        "task_category": "bug_fix" if task_id.startswith("bugfix") else "benchmark",
        "stratum": stratum,
        "purpose": "test",
        "config_pair": [left_config, right_config],
        "scores": {"selection_score": 0.5, "sequence_divergence": 0.5, "success_gap": 0.666667 if success_gap else 0},
        "left": {
            "config": left_config,
            "harness": harness[left_config],
            "model": model[left_config],
            "success": left_success,
            "n": 3,
            "first_tool_families": {"read": 3},
            "top_family_sequences": [{"sequence": ["read", "edit"], "count": 3}],
            "trace_paths": [f"traces/{left_config}/{task_id}/{repeat}.json" for repeat in (1, 2, 3)],
        },
        "right": {
            "config": right_config,
            "harness": harness[right_config],
            "model": model[right_config],
            "success": right_success,
            "n": 3,
            "first_tool_families": {"search": 3},
            "top_family_sequences": [{"sequence": ["search", "read", "edit"], "count": 3}],
            "trace_paths": [f"traces/{right_config}/{task_id}/{repeat}.json" for repeat in (1, 2, 3)],
        },
    }


def _trace(path: Path, config: int, task_id: str, repeat: int, success: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "config_id": config,
        "task_id": task_id,
        "repeat_index": repeat,
        "harness": "opencode",
        "model_snapshot": "model",
        "tool_calls": [
            {"step": 1, "tool_name": "read", "args_summary": "", "ts": None},
            {"step": 2, "tool_name": "edit", "args_summary": "", "ts": None},
        ],
        "outcome": {"success": success},
        "reasoning_steps": [{"present": True, "type": "reasoning"}],
        "evidence_levels": {"tool_calls": "direct", "reasoning_steps": "direct"},
    }))


def test_phase3_attribution_builds_valid_20_label_hci_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "REPO", tmp_path)
    seeds = [
        _seed(1, "bugfix-t2-03", "haiku_same_model_harness", (2, 3)),
        _seed(2, "task-02", "haiku_same_model_harness", (2, 3)),
        _seed(3, "bugfix-t2-03", "haiku_same_model_harness", (1, 2)),
        _seed(4, "bugfix-t2-03", "gptmini_same_model_harness", (5, 6), success_gap=True),
        _seed(5, "task-05", "gptmini_same_model_harness", (5, 6)),
        _seed(6, "task-06", "gptmini_same_model_harness", (4, 6)),
        _seed(7, "task-07", "opencode_model_swap", (2, 4), success_gap=True),
        _seed(8, "task-08", "opencode_model_swap", (2, 4), success_gap=True),
        _seed(9, "task-09", "opencode_model_swap", (2, 4), success_gap=True),
        _seed(10, "task-10", "hermes_model_swap", (3, 5)),
        _seed(11, "task-11", "hermes_model_swap", (3, 5), success_gap=True),
        _seed(12, "task-12", "hermes_model_swap", (3, 5)),
    ]
    manifest = tmp_path / "analysis" / "phase3" / "decision-point-seeds.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"selected": seeds}))

    for seed in seeds:
        repeat = 300 + int(seed["seed_id"].split("-")[-1])
        for side in ("left", "right"):
            cfg = seed[side]["config"]
            _trace(tmp_path / "traces" / str(cfg) / seed["task_id"] / f"{repeat}.json", cfg, seed["task_id"], repeat, True)
        if seed["task_id"] == "bugfix-t2-03":
            semantic_repeat = 400 + int(seed["seed_id"].split("-")[-1])
            for side in ("left", "right"):
                cfg = seed[side]["config"]
                _trace(tmp_path / "traces" / str(cfg) / seed["task_id"] / f"{semantic_repeat}.json", cfg, seed["task_id"], semantic_repeat, True)

    attribution = build_phase3_attribution(manifest)
    validation = validate_phase3_attribution(attribution)

    assert validation["ok"] is True
    assert attribution["hci_label_count"] == 20
    assert {label["factorial_label"] for label in attribution["hci_labels"]} <= {
        "harness_main_effect",
        "model_main_effect",
        "interaction",
        "noise",
    }
    assert any(label["decision_kind"] == "semantic_output_convention" for label in attribution["hci_labels"])

    attribution_path, hci_path, report_path = write_phase3_attribution_outputs(attribution)
    assert json.loads(hci_path.read_text())["label_count"] == 20
    assert "Phase 3 completion report" in report_path.read_text()
    assert attribution_path.exists()
