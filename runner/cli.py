"""Command line entrypoint for the Phase 1 runner."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from runner import persist
from runner.configs import CONFIGS
from runner.phase3_selection import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_PER_STRATUM,
    DEFAULT_REPORT_PATH,
    build_phase3_seed_manifest,
    write_phase3_seed_outputs,
)
from runner.phase3_attribution import (
    DEFAULT_ATTRIBUTION_PATH,
    DEFAULT_HCI_LABELS_PATH,
    DEFAULT_REPORT_PATH as DEFAULT_PHASE3_ATTRIBUTION_REPORT_PATH,
    build_phase3_attribution,
    validate_phase3_attribution,
    write_phase3_attribution_outputs,
)
from runner.provision import load_tasks
from runner.phase2_validation import validate_phase2
from runner.runner import DEFAULT_TIMEOUT_S, run_once

DEFAULT_PILOT_CONFIGS = [1, 6]
DEFAULT_PILOT_TASKS = ["bugfix-t2-01", "rename-t2-01", "bench-grade-school"]
DEFAULT_PHASE2_REPEATS = 3
DEFAULT_PHASE2_REPEAT_START = 1


def _summary(trace: dict) -> dict:
    return {
        "run_id": trace["run_id"],
        "success": trace["outcome"]["success"],
        "tools": [tc["tool_name"] for tc in trace["tool_calls"]],
        "wall_time_s": trace["wall_time_s"],
        "trace": f"traces/{trace['config_id']}/{trace['task_id']}/{trace['repeat_index']}.json",
        "private_audit": trace.get("private_audit_path"),
    }


def _phase2_plan(
    repeat_start: int = DEFAULT_PHASE2_REPEAT_START,
    repeats: int = DEFAULT_PHASE2_REPEATS,
    config_ids: list[int] | None = None,
    task_ids: list[str] | None = None,
) -> list[dict]:
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


def _existing(planned: list[dict]) -> list[str]:
    return [
        str(path)
        for item in planned
        if (path := persist.trace_path(item["config"], item["task"], item["repeat"])).exists()
    ]


def _prompt_suffix(inline: str | None, file_path: str | None) -> str | None:
    if inline and file_path:
        raise ValueError("use either --prompt-suffix or --prompt-suffix-file, not both")
    if file_path:
        return Path(file_path).read_text()
    return inline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run one (config, task, repeat)")
    run.add_argument("--config", type=int, required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--repeat", type=int, default=0)
    run.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    run.add_argument("--overwrite", action="store_true", help="intentionally replace an existing trace")
    run.add_argument("--prompt-suffix", help="append a Phase 3 counterfactual instruction to the task prompt")
    run.add_argument("--prompt-suffix-file", help="append a Phase 3 counterfactual instruction read from a file")
    run.add_argument("--intervention-id", help="stable Phase 3 intervention id recorded in the trace")
    run.add_argument("--intervention-method", help="Phase 3 method label such as M3")
    run.add_argument("--intervention-note", help="short public note recorded in the trace")

    pilot = sub.add_parser("pilot", help="run or list the default 2 config x 3 task pilot")
    pilot.add_argument("--repeat", type=int, default=0)
    pilot.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    pilot.add_argument("--overwrite", action="store_true", help="intentionally replace existing traces")
    pilot.add_argument("--dry-list", action="store_true", help="print planned runs without launching harnesses")

    phase2 = sub.add_parser("phase2", help="run or list the Phase 2 full factorial batch")
    phase2.add_argument("--repeat-start", type=int, default=DEFAULT_PHASE2_REPEAT_START)
    phase2.add_argument("--repeats", type=int, default=DEFAULT_PHASE2_REPEATS)
    phase2.add_argument("--config", type=int, action="append", dest="configs", help="limit to a config id; repeatable")
    phase2.add_argument("--task", action="append", dest="tasks", help="limit to a task id; repeatable")
    phase2.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    phase2.add_argument("--overwrite", action="store_true", help="intentionally replace existing traces")
    phase2.add_argument("--skip-existing", action="store_true", help="resume by omitting runs whose trace already exists")
    phase2.add_argument("--continue-on-error", action="store_true", help="continue the batch after one run raises")
    phase2.add_argument("--dry-list", action="store_true", help="print planned runs without launching harnesses")

    phase2_validate = sub.add_parser("phase2-validate", help="validate Phase 2 formal trace readiness")
    phase2_validate.add_argument("--repeat-start", type=int, default=DEFAULT_PHASE2_REPEAT_START)
    phase2_validate.add_argument("--repeats", type=int, default=DEFAULT_PHASE2_REPEATS)
    phase2_validate.add_argument("--config", type=int, action="append", dest="configs", help="limit to a config id; repeatable")
    phase2_validate.add_argument("--task", action="append", dest="tasks", help="limit to a task id; repeatable")
    phase2_validate.add_argument("--indent", type=int, default=2, help="JSON indentation; use 0 for one line")

    phase3_select = sub.add_parser(
        "phase3-select",
        help="select high-divergence Phase 2 seeds for Phase 3 M1-M4 attribution",
    )
    phase3_select.add_argument("--per-stratum", type=int, default=DEFAULT_PER_STRATUM)
    phase3_select.add_argument("--output", default=str(DEFAULT_MANIFEST_PATH))
    phase3_select.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    phase3_select.add_argument("--dry-run", action="store_true", help="print the manifest without writing files")
    phase3_select.add_argument("--indent", type=int, default=2, help="JSON indentation; use 0 for one line")

    phase3_attr = sub.add_parser(
        "phase3-attribution",
        help="build Phase 3 M1-M4 attribution records and HCI ground-truth labels",
    )
    phase3_attr.add_argument("--seed-manifest", default=str(DEFAULT_MANIFEST_PATH))
    phase3_attr.add_argument("--output", default=str(DEFAULT_ATTRIBUTION_PATH))
    phase3_attr.add_argument("--hci-labels", default=str(DEFAULT_HCI_LABELS_PATH))
    phase3_attr.add_argument("--report", default=str(DEFAULT_PHASE3_ATTRIBUTION_REPORT_PATH))
    phase3_attr.add_argument("--dry-run", action="store_true", help="print the attribution JSON without writing files")
    phase3_attr.add_argument("--indent", type=int, default=2, help="JSON indentation; use 0 for one line")

    args = parser.parse_args(argv)
    if args.cmd == "run":
        try:
            prompt_suffix = _prompt_suffix(args.prompt_suffix, args.prompt_suffix_file)
        except ValueError as exc:
            print(json.dumps({"error": "invalid_intervention", "detail": str(exc)}, ensure_ascii=False))
            return 2
        intervention = {
            key: value for key, value in {
                "id": args.intervention_id,
                "method": args.intervention_method,
                "note": args.intervention_note,
            }.items() if value
        } or None
        try:
            trace = run_once(
                args.config,
                args.task,
                args.repeat,
                args.timeout,
                overwrite=args.overwrite,
                prompt_suffix=prompt_suffix,
                intervention=intervention,
            )
        except FileExistsError as exc:
            print(json.dumps({"error": "trace_exists", "detail": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps(_summary(trace), ensure_ascii=False))
        return 0

    if args.cmd == "pilot":
        planned = [
            {"config": config_id, "task": task_id, "repeat": args.repeat}
            for config_id in DEFAULT_PILOT_CONFIGS
            for task_id in DEFAULT_PILOT_TASKS
        ]
        if args.dry_list:
            print(json.dumps({"count": len(planned), "planned": planned}, ensure_ascii=False, indent=2))
            return 0
        if not args.overwrite:
            existing = _existing(planned)
            if existing:
                print(json.dumps({"error": "trace_exists", "existing": existing}, ensure_ascii=False, indent=2))
                return 1
        results = [
            _summary(run_once(item["config"], item["task"], item["repeat"], args.timeout, overwrite=args.overwrite))
            for item in planned
        ]
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "phase2":
        try:
            planned = _phase2_plan(args.repeat_start, args.repeats, args.configs, args.tasks)
        except ValueError as exc:
            print(json.dumps({"error": "invalid_plan", "detail": str(exc)}, ensure_ascii=False))
            return 2
        existing = _existing(planned)
        planned_to_run = [
            item
            for item in planned
            if not persist.trace_path(item["config"], item["task"], item["repeat"]).exists()
        ] if args.skip_existing else planned
        payload = {
            "count": len(planned_to_run),
            "total_planned": len(planned),
            "repeat_start": args.repeat_start,
            "repeats": args.repeats,
            "skipped_existing": len(planned) - len(planned_to_run),
            "planned": planned_to_run,
        }
        if args.dry_list:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if existing and not (args.overwrite or args.skip_existing):
            print(json.dumps({"error": "trace_exists", "existing": existing}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({
            "event": "phase2_start",
            "count": len(planned_to_run),
            "total_planned": len(planned),
            "skipped_existing": len(planned) - len(planned_to_run),
        }, ensure_ascii=False), flush=True)
        results = []
        errors = []
        for item in planned_to_run:
            print(json.dumps({"event": "phase2_run_start", **item}, ensure_ascii=False), flush=True)
            try:
                summary = _summary(
                    run_once(item["config"], item["task"], item["repeat"], args.timeout, overwrite=args.overwrite)
                )
            except Exception as exc:  # pragma: no cover - exercised through CLI behavior in long batches
                error = {
                    "event": "phase2_run_error",
                    **item,
                    "error": type(exc).__name__,
                    "detail": str(exc),
                }
                errors.append(error)
                print(json.dumps(error, ensure_ascii=False), flush=True)
                if not args.continue_on_error:
                    print(json.dumps({
                        "event": "phase2_aborted",
                        "completed": len(results),
                        "errors": len(errors),
                    }, ensure_ascii=False), flush=True)
                    return 1
                continue
            results.append(summary)
            print(json.dumps({"event": "phase2_run_result", **summary}, ensure_ascii=False), flush=True)
        print(json.dumps({
            "event": "phase2_complete",
            "completed": len(results),
            "errors": len(errors),
        }, ensure_ascii=False), flush=True)
        return 0 if not errors else 1

    if args.cmd == "phase2-validate":
        try:
            report = validate_phase2(
                repeat_start=args.repeat_start,
                repeats=args.repeats,
                config_ids=args.configs,
                task_ids=args.tasks,
            )
        except ValueError as exc:
            print(json.dumps({"ok": False, "error": "invalid_plan", "detail": str(exc)}, ensure_ascii=False))
            return 2
        indent = None if args.indent == 0 else args.indent
        print(json.dumps(report, ensure_ascii=False, indent=indent, sort_keys=True))
        return 0 if report["ok"] else 1

    if args.cmd == "phase3-select":
        try:
            manifest = build_phase3_seed_manifest(per_stratum=args.per_stratum)
        except ValueError as exc:
            print(json.dumps({"ok": False, "error": "invalid_plan", "detail": str(exc)}, ensure_ascii=False))
            return 2
        indent = None if args.indent == 0 else args.indent
        if args.dry_run:
            print(json.dumps(manifest, ensure_ascii=False, indent=indent, sort_keys=True))
            return 0
        manifest_path, report_path = write_phase3_seed_outputs(manifest, args.output, args.report)
        print(json.dumps({
            "ok": True,
            "selected": len(manifest["selected"]),
            "candidates": len(manifest["candidates"]),
            "manifest": str(manifest_path),
            "report": str(report_path),
        }, ensure_ascii=False, indent=indent, sort_keys=True))
        return 0

    if args.cmd == "phase3-attribution":
        attribution = build_phase3_attribution(args.seed_manifest)
        validation = validate_phase3_attribution(attribution)
        indent = None if args.indent == 0 else args.indent
        if args.dry_run:
            print(json.dumps({**attribution, "validation": validation}, ensure_ascii=False, indent=indent, sort_keys=True))
            return 0 if validation["ok"] else 1
        attribution_path, hci_path, report_path = write_phase3_attribution_outputs(
            attribution,
            args.output,
            args.hci_labels,
            args.report,
        )
        print(json.dumps({
            "ok": validation["ok"],
            "failures": validation["failures"],
            "selected_seeds": attribution["selected_seed_count"],
            "decision_points": attribution["decision_point_count"],
            "hci_labels": attribution["hci_label_count"],
            "attribution": str(attribution_path),
            "hci_ground_truth_labels": str(hci_path),
            "report": str(report_path),
        }, ensure_ascii=False, indent=indent, sort_keys=True))
        return 0 if validation["ok"] else 1

    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
