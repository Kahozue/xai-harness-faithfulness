"""Command line entrypoint for the Phase 1 runner."""
from __future__ import annotations

import argparse
import json

from runner.runner import DEFAULT_TIMEOUT_S, run_once

DEFAULT_PILOT_CONFIGS = [1, 6]
DEFAULT_PILOT_TASKS = ["bugfix-t2-01", "rename-t2-01", "bench-grade-school"]


def _summary(trace: dict) -> dict:
    return {
        "run_id": trace["run_id"],
        "success": trace["outcome"]["success"],
        "tools": [tc["tool_name"] for tc in trace["tool_calls"]],
        "wall_time_s": trace["wall_time_s"],
        "trace": f"traces/{trace['config_id']}/{trace['task_id']}/{trace['repeat_index']}.json",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run one (config, task, repeat)")
    run.add_argument("--config", type=int, required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--repeat", type=int, default=0)
    run.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)

    pilot = sub.add_parser("pilot", help="run or list the default 2 config x 3 task pilot")
    pilot.add_argument("--repeat", type=int, default=0)
    pilot.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    pilot.add_argument("--dry-list", action="store_true", help="print planned runs without launching harnesses")

    args = parser.parse_args(argv)
    if args.cmd == "run":
        trace = run_once(args.config, args.task, args.repeat, args.timeout)
        print(json.dumps(_summary(trace), ensure_ascii=False))
        return 0

    if args.cmd == "pilot":
        planned = [
            {"config": config_id, "task": task_id, "repeat": args.repeat}
            for config_id in DEFAULT_PILOT_CONFIGS
            for task_id in DEFAULT_PILOT_TASKS
        ]
        if args.dry_list:
            print(json.dumps({"planned": planned}, ensure_ascii=False, indent=2))
            return 0
        results = [
            _summary(run_once(item["config"], item["task"], item["repeat"], args.timeout))
            for item in planned
        ]
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
