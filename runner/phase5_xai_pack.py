"""Phase 5 XAI presentation data-pack generation.

This module prepares slide-ready data, chart assets, and source mappings for
the XAI deck. It intentionally does not create or modify any PPTX file.
"""
from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from runner import paths
from runner.configs import CONFIGS
from runner.phase4_analysis import _config_label
from runner.provision import load_tasks

DEFAULT_PACK_DIR = Path("analysis") / "phase5" / "xai-presentation-pack"
PHASE4_METRICS = Path("analysis") / "phase4" / "metrics-summary.json"
PHASE4_CASE_PACK = Path("analysis") / "phase4" / "hci-case-pack.json"
PHASE3_LABELS = Path("analysis") / "phase3" / "hci-ground-truth-labels.json"
PRESENTATION_STRUCTURE = Path("docs") / "specs" / "2026-06-04-phase5-xai-presentation-structure.md"

SOURCE_FILES = {
    "phase5_structure": str(PRESENTATION_STRUCTURE),
    "phase4_metrics": str(PHASE4_METRICS),
    "phase4_case_pack": str(PHASE4_CASE_PACK),
    "phase3_labels": str(PHASE3_LABELS),
    "phase4_report": "docs/verification/2026-06-04-phase4-analysis-report.md",
    "registry": "tasks/registry.yaml",
}

EXISTING_PHASE4_CHARTS = {
    "jaccard_matrix": {
        "path": "analysis/phase4/figures/jaccard-matrix.svg",
        "slide": 15,
        "use": "RQ3: how large the harness/model tool-set differences are.",
    },
    "factorial_contrast_bars": {
        "path": "analysis/phase4/figures/factorial-contrast-bars.svg",
        "slide": 16,
        "use": "RQ3: descriptive contrast across harness/model/mixed comparisons.",
    },
    "disagreement_success_scatter": {
        "path": "analysis/phase4/figures/disagreement-success-scatter.svg",
        "slide": 17,
        "use": "RQ2: sequence disagreement is almost unrelated to success gap here.",
    },
    "method_consistency": {
        "path": "analysis/phase4/figures/method-consistency.svg",
        "slide": 18,
        "use": "RQ1: M1-M4 agreement over selected high-divergence decision points.",
    },
    "agent_card_matrix": {
        "path": "analysis/phase4/figures/agent-card-matrix.svg",
        "slide": 19,
        "use": "RQ4: condensed descriptive agent-card proxy dimensions.",
    },
}

PALETTE = {
    "ink": "#1f2933",
    "muted": "#64748b",
    "line": "#d7dee8",
    "panel": "#f7f9fc",
    "paper": "#ffffff",
    "teal": "#0f8b8d",
    "coral": "#e45756",
    "amber": "#f2a541",
    "green": "#4f9d69",
    "violet": "#7b5ea7",
    "blue": "#3b6ea8",
    "slate": "#475569",
}


def _repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else paths.REPO / path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO))
    except ValueError:
        return str(path)


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(_repo_path(path).read_text())


def _round(value: float | int | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _pct(value: float | int | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.{digits}f}%"


def _success(trace: dict[str, Any]) -> bool:
    return bool((trace.get("outcome") or {}).get("success") is True)


def _formal_trace_paths() -> list[Path]:
    return sorted(
        path
        for path in (_repo_path("traces")).glob("*/*/*.json")
        if path.stem in {"1", "2", "3"}
    )


def _all_trace_counts() -> dict[str, Any]:
    counts = Counter()
    by_repeat = Counter()
    by_config = Counter()
    for path in sorted((_repo_path("traces")).glob("*/*/*.json")):
        config_id = path.parts[-3]
        repeat = path.stem
        by_config[config_id] += 1
        by_repeat[repeat] += 1
        if repeat in {"1", "2", "3"}:
            counts["formal_baseline"] += 1
        elif repeat == "0":
            counts["pilot"] += 1
        else:
            counts["phase3_counterfactual_or_extra"] += 1
    return {
        "total_public_trace_json": sum(counts.values()),
        "classes": dict(counts),
        "by_config": dict(sorted(by_config.items(), key=lambda item: int(item[0]))),
        "by_repeat": dict(sorted(by_repeat.items(), key=lambda item: int(item[0]))),
    }


def _safe_filename(value: str) -> str:
    return (
        value.lower()
        .replace("_", "-")
        .replace("/", "-")
        .replace(" ", "-")
        .replace(":", "")
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _strip_trailing_whitespace(path: Path) -> None:
    text = path.read_text()
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n")


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _svg(width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" fill="{PALETTE['paper']}"/>
<style>
  text {{ font-family: Arial, Helvetica, sans-serif; fill: {PALETTE['ink']}; }}
  .title {{ font-size: 28px; font-weight: 700; }}
  .subtitle {{ font-size: 15px; fill: {PALETTE['muted']}; }}
  .label {{ font-size: 14px; }}
  .small {{ font-size: 12px; fill: {PALETTE['muted']}; }}
  .axis {{ stroke: {PALETTE['line']}; stroke-width: 1; }}
</style>
{body}
</svg>
"""


def _text(x: float, y: float, text: Any, css: str = "label", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{css}" text-anchor="{anchor}">{_e(text)}</text>'


def _wrap(text: str, max_chars: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _bar_chart(
    title: str,
    subtitle: str,
    rows: list[dict[str, Any]],
    label_key: str,
    value_key: str,
    output: Path,
    *,
    max_value: float = 1.0,
    value_suffix: str = "",
    color: str = PALETTE["teal"],
    width: int = 1280,
    height: int | None = None,
) -> None:
    row_h = 44
    height = height or max(360, 120 + row_h * len(rows))
    left = 260
    bar_w = width - left - 170
    body = [_text(40, 48, title, "title"), _text(40, 76, subtitle, "subtitle")]
    body.append(f'<line x1="{left}" y1="100" x2="{left}" y2="{height - 42}" class="axis"/>')
    for i, row in enumerate(rows):
        y = 120 + i * row_h
        value = float(row[value_key])
        w = 0 if max_value <= 0 else bar_w * min(value / max_value, 1.0)
        body.append(_text(40, y + 21, row[label_key], "label"))
        body.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="24" fill="{PALETTE["panel"]}" rx="4"/>')
        body.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="24" fill="{color}" rx="4"/>')
        suffix = value_suffix or ("%" if max_value == 1.0 else "")
        label = f"{value * 100:.1f}%" if suffix == "%" else f"{value:.3f}{suffix}"
        body.append(_text(left + bar_w + 18, y + 18, label, "label"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_trace_inventory(data: dict[str, Any], output: Path) -> None:
    classes = data["trace_inventory"]["classes"]
    rows = [
        {"label": "Formal baseline (repeats 1-3)", "value": classes.get("formal_baseline", 0)},
        {"label": "Pilot repeat 0", "value": classes.get("pilot", 0)},
        {"label": "Phase 3 counterfactual / extra", "value": classes.get("phase3_counterfactual_or_extra", 0)},
    ]
    max_value = max(row["value"] for row in rows)
    _bar_chart(
        "Trace inventory and evidence boundary",
        "Baseline statistics use only formal repeats 1-3; other traces are context/case evidence.",
        rows,
        "label",
        "value",
        output,
        max_value=max_value,
        value_suffix=" traces",
        color=PALETTE["blue"],
    )


def _chart_controlled_vs_benchmark(data: dict[str, Any], output: Path) -> None:
    rows = [
        {
            "label": f"{row['split']} (n={row['n']})",
            "value": row["success_rate"],
        }
        for row in data["tables"]["task_split_summary"]
    ]
    _bar_chart(
        "Controlled vs benchmark split",
        "Controlled software-engineering tasks and benchmark tasks should be interpreted separately.",
        rows,
        "label",
        "value",
        output,
        color=PALETTE["coral"],
    )


def _chart_config_success(data: dict[str, Any], output: Path) -> None:
    rows = [
        {
            "label": f"c{row['config_id']} {row['harness']} / {row['model_role']}",
            "value": row["success_rate"],
        }
        for row in data["tables"]["config_summary"]
    ]
    _bar_chart(
        "Success by 6 harness/model configs",
        "Each config has 60 formal runs: 20 tasks x 3 repeats.",
        rows,
        "label",
        "value",
        output,
        color=PALETTE["green"],
    )


def _chart_task_difficulty(data: dict[str, Any], output: Path) -> None:
    rows = sorted(
        [
            {
                "label": f"{row['task_id']} ({row['task_category']})",
                "value": row["success_rate"],
            }
            for row in data["tables"]["task_summary"]
        ],
        key=lambda row: (row["value"], row["label"]),
    )
    _bar_chart(
        "Task success ranking",
        "Hard tasks are concentrated in benchmark and one controlled bug-fix case.",
        rows,
        "label",
        "value",
        output,
        color=PALETTE["amber"],
        height=1040,
    )


def _chart_category_success_cost(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["category_summary"]
    width = 1280
    height = 520
    left = 170
    top = 120
    group_w = 190
    max_tools = max(float(row["mean_tool_calls"]) for row in rows)
    body = [
        _text(40, 48, "Category success and tool-call cost", "title"),
        _text(40, 76, "Success is task-category dependent; rename is tool-heavy despite perfect success.", "subtitle"),
    ]
    for i, row in enumerate(rows):
        x = left + i * group_w
        success_h = 250 * float(row["success_rate"])
        tool_h = 250 * (float(row["mean_tool_calls"]) / max_tools)
        body.append(f'<rect x="{x}" y="{top + 250 - success_h:.1f}" width="52" height="{success_h:.1f}" fill="{PALETTE["green"]}" rx="4"/>')
        body.append(f'<rect x="{x + 66}" y="{top + 250 - tool_h:.1f}" width="52" height="{tool_h:.1f}" fill="{PALETTE["violet"]}" rx="4"/>')
        body.append(_text(x + 26, top + 280, f"{float(row['success_rate']) * 100:.0f}%", "small", "middle"))
        body.append(_text(x + 92, top + 280, f"{float(row['mean_tool_calls']):.1f}", "small", "middle"))
        for j, line in enumerate(_wrap(str(row["category"]).replace("_", " "), 14)[:2]):
            body.append(_text(x + 58, top + 320 + j * 16, line, "label", "middle"))
    body.append(f'<rect x="930" y="112" width="18" height="18" fill="{PALETTE["green"]}"/>')
    body.append(_text(956, 126, "success rate", "label"))
    body.append(f'<rect x="930" y="144" width="18" height="18" fill="{PALETTE["violet"]}"/>')
    body.append(_text(956, 158, "mean tool calls (scaled)", "label"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_first_tool_stacked(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["first_tool_family_by_config"]
    families = ["read", "search", "shell", "plan", "edit", "agent", "<none>"]
    colors = {
        "read": PALETTE["blue"],
        "search": PALETTE["teal"],
        "shell": PALETTE["amber"],
        "plan": PALETTE["violet"],
        "edit": PALETTE["green"],
        "agent": PALETTE["coral"],
        "<none>": PALETTE["slate"],
    }
    width = 1280
    height = 510
    left = 220
    bar_w = 760
    body = [
        _text(40, 48, "First tool family by config", "title"),
        _text(40, 76, "First action reveals harness affordance: Codex starts with shell; Hermes/OpenCode often search/read.", "subtitle"),
    ]
    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        grouped[int(row["config_id"])] = row
    for i, config_id in enumerate(sorted(grouped)):
        row = grouped[config_id]
        y = 118 + i * 56
        total = sum(int(row.get(family, 0)) for family in families) or 1
        body.append(_text(40, y + 21, row["config_label"], "label"))
        x = left
        for family in families:
            count = int(row.get(family, 0))
            if count == 0:
                continue
            w = bar_w * count / total
            body.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="26" fill="{colors[family]}" rx="3"/>')
            if w > 34:
                body.append(_text(x + w / 2, y + 18, count, "small", "middle"))
            x += w
    lx = 1010
    ly = 116
    for i, family in enumerate(families):
        body.append(f'<rect x="{lx}" y="{ly + i * 24}" width="16" height="16" fill="{colors[family]}"/>')
        body.append(_text(lx + 24, ly + 13 + i * 24, family, "small"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_task_heatmap(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["task_success_by_config"]
    tasks = []
    for row in data["tables"]["task_summary"]:
        tasks.append((row["task_category"], row["task_id"]))
    tasks = sorted(tasks)
    values = {(row["task_id"], int(row["config_id"])): float(row["success_rate"]) for row in rows}
    width = 1260
    height = 132 + len(tasks) * 36
    left = 260
    cell_w = 108
    cell_h = 26
    body = [
        _text(40, 48, "Task x config success heatmap", "title"),
        _text(40, 76, "Each cell is 3 formal repeats; benchmark rows expose the low-success region.", "subtitle"),
    ]
    for config_id in range(1, 7):
        body.append(_text(left + (config_id - 1) * cell_w + cell_w / 2, 108, f"c{config_id}", "label", "middle"))
    for i, (category, task_id) in enumerate(tasks):
        y = 126 + i * 36
        body.append(_text(40, y + 18, f"{task_id} ({category})", "small"))
        for config_id in range(1, 7):
            value = values[(task_id, config_id)]
            if value >= 0.9:
                color = "#3f9b68"
            elif value >= 0.6:
                color = "#f0b34f"
            elif value >= 0.3:
                color = "#e57a59"
            else:
                color = "#c9484a"
            x = left + (config_id - 1) * cell_w
            body.append(f'<rect x="{x}" y="{y}" width="{cell_w - 10}" height="{cell_h}" fill="{color}" rx="4"/>')
            body.append(_text(x + (cell_w - 10) / 2, y + 18, f"{value * 100:.0f}%", "small", "middle"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_phase3_label_summary(data: dict[str, Any], output: Path) -> None:
    rows = [
        ("Attribution labels", data["phase3_method_consistency"]["label_distribution"]),
        ("Decision kinds", data["phase3_method_consistency"]["decision_kind_distribution"]),
        ("M1-M4 agreement", data["phase3_method_consistency"]["agreement_count_distribution"]),
    ]
    width = 1280
    height = 620
    body = [
        _text(40, 48, "Phase 3 label and method-consistency summary", "title"),
        _text(40, 76, "20 selected high-divergence labels; 10/20 have unanimous M1-M4 agreement.", "subtitle"),
    ]
    colors = [PALETTE["teal"], PALETTE["coral"], PALETTE["amber"], PALETTE["violet"], PALETTE["green"]]
    for panel_i, (title, counts) in enumerate(rows):
        x0 = 70 + panel_i * 410
        y0 = 126
        body.append(f'<rect x="{x0 - 18}" y="{y0 - 36}" width="360" height="430" fill="{PALETTE["panel"]}" rx="8"/>')
        body.append(_text(x0, y0 - 10, title, "label"))
        max_count = max(int(v) for v in counts.values()) or 1
        for i, (label, count) in enumerate(counts.items()):
            y = y0 + 34 + i * 86
            w = 260 * int(count) / max_count
            body.append(_text(x0, y - 8, label, "small"))
            body.append(f'<rect x="{x0}" y="{y}" width="270" height="24" fill="#ffffff" rx="4"/>')
            body.append(f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="24" fill="{colors[i % len(colors)]}" rx="4"/>')
            body.append(_text(x0 + 286, y + 18, count, "label"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_factorial_by_split(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["factorial_by_split"]
    width = 1280
    height = 560
    body = [
        _text(40, 48, "Factorial contrasts by task split", "title"),
        _text(40, 76, "Benchmark has much higher failure rate; controlled tasks still show sequence divergence.", "subtitle"),
    ]
    x0 = 130
    y0 = 128
    group_w = 180
    max_val = 0.7
    for i, row in enumerate(rows):
        x = x0 + i * group_w
        seq_h = 260 * float(row["mean_sequence_disagreement"]) / max_val
        fail_h = 260 * float(row["mean_failure_rate"]) / max_val
        body.append(f'<rect x="{x}" y="{y0 + 260 - seq_h:.1f}" width="46" height="{seq_h:.1f}" fill="{PALETTE["teal"]}" rx="4"/>')
        body.append(f'<rect x="{x + 58}" y="{y0 + 260 - fail_h:.1f}" width="46" height="{fail_h:.1f}" fill="{PALETTE["coral"]}" rx="4"/>')
        body.append(_text(x + 23, y0 + 286, f"{float(row['mean_sequence_disagreement']):.2f}", "small", "middle"))
        body.append(_text(x + 81, y0 + 286, f"{float(row['mean_failure_rate']):.2f}", "small", "middle"))
        label = f"{row['task_split']} / {row['contrast_family']}"
        for j, line in enumerate(_wrap(label.replace("_", " "), 18)[:3]):
            body.append(_text(x + 52, y0 + 326 + j * 15, line, "small", "middle"))
    body.append(f'<rect x="930" y="118" width="18" height="18" fill="{PALETTE["teal"]}"/>')
    body.append(_text(956, 132, "sequence disagreement", "label"))
    body.append(f'<rect x="930" y="150" width="18" height="18" fill="{PALETTE["coral"]}"/>')
    body.append(_text(956, 164, "mean failure rate", "label"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_research_design_pipeline(data: dict[str, Any], output: Path) -> None:
    width = 1280
    height = 500
    steps = [
        ("6 configs", "Harness/model matrix"),
        ("20 tasks", "5 categories x 4"),
        ("360 traces", "3 formal repeats"),
        ("M1-M4", "White-box attribution"),
        ("Agent cards", "Descriptive proxies"),
    ]
    body = [
        _text(40, 48, "Research design pipeline", "title"),
        _text(40, 76, "Fixed task suite and formal repeats flow into normalized traces and attribution outputs.", "subtitle"),
    ]
    y = 180
    for i, (head, sub) in enumerate(steps):
        x = 70 + i * 238
        body.append(f'<rect x="{x}" y="{y}" width="190" height="118" fill="{PALETTE["panel"]}" stroke="{PALETTE["line"]}" rx="8"/>')
        body.append(_text(x + 95, y + 46, head, "title", "middle"))
        body.append(_text(x + 95, y + 78, sub, "small", "middle"))
        if i < len(steps) - 1:
            body.append(f'<line x1="{x + 198}" y1="{y + 59}" x2="{x + 230}" y2="{y + 59}" stroke="{PALETTE["slate"]}" stroke-width="3"/>')
            body.append(f'<polygon points="{x + 230},{y + 59} {x + 218},{y + 52} {x + 218},{y + 66}" fill="{PALETTE["slate"]}"/>')
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_method_ladder(data: dict[str, Any], output: Path) -> None:
    methods = [
        ("M1", "System prompt layer", "source/dossier"),
        ("M2", "Tool affordance", "source/dossier + trace schema"),
        ("M3", "Direct counterfactual", "executed repeat 301-312/401/403/404"),
        ("M4", "Planning-loop trace", "public trace + private replay refs"),
    ]
    width = 1280
    height = 560
    body = [
        _text(40, 48, "M1-M4 attribution evidence ladder", "title"),
        _text(40, 76, "Each method answers a different boundary; hidden chain-of-thought remains omitted.", "subtitle"),
    ]
    for i, (m, name, evidence) in enumerate(methods):
        x = 110 + i * 280
        y = 150 + i * 35
        body.append(f'<rect x="{x}" y="{y}" width="220" height="126" fill="{PALETTE["panel"]}" stroke="{PALETTE["line"]}" rx="8"/>')
        body.append(_text(x + 22, y + 38, m, "title"))
        body.append(_text(x + 22, y + 68, name, "label"))
        for j, line in enumerate(_wrap(evidence, 25)[:2]):
            body.append(_text(x + 22, y + 96 + j * 16, line, "small"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_environment_controls(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["environment_controls"]
    width = 1500
    height = 560
    columns = [
        ("Config", 50, 85),
        ("Harness", 145, 130),
        ("Model", 285, 235),
        ("Version", 535, 160),
        ("Effort/budget source", 710, 360),
        ("Raw/private refs", 1085, 175),
        ("n", 1280, 70),
    ]
    body = [
        _text(40, 48, "Environment locks and replay evidence", "title"),
        _text(40, 76, "Version, model snapshot, effort route, and raw/private references are recorded per config.", "subtitle"),
    ]
    y = 112
    body.append(f'<rect x="34" y="{y - 28}" width="1410" height="34" fill="{PALETTE["ink"]}" rx="6"/>')
    for title, x, _w in columns:
        body.append(f'<text x="{x}" y="{y - 6}" class="small" fill="#ffffff">{_e(title)}</text>')
    for i, row in enumerate(rows):
        yrow = y + 16 + i * 66
        fill = PALETTE["panel"] if i % 2 == 0 else "#ffffff"
        body.append(f'<rect x="34" y="{yrow - 26}" width="1410" height="58" fill="{fill}" stroke="{PALETTE["line"]}"/>')
        values = [
            f"c{row['config_id']}",
            row["harness"],
            row["model_role"],
            row["harness_versions"],
            row["effort_source"],
            f"raw {row['raw_log_paths_present']}; private {row['private_audit_paths_present']}",
            row["n"],
        ]
        for (_, x, w), value in zip(columns, values):
            for j, line in enumerate(_wrap(str(value), max(10, int(w / 9)))[:2]):
                body.append(_text(x, yrow - 6 + j * 15, line, "small"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_task_suite(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["task_suite"]
    counts = Counter(row["category"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    width = 1280
    height = 520
    body = [
        _text(40, 48, "Task-suite composition", "title"),
        _text(40, 76, "20 Python tasks: 16 controlled tasks and 4 Aider/Exercism benchmark tasks.", "subtitle"),
    ]
    x0 = 90
    y0 = 135
    colors = [PALETTE["green"], PALETTE["teal"], PALETTE["amber"], PALETTE["violet"], PALETTE["coral"]]
    for i, (category, count) in enumerate(sorted(counts.items())):
        x = x0 + i * 150
        body.append(f'<rect x="{x}" y="{y0}" width="110" height="{count * 42}" fill="{colors[i % len(colors)]}" rx="8"/>')
        body.append(_text(x + 55, y0 + count * 42 + 28, category.replace("_", " "), "small", "middle"))
        body.append(_text(x + 55, y0 + count * 21 + 8, count, "title", "middle"))
    body.append(_text(875, 160, "Source split", "label"))
    y = 198
    for i, (source, count) in enumerate(sorted(source_counts.items())):
        body.append(f'<rect x="875" y="{y + i * 48}" width="{count * 20}" height="26" fill="{colors[(i + 2) % len(colors)]}" rx="4"/>')
        body.append(_text(875 + count * 20 + 16, y + 18 + i * 48, f"{source}: {count}", "label"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_trace_schema(data: dict[str, Any], output: Path) -> None:
    fields = [
        ("identity", "config_id, harness, model_snapshot, task_id, repeat"),
        ("tool path", "tool_calls, turns, wall_time_s"),
        ("outcome", "success, grader_detail, final diff pointer"),
        ("replay refs", "raw_log_path, private_audit_path"),
        ("boundary", "evidence_levels, runtime_budget, hidden CoT omitted"),
    ]
    width = 1280
    height = 480
    body = [
        _text(40, 48, "Normalized trace schema evidence", "title"),
        _text(40, 76, "Four harnesses become comparable through one public sanitized JSON shape.", "subtitle"),
    ]
    for i, (head, desc) in enumerate(fields):
        x = 70 + (i % 3) * 395
        y = 130 + (i // 3) * 150
        body.append(f'<rect x="{x}" y="{y}" width="330" height="108" fill="{PALETTE["panel"]}" stroke="{PALETTE["line"]}" rx="8"/>')
        body.append(_text(x + 22, y + 36, head, "label"))
        for j, line in enumerate(_wrap(desc, 36)[:3]):
            body.append(_text(x + 22, y + 62 + j * 16, line, "small"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_config_routing_matrix(data: dict[str, Any], output: Path) -> None:
    harness_label = {
        "claude_code": "Claude Code",
        "opencode": "OpenCode",
        "hermes": "Hermes",
        "codex": "Codex",
    }
    provider_label = {"anthropic": "Anthropic native", "openai": "OpenAI native"}
    harnesses: list[str] = []
    models: list[str] = []
    provider_by_model: dict[str, str] = {}
    cell: dict[tuple[str, str], Any] = {}
    for config in CONFIGS:
        if config.harness not in harnesses:
            harnesses.append(config.harness)
        if config.model_role not in models:
            models.append(config.model_role)
        provider_by_model[config.model_role] = config.provider
        cell[(config.model_role, config.harness)] = config
    crossed = {h for h in harnesses if sum((m, h) in cell for m in models) > 1}

    width = 1320
    height = 200 + len(models) * 170
    col_w = (width - 300) // max(len(harnesses), 1)
    body = [
        _text(40, 48, "6 configs: harness x model routing grid", "title"),
        _text(40, 76, "Same model keeps one provider route across harnesses. OpenCode/Hermes are crossed cells; Claude Code/Codex are single-model anchors.", "subtitle"),
    ]
    for c, harness in enumerate(harnesses):
        x = 300 + c * col_w
        body.append(_text(x + (col_w - 30) / 2, 150, harness_label.get(harness, harness), "label", "middle"))
    for r, model in enumerate(models):
        y = 175 + r * 170
        label = "Haiku 4.5" if model == "haiku" else "GPT-5.4-mini"
        body.append(_text(40, y + 60, label, "label"))
        body.append(_text(40, y + 84, provider_label.get(provider_by_model.get(model, ""), provider_by_model.get(model, "")), "small"))
        for c, harness in enumerate(harnesses):
            x = 300 + c * col_w
            config = cell.get((model, harness))
            if config is None:
                body.append(f'<rect x="{x}" y="{y}" width="{col_w - 30}" height="130" fill="{PALETTE["paper"]}" stroke="{PALETTE["line"]}" stroke-dasharray="6 6" rx="8"/>')
                body.append(_text(x + (col_w - 30) / 2, y + 70, "not run", "small", "middle"))
                continue
            is_crossed = harness in crossed
            fill = PALETTE["panel"] if is_crossed else "#fdeed9"
            tag = "crossed (interaction)" if is_crossed else "anchor"
            body.append(f'<rect x="{x}" y="{y}" width="{col_w - 30}" height="130" fill="{fill}" stroke="{PALETTE["line"]}" rx="8"/>')
            body.append(_text(x + 22, y + 46, f"c{config.id}", "title"))
            body.append(_text(x + 22, y + 78, harness_label.get(harness, harness), "label"))
            body.append(_text(x + 22, y + 106, tag, "small"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_action_map(data: dict[str, Any], output: Path) -> None:
    rows = data["tables"]["action_implications"]
    width = 1320
    height = 160 + len(rows) * 132
    body = [
        _text(40, 48, "From attribution to action", "title"),
        _text(40, 76, "Each XAI finding maps to a concrete prompt/tool-surface governance action; no HCI human-study claim is made.", "subtitle"),
        _text(70, 124, "Finding (XAI evidence)", "small"),
        _text(770, 124, "Governance action", "small"),
    ]
    for i, row in enumerate(rows):
        y = 144 + i * 132
        body.append(f'<rect x="60" y="{y}" width="600" height="108" fill="{PALETTE["panel"]}" stroke="{PALETTE["line"]}" rx="8"/>')
        for j, line in enumerate(_wrap(str(row["finding"]), 50)[:4]):
            body.append(_text(82, y + 34 + j * 22, line, "label"))
        body.append(f'<line x1="676" y1="{y + 54}" x2="748" y2="{y + 54}" stroke="{PALETTE["slate"]}" stroke-width="3"/>')
        body.append(f'<polygon points="748,{y + 54} 734,{y + 46} 734,{y + 62}" fill="{PALETTE["slate"]}"/>')
        body.append(f'<rect x="756" y="{y}" width="504" height="108" fill="#eef6ef" stroke="{PALETTE["line"]}" rx="8"/>')
        for j, line in enumerate(_wrap(str(row["action"]), 46)[:4]):
            body.append(_text(778, y + 34 + j * 22, line, "label"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _chart_case_card(case: dict[str, Any], output: Path, index: int) -> None:
    width = 1500
    height = 720
    left = case["left"]
    right = case["right"]
    body = [
        _text(40, 48, f"Case {index}: {case['task_id']} / {case['factorial_label']}", "title"),
        _text(40, 76, f"{case['decision_kind']} | {case['confidence']} confidence | M1-M4 agreement {case['method_agreement']['agreement_count']}/{case['method_agreement']['method_count']}", "subtitle"),
    ]
    panels = [("Left", left, 70), ("Right", right, 780)]
    for title, side, x in panels:
        body.append(f'<rect x="{x}" y="118" width="620" height="470" fill="{PALETTE["panel"]}" stroke="{PALETTE["line"]}" rx="10"/>')
        body.append(_text(x + 26, 158, f"{title}: c{side['config']} {side['harness']}", "label"))
        body.append(_text(x + 26, 186, side["model"], "small"))
        body.append(_text(x + 26, 226, f"Outcome: {side['success_count']}/{side['n']} successful repeats", "label"))
        body.append(_text(x + 26, 264, "Dominant tool-family path", "small"))
        seq = " -> ".join(side["dominant_tool_family_sequence"])
        for j, line in enumerate(_wrap(seq, 54)[:8]):
            body.append(_text(x + 26, 292 + j * 22, line, "label"))
    evidence = case["condition_b_evidence_limitation_action"]["evidence"]
    y = 636
    body.append(_text(70, y, "Evidence refs: " + " | ".join(evidence[:2]), "small"))
    output.write_text(_svg(width, height, "\n".join(body)))


def _aggregate_first_tools(cell_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_config: dict[int, Counter[str]] = defaultdict(Counter)
    for cell in cell_summaries:
        by_config[int(cell["config_id"])].update(cell.get("first_tool_families", {}))
    rows = []
    all_families = sorted({family for counts in by_config.values() for family in counts})
    for config_id in sorted(by_config):
        row: dict[str, Any] = {
            "config_id": config_id,
            "config_label": _config_label(config_id),
            "n": sum(by_config[config_id].values()),
        }
        for family in all_families:
            row[family] = by_config[config_id].get(family, 0)
        rows.append(row)
    return rows


# Runtime budgets that the standard harness traces do not expose for OpenCode/Hermes.
# Backfilled from the 2026-06-05 thinking-capture investigation (logging proxy on the
# Anthropic endpoint + OpenCode model catalog). See
# docs/verification/2026-06-05-thinking-capture-investigation.md.
#   thinking_budget_tokens: actual budget sent on the Anthropic path (Claude Code 63999,
#     OpenCode 16000, Hermes 0 = native does not enable extended thinking). None on the
#     OpenAI path (reasoning is effort-based and encrypted, no thinking-token budget).
#   max_output / context: model/catalog windows (Haiku 64000/200000; GPT-5.4-mini
#     128000/400000 per OpenCode catalog; Codex context 258400 per its model_family).
_INVESTIGATED_BUDGET = {
    1: {"max_output_tokens": 64000, "thinking_budget_tokens": 63999, "context_window_tokens": 200000},
    2: {"max_output_tokens": 64000, "thinking_budget_tokens": 16000, "context_window_tokens": 200000},
    3: {"max_output_tokens": 64000, "thinking_budget_tokens": 0, "context_window_tokens": 200000},
    4: {"max_output_tokens": 128000, "thinking_budget_tokens": None, "context_window_tokens": 400000},
    5: {"max_output_tokens": 128000, "thinking_budget_tokens": None, "context_window_tokens": 400000},
    6: {"max_output_tokens": None, "thinking_budget_tokens": None, "context_window_tokens": 258400},
}


def _environment_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in metrics["environment_controls"]["configs"]:
        budget = (item["runtime_budget_variants"][0] or {}).get("budget", {})
        _inv = _INVESTIGATED_BUDGET.get(item["config_id"], {})
        rows.append({
            "config_id": item["config_id"],
            "harness": item["harness"],
            "model_role": item["model_role"],
            "model_snapshots": "; ".join(item["model_snapshots_observed"]),
            "provider": item["provider"],
            "harness_versions": "; ".join(item["harness_versions_observed"]),
            "reasoning_efforts": "; ".join(item["reasoning_efforts_observed"]),
            "effort_source": budget.get("effort_source"),
            "max_output_tokens": _inv.get("max_output_tokens", budget.get("max_output_tokens")),
            "thinking_budget_tokens": _inv.get("thinking_budget_tokens", budget.get("thinking_budget_tokens")),
            "context_window_tokens": _inv.get("context_window_tokens", budget.get("context_window_tokens")),
            "raw_log_paths_present": item["raw_log_paths_present"],
            "private_audit_paths_present": item["private_audit_paths_present"],
            "n": item["n"],
        })
    return rows


def _task_suite_rows() -> list[dict[str, Any]]:
    rows = []
    for task in load_tasks():
        rows.append({
            "task_id": task["id"],
            "category": task.get("category"),
            "tier": task.get("tier"),
            "source": task.get("source"),
            "grader": (task.get("grader") or {}).get("hidden_tests") or (task.get("grader") or {}).get("type"),
            "provenance": task.get("provenance", ""),
        })
    return rows


def _config_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = {item["config_id"]: item for item in metrics["config_metadata"]}
    rows = []
    for card in metrics["agent_cards"]:
        meta = metadata[card["config_id"]]
        dims = card["dimensions"]
        rows.append({
            "config_id": card["config_id"],
            "config_label": _config_label(card["config_id"]),
            "harness": card["harness"],
            "model_role": card["model_role"],
            "model_snapshot": card["model_snapshot"],
            "provider": meta["provider"],
            "success_rate": dims["fidelity"],
            "failed_trace_count": card["failed_trace_count"],
            "mean_stability": dims["stability"],
            "robustness_min_category_success": dims["robustness"],
            "actionability": dims["actionability"],
            "governability": dims["governability"],
            "n": card["n"],
            "role": meta.get("role", ""),
        })
    return rows


def _task_success_by_config_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for task in metrics["task_summaries"]:
        for cell in task["by_config"]:
            rows.append({
                "task_id": task["task_id"],
                "task_category": task["task_category"],
                "source": task["source"],
                "tier": task["tier"],
                "config_id": cell["config_id"],
                "config_label": _config_label(int(cell["config_id"])),
                "success_count": cell["success_count"],
                "success_rate": cell["success_rate"],
                "mean_tool_calls": cell["mean_tool_calls"],
                "first_tool_families": json.dumps(cell["first_tool_families"], ensure_ascii=False, sort_keys=True),
                "n": cell["n"],
            })
    return rows


def _case_rows(case_pack: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, case in enumerate(case_pack.get("cases", []), start=1):
        rows.append({
            "xai_case_id": f"XAI-C{index:02d}",
            "source_case_id": case["case_id"],
            "task_id": case["task_id"],
            "task_category": case["task_category"],
            "decision_kind": case["decision_kind"],
            "factorial_label": case["factorial_label"],
            "confidence": case["confidence"],
            "method_agreement": f"{case['method_agreement']['agreement_count']}/{case['method_agreement']['method_count']}",
            "left_config": case["left"]["config"],
            "left_harness": case["left"]["harness"],
            "left_model": case["left"]["model"],
            "left_success": f"{case['left']['success_count']}/{case['left']['n']}",
            "left_dominant_path": " -> ".join(case["left"]["dominant_tool_family_sequence"]),
            "right_config": case["right"]["config"],
            "right_harness": case["right"]["harness"],
            "right_model": case["right"]["model"],
            "right_success": f"{case['right']['success_count']}/{case['right']['n']}",
            "right_dominant_path": " -> ".join(case["right"]["dominant_tool_family_sequence"]),
            "limitation": (
                "Selected from high-divergence Phase 3 labels; use as an XAI "
                "walkthrough example, not as a prevalence estimate over all tasks."
            ),
        })
    return rows


def _headline_rows(metrics: dict[str, Any], trace_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    overall = metrics["overall"]
    association = metrics["success_association"]
    consistency = metrics["phase3_method_consistency"]
    return [
        {"metric": "formal_trace_count", "value": overall["formal_trace_count"], "presentation_text": "360 formal traces", "source": "metrics-summary.overall"},
        {"metric": "overall_success", "value": overall["success_rate"], "presentation_text": f"{overall['success_count']}/{overall['formal_trace_count']} ({_pct(overall['success_rate'])})", "source": "metrics-summary.overall"},
        {"metric": "task_suite", "value": overall["task_count"], "presentation_text": "20 tasks: 5 categories x 4", "source": "tasks/registry.yaml"},
        {"metric": "public_trace_json_total", "value": trace_inventory["total_public_trace_json"], "presentation_text": "396 public trace JSON files; only 360 are formal baseline", "source": "traces/"},
        {"metric": "sequence_disagreement_success_gap_r", "value": association["pearson_sequence_disagreement_vs_success_gap"], "presentation_text": f"r={association['pearson_sequence_disagreement_vs_success_gap']:.3f} over {association['n']} config-pair/task observations", "source": "metrics-summary.success_association"},
        {"metric": "unanimous_m1_m4", "value": consistency["unanimous_rate"], "presentation_text": f"{consistency['unanimous_count']}/{consistency['hci_label_count']} ({_pct(consistency['unanimous_rate'])})", "source": "metrics-summary.phase3_method_consistency"},
    ]


def _method_consistency_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    consistency = metrics["phase3_method_consistency"]
    rows = []
    for bucket, values in (
        ("factorial_label", consistency["label_distribution"]),
        ("decision_kind", consistency["decision_kind_distribution"]),
        ("agreement_count", consistency["agreement_count_distribution"]),
        ("confidence", consistency["confidence_distribution"]),
    ):
        for label, count in values.items():
            rows.append({"bucket": bucket, "label": label, "count": count})
    return rows


def _agent_card_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for card in metrics["agent_cards"]:
        row = {
            "config_id": card["config_id"],
            "config_label": _config_label(card["config_id"]),
            "harness": card["harness"],
            "model_role": card["model_role"],
            "model_snapshot": card["model_snapshot"],
            "dimension_scale": card["dimension_scale"],
        }
        row.update(card["dimensions"])
        rows.append(row)
    return rows


def _slide_map() -> list[dict[str, Any]]:
    return [
        {"slide": 1, "title": "Cover", "tables": [], "charts": [], "source": "content-draft.md", "note": "No data claim needed; old 24-slide HTML deck is deprecated."},
        {"slide": 2, "title": "Background and motivation", "tables": ["case-candidates.csv"], "charts": ["charts/xai-case-card-01.svg"], "source": "phase4_case_pack", "note": "Use one concrete same-task divergence only as the hook, not as a prevalence claim."},
        {"slide": 3, "title": "Faithfulness definition and RQ1-RQ4", "tables": [], "charts": [], "source": "content-draft.md", "note": "Define faithfulness as observable attribution support, not hidden chain-of-thought access."},
        {"slide": 4, "title": "What is a harness and why these four", "tables": ["config-summary.csv"], "charts": ["charts/config-routing-grid.svg"], "source": "dossiers + metrics-summary.config_metadata", "note": "Introduce Claude Code, Codex CLI, OpenCode, and Hermes before comparing behavior."},
        {"slide": 5, "title": "Harness mechanism comparison", "tables": ["environment-controls.csv"], "charts": ["charts/first-tool-family-stacked-by-config.svg"], "source": "dossiers + traces", "note": "Connect prompt/tool/planning/memory differences to later M1/M2 attribution."},
        {"slide": 6, "title": "Why white-box M1-M4 attribution", "tables": ["method-consistency.csv"], "charts": ["charts/method-evidence-ladder.svg"], "source": "phase3_attribution", "note": "M1/M2 are source/dossier/tool-surface evidence, not uniform runtime ablations."},
        {"slide": 7, "title": "Research design overview", "tables": ["headline-stats.csv"], "charts": ["charts/research-design-pipeline.svg"], "source": "metrics-summary.overall", "note": "6 configs x 20 tasks x 3 formal repeats; counterfactual repeats are method/case evidence only."},
        {"slide": 8, "title": "6 configs and source separation", "tables": ["config-summary.csv"], "charts": ["charts/config-routing-grid.svg"], "source": "metrics-summary.config_metadata", "note": "Claude Code and Codex are anchor cells; OpenCode/Hermes form crossed cells. Model effect is model+provider route."},
        {"slide": 9, "title": "Design decisions and tradeoffs", "tables": ["design-tradeoffs.csv"], "charts": [], "source": "design spec / phase4 guardrails", "note": "Explain Antigravity, reverse-proxy, benchmark, and SWE-bench exclusions."},
        {"slide": 10, "title": "Detailed experiment pipeline", "tables": ["source-index.csv"], "charts": ["charts/research-design-pipeline.svg"], "source": "runner + trace policy", "note": "Show provision, clean HOME, capture, mutation guard, hidden grader, normalization, immutable trace."},
        {"slide": 11, "title": "Environment locks and reproducibility", "tables": ["environment-controls.csv"], "charts": ["charts/environment-controls-matrix.svg"], "source": "metrics-summary.environment_controls", "note": "Effort/token/thinking/context controls differ by harness; cite exact route and empty-field boundary."},
        {"slide": 12, "title": "Isolation and contamination controls", "tables": ["source-index.csv"], "charts": ["charts/trace-inventory.svg"], "source": "phase2 isolation report + trace policy", "note": "Per-run HOME, hidden-test handling, repo mutation guard, and Phase 2 reset are design evidence."},
        {"slide": 13, "title": "Task suite and grading", "tables": ["task-suite.csv", "category-summary.csv"], "charts": ["charts/task-suite-composition.svg"], "source": "tasks/registry.yaml", "note": "Hidden pytest/unittest graders, no LLM judge; benchmark and controlled provenance stay separate."},
        {"slide": 14, "title": "Normalized trace schema and evidence levels", "tables": ["trace-inventory.csv"], "charts": ["charts/trace-schema-evidence.svg", "charts/method-evidence-ladder.svg"], "source": "traces + trace schema", "note": "State direct/source-derived/inferred/unknown evidence levels."},
        {"slide": 15, "title": "Execution reality", "tables": ["source-index.csv"], "charts": ["screenshots/runner-cli-execution.png", "screenshots/claude-trace-system-prompt.png"], "source": "raw/private refs + sanitized screenshots", "note": "Show sanitized real execution evidence; do not dwell on git storage policy."},
        {"slide": 16, "title": "Data scale", "tables": ["headline-stats.csv", "trace-inventory.csv"], "charts": ["charts/trace-inventory.svg"], "source": "metrics-summary.overall", "note": "Formal baseline is 360, not 396 public JSON traces."},
        {"slide": 17, "title": "Controlled vs benchmark split", "tables": ["task-split-summary.csv"], "charts": ["charts/controlled-vs-benchmark.svg", "charts/factorial-by-split.svg"], "source": "metrics-summary.overall.task_splits", "note": "Do not mix benchmark low success into controlled conclusions."},
        {"slide": 18, "title": "Jaccard and sequence disagreement", "tables": ["pairwise-observations.csv"], "charts": ["analysis/phase4/figures/jaccard-matrix.svg"], "source": "metrics-summary.pairwise + phase3 seed selection", "note": "Tool names are canonicalized into families before comparison."},
        {"slide": 19, "title": "Factorial decomposition", "tables": ["factorial-summary.csv", "factorial-by-split.csv"], "charts": ["analysis/phase4/figures/factorial-contrast-bars.svg", "charts/factorial-by-split.svg"], "source": "metrics-summary.factorial_decomposition", "note": "Use descriptive language; interaction claims rely on OpenCode/Hermes crossed cells."},
        {"slide": 20, "title": "Disagreement vs success", "tables": ["success-association.csv"], "charts": ["analysis/phase4/figures/disagreement-success-scatter.svg"], "source": "metrics-summary.success_association", "note": "Near-zero descriptive correlation is a finding, not proof of no risk or causal independence."},
        {"slide": 21, "title": "M1-M4 consistency", "tables": ["method-consistency.csv"], "charts": ["analysis/phase4/figures/method-consistency.svg", "charts/phase3-label-summary.svg"], "source": "metrics-summary.phase3_method_consistency", "note": "Labels are selected high-divergence decision points, not prevalence estimates."},
        {"slide": 22, "title": "Concrete XAI case walkthrough", "tables": ["case-candidates.csv"], "charts": ["charts/xai-case-card-03.svg"], "source": "phase4_case_pack", "note": "Use XAI-C03: bugfix-t2-03, OpenCode vs Hermes. Do not describe it as Hermes vs Codex."},
        {"slide": 23, "title": "Agent-card matrix", "tables": ["agent-card-matrix.csv"], "charts": ["analysis/phase4/figures/agent-card-matrix.svg"], "source": "metrics-summary.agent_cards", "note": "Actionability/governability are coverage gates here, not discriminative rankings."},
        {"slide": 24, "title": "From attribution to action", "tables": ["action-implications.csv", "agent-card-matrix.csv"], "charts": ["charts/attribution-action-map.svg", "analysis/phase4/figures/agent-card-matrix.svg"], "source": "agent_cards + cases", "note": "Translate evidence to prompt/tool-surface governance actions."},
        {"slide": 25, "title": "Limitations", "tables": ["limitations.csv"], "charts": [], "source": "phase4_report + phase4 guardrails", "note": "Include Python-only suite, specialized/general harness comparability, model+provider route, effort non-equivalence, selected labels, and descriptive-stat boundary."},
        {"slide": 26, "title": "Future work", "tables": ["future-work.csv"], "charts": [], "source": "content-draft.md", "note": "Mention downstream HCI human-study only as future work unless a human study is complete."},
        {"slide": 27, "title": "Closing", "tables": ["source-index.csv", "chart-manifest.csv"], "charts": [], "source": "content-draft.md", "note": "Close on faithful observable attribution: not a leaderboard and not mind-reading."},
    ]


def _support_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "design_tradeoffs": [
            {"decision": "Use formal repeats 1-3 only", "reason": "Avoid pilot/counterfactual leakage into baseline statistics.", "slide": 16},
            {"decision": "Separate controlled and benchmark tasks", "reason": "Benchmark rows have much lower success and different provenance.", "slide": 17},
            {"decision": "Use OpenCode/Hermes as crossed interaction cells", "reason": "Claude Code and Codex are anchor cells, not fully crossed across both models.", "slide": 19},
            {"decision": "Use M1-M4 instead of success-only scoring", "reason": "Success cannot identify prompt/tool/model interaction causes.", "slide": 6},
            {"decision": "Keep HCI human study out of XAI deck", "reason": "Phase 4 metrics are evidence materials, not human response data.", "slide": 25},
            {"decision": "Use the 27-slide content draft as the only canonical deck basis", "reason": "The old 24-slide HTML deck is deprecated and should not drive PPT production.", "slide": 1},
            {"decision": "Exclude Antigravity CLI", "reason": "Its release timing and harness maturity would add unstable variables to this baseline.", "slide": 9},
            {"decision": "Avoid reverse-proxy route rewriting", "reason": "Official route behavior is part of each agent product; translation layers would add format confounds.", "slide": 9},
            {"decision": "Use Aider/Exercism Python benchmarks instead of SWE-bench Verified", "reason": "They are provenance-backed, runnable on the aarch64 host, and better aligned with tool-path divergence analysis.", "slide": 9},
        ],
        "limitations": [
            {"limitation": "20-task Python suite only", "consequence": "Do not generalize to all coding-agent work.", "slide": 25},
            {"limitation": "Benchmark and controlled tasks differ", "consequence": "Interpret low benchmark success separately.", "slide": 25},
            {"limitation": "Specialized and general-purpose harnesses are mixed", "consequence": "Hermes is not coding-specialized in the same way Claude Code/Codex are, so comparisons need caveats.", "slide": 25},
            {"limitation": "Anchor cells are not fully crossed", "consequence": "Interaction claims use OpenCode/Hermes overlap only.", "slide": 19},
            {"limitation": "Model effect includes provider route", "consequence": "Haiku uses Anthropic and GPT-mini uses OpenAI, so model contrasts are model+provider-route contrasts.", "slide": 25},
            {"limitation": "Reasoning effort is aligned only within each harness' controls", "consequence": "High effort is not a perfectly equivalent knob across Claude Code, OpenCode, Hermes, and Codex.", "slide": 25},
            {"limitation": "Phase 3 labels are selected high-divergence cases", "consequence": "They support explanation, not prevalence estimates.", "slide": 21},
            {"limitation": "M1/M2 are not uniform runtime ablations", "consequence": "They use source, dossier, captured prompt, and tool-surface evidence according to each harness' visibility.", "slide": 25},
            {"limitation": "Hidden chain-of-thought omitted", "consequence": "Trace evidence uses visible tool path, prompts, metadata, and replay refs.", "slide": 3},
            {"limitation": "Agent-card actionability/governability are coverage gates", "consequence": "Current all-1.0 values should not be treated as discriminative capability rankings.", "slide": 23},
            {"limitation": "Correlation and factorial summaries are descriptive", "consequence": "They do not prove broad causal independence or general agent quality.", "slide": 20},
            {"limitation": "No HCI human responses yet", "consequence": "Trust/clarity/calibration claims wait for HCI phase.", "slide": 25},
        ],
        "future_work": [
            {"next_step": "Run HCI human study after XAI deck", "why": "Measure clarity, trust calibration, verification choice, safety/control, and cognitive load.", "slide": 26},
            {"next_step": "Expand beyond Python toy repo", "why": "Test language/framework/repository-size robustness.", "slide": 26},
            {"next_step": "Test newer harness mechanisms separately", "why": "Avoid mixing Phase 2 baseline with later harness behavior changes.", "slide": 26},
            {"next_step": "Ablate /goal, memory, and plan-mode mechanisms", "why": "Separate default harness behavior from optional harness features.", "slide": 26},
            {"next_step": "Make agent-card governance dimensions more discriminative", "why": "Replace coverage-gate dimensions with visibility, patchability, and intervention-support metrics.", "slide": 26},
            {"next_step": "Build optional HTML dashboard", "why": "Make trace/path/case inspection easier for appendix or defense.", "slide": 27},
        ],
        "action_implications": [
            {"finding": "Tool path diverges even when success is unchanged", "action": "Show evidence path, not only pass/fail status.", "slide": 24},
            {"finding": "First-tool strategies differ by harness", "action": "Expose or standardize initial discovery affordances when governance matters.", "slide": 24},
            {"finding": "Benchmark failures cluster by category", "action": "Separate high-risk task classes and require replay inspection.", "slide": 24},
            {"finding": "M1-M4 agreement is partial", "action": "Use confidence labels and caveats on agent cards.", "slide": 24},
        ],
    }


def build_phase5_xai_pack_data() -> dict[str, Any]:
    metrics = _read_json(PHASE4_METRICS)
    case_pack = _read_json(PHASE4_CASE_PACK)
    labels = _read_json(PHASE3_LABELS)
    trace_inventory = _all_trace_counts()
    source_index = [
        {"artifact": name, "path": path, "purpose": purpose}
        for name, path, purpose in [
            ("canonical_content_draft", "analysis/phase5/xai-presentation-pack/deck/content-draft.md", "27-slide canonical PPT basis and speaker-structure draft"),
            ("canonical_deck_readme", "analysis/phase5/xai-presentation-pack/deck/README.md", "states that the old 24-slide HTML deck is discarded"),
            ("phase5_structure", str(PRESENTATION_STRUCTURE), "slide order and narrative scope"),
            ("phase5_slide_map", "analysis/phase5/xai-presentation-pack/slide-data-map.json", "per-slide table/chart/source mapping"),
            ("phase5_manifest", "analysis/phase5/xai-presentation-pack/manifest.json", "data pack inventory and generated artifact paths"),
            ("phase5_screenshots_readme", "analysis/phase5/xai-presentation-pack/screenshots/README.md", "execution-reality screenshot provenance and safety scan"),
            ("phase5_data_pack_report", "docs/verification/2026-06-04-phase5-xai-data-pack-report.md", "pack generation and verification report"),
            ("phase5_canonical_consistency_audit", "docs/verification/2026-06-05-phase5-canonical-consistency-audit.md", "27-slide canonical reference/path completeness audit"),
            ("study_design", "docs/specs/2026-06-03-xai-harness-faithfulness-design.md", "original study design, pipeline, and environment controls"),
            ("trace_policy", "docs/specs/2026-06-04-trace-recording-policy.md", "raw/private/public trace recording and hidden-thinking policy"),
            ("phase4_guardrails", "docs/specs/2026-06-04-phase4-analysis-guardrails.md", "non-overclaim, task-sampling, harness-affinity, and XAI/HCI boundaries"),
            ("phase2_isolation_reset", "docs/verification/2026-06-04-phase2-isolation-reset.md", "shared-HOME contamination finding and formal rerun/reset rationale"),
            ("phase2_completion", "docs/verification/2026-06-04-phase2-completion-report.md", "formal matrix completion and per-run isolation verification"),
            ("phase3_seed_selection", "docs/verification/2026-06-04-phase3-seed-selection.md", "decision-point selection and tool-family canonicalization"),
            ("phase3_completion", "docs/verification/2026-06-04-phase3-completion-report.md", "M1-M4 attribution completion and counterfactual repeat ranges"),
            ("phase4_metrics", str(PHASE4_METRICS), "formal baseline metrics and existing figures"),
            ("phase4_case_pack", str(PHASE4_CASE_PACK), "case walkthrough candidates and trace refs"),
            ("phase3_labels", str(PHASE3_LABELS), "selected decision-point labels"),
            ("phase4_report", SOURCE_FILES["phase4_report"], "topline narrative and limitations"),
            ("dossier_overview", "docs/dossier/00-overview.md", "harness dossier index and evidence boundary"),
            ("dossier_claude_code", "docs/dossier/claude-code.md", "Claude Code prompt/tool/trace/environment evidence"),
            ("dossier_codex_cli", "docs/dossier/codex-cli.md", "Codex CLI prompt/tool/trace/environment evidence"),
            ("dossier_opencode", "docs/dossier/opencode.md", "OpenCode prompt/tool/trace/environment evidence"),
            ("dossier_hermes", "docs/dossier/hermes.md", "Hermes prompt/tool/trace/environment evidence"),
            ("dossier_hermes_memory", "docs/dossier/hermes-memory.md", "Hermes memory/context mechanism evidence"),
            ("dossier_cross_harness", "docs/dossier/cross-harness-comparison.md", "cross-harness mechanism comparison evidence"),
            ("runner_trace_schema", "runner/trace_schema.py", "normalized trace schema and evidence field boundary"),
            ("runner_phase5_pack", "runner/phase5_xai_pack.py", "phase5 data pack generation authority"),
            ("task_registry", SOURCE_FILES["registry"], "task provenance, category, tier, grader"),
            ("vps_private_raw", "/data/harness-lab/private-audits and /data/harness-lab/runs", "complete replay layer outside git"),
        ]
    ]
    tables = {
        "headline_stats": _headline_rows(metrics, trace_inventory),
        "config_summary": _config_rows(metrics),
        "task_split_summary": metrics["overall"]["task_splits"],
        "category_summary": metrics["category_summaries"],
        "category_success_by_config": metrics["category_success_by_config"],
        "factorial_summary": metrics["factorial_decomposition"]["contrast_summary"],
        "factorial_by_split": metrics["factorial_decomposition"]["contrast_by_split"],
        "success_association": [metrics["success_association"]],
        "method_consistency": _method_consistency_rows(metrics),
        "agent_card_matrix": _agent_card_rows(metrics),
        "task_summary": metrics["task_summaries"],
        "task_success_by_config": _task_success_by_config_rows(metrics),
        "pairwise_observations": metrics["pairwise"]["observations"],
        "pairwise_by_category": metrics["pairwise"]["pair_by_category"],
        "first_tool_family_by_config": _aggregate_first_tools(metrics["cell_summaries"]),
        "case_candidates": _case_rows(case_pack),
        "trace_inventory": [
            {"bucket": bucket, "count": count}
            for bucket, count in trace_inventory["classes"].items()
        ],
        "environment_controls": _environment_rows(metrics),
        "task_suite": _task_suite_rows(),
        "source_index": source_index,
    }
    tables.update(_support_rows())
    data = {
        "phase": "phase5_xai_presentation_pack",
        "schema_version": 1,
        "boundary": {
            "pptx_created": False,
            "scope": "XAI deck support only; HCI human-study metrics are intentionally deferred.",
            "canonical_deck_basis": "analysis/phase5/xai-presentation-pack/deck/content-draft.md (27 slides)",
            "deprecated_deck": "analysis/phase5/xai-presentation-pack/deck/index.html is not a canonical source.",
            "baseline_statistics": "Formal Phase 2 repeats 1-3 only.",
            "nonformal_traces": "Pilot repeat 0 and Phase 3 counterfactual/extra repeats may be used for examples, not baseline rates.",
            "vps_authority": "/data/repos/xai-harness-faithfulness",
        },
        "source_files": SOURCE_FILES,
        "trace_inventory": trace_inventory,
        "phase3_label_count": labels.get("label_count"),
        "phase4_existing_charts": EXISTING_PHASE4_CHARTS,
        "phase3_method_consistency": metrics["phase3_method_consistency"],
        "tables": tables,
        "slide_map": _slide_map(),
    }
    return data


def _chart_manifest(generated: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for name, spec in EXISTING_PHASE4_CHARTS.items():
        rows.append({
            "chart_id": name,
            "path": spec["path"],
            "status": "existing_phase4",
            "recommended_slide": spec["slide"],
            "use": spec["use"],
        })
    generated_use = {
        "trace-inventory.svg": "Evidence scale and baseline/nonbaseline boundary.",
        "config-success-bars.svg": "Topline config success comparison.",
        "controlled-vs-benchmark.svg": "Controlled vs benchmark split.",
        "category-success-cost.svg": "Category success vs tool-call effort.",
        "task-difficulty-ranked.svg": "Task-level difficulty ranking.",
        "task-success-heatmap.svg": "Task/config success matrix.",
        "first-tool-family-stacked-by-config.svg": "Harness first-action style comparison.",
        "phase3-label-summary.svg": "Attribution label and agreement distributions.",
        "factorial-by-split.svg": "Contrast metrics separated by controlled/benchmark split.",
        "research-design-pipeline.svg": "Method pipeline overview.",
        "method-evidence-ladder.svg": "M1-M4 method evidence boundary.",
        "environment-controls-matrix.svg": "Environment lock table as chart.",
        "task-suite-composition.svg": "Task category/source composition.",
        "trace-schema-evidence.svg": "Normalized trace schema evidence model.",
        "config-routing-grid.svg": "Harness x model routing grid: anchor vs crossed interaction cells.",
        "attribution-action-map.svg": "Map XAI findings to prompt/tool-surface governance actions.",
        "pipeline-flow.svg": "Per-run pipeline: provision to immutable persist (8 steps).",
        "isolation-hierarchy.svg": "Per-run clean HOME and Hermes isolation from production.",
        "grader-flow.svg": "Deterministic hidden-pytest grading flow (no LLM judge).",
    }
    for name, path in sorted(generated.items()):
        rows.append({
            "chart_id": name.replace(".svg", ""),
            "path": path,
            "status": "generated_phase5_pack",
            "recommended_slide": "",
            "use": generated_use.get(name, "Concrete case walkthrough candidate."),
        })
    return rows


def write_phase5_xai_pack(data: dict[str, Any], output_dir: str | Path = DEFAULT_PACK_DIR) -> dict[str, Any]:
    out = _repo_path(output_dir)
    tables_dir = out / "tables"
    charts_dir = out / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    screenshot_src = _repo_path(DEFAULT_PACK_DIR) / "screenshots"
    if screenshot_src.exists():
        screenshot_dir = out / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        for source in screenshot_src.iterdir():
            if source.is_file():
                (screenshot_dir / source.name).write_bytes(source.read_bytes())

    table_paths = {}
    for name, rows in data["tables"].items():
        path = tables_dir / f"{_safe_filename(name)}.csv"
        if name == "task_summary":
            rows = [
                {key: value for key, value in row.items() if key != "by_config"}
                for row in rows
            ]
        _write_csv(path, rows)
        table_paths[name] = _rel(path)

    generated_charts = {
        "trace-inventory.svg": charts_dir / "trace-inventory.svg",
        "config-success-bars.svg": charts_dir / "config-success-bars.svg",
        "controlled-vs-benchmark.svg": charts_dir / "controlled-vs-benchmark.svg",
        "category-success-cost.svg": charts_dir / "category-success-cost.svg",
        "task-difficulty-ranked.svg": charts_dir / "task-difficulty-ranked.svg",
        "task-success-heatmap.svg": charts_dir / "task-success-heatmap.svg",
        "first-tool-family-stacked-by-config.svg": charts_dir / "first-tool-family-stacked-by-config.svg",
        "phase3-label-summary.svg": charts_dir / "phase3-label-summary.svg",
        "factorial-by-split.svg": charts_dir / "factorial-by-split.svg",
        "research-design-pipeline.svg": charts_dir / "research-design-pipeline.svg",
        "method-evidence-ladder.svg": charts_dir / "method-evidence-ladder.svg",
        "environment-controls-matrix.svg": charts_dir / "environment-controls-matrix.svg",
        "task-suite-composition.svg": charts_dir / "task-suite-composition.svg",
        "trace-schema-evidence.svg": charts_dir / "trace-schema-evidence.svg",
        "config-routing-grid.svg": charts_dir / "config-routing-grid.svg",
        "attribution-action-map.svg": charts_dir / "attribution-action-map.svg",
        "pipeline-flow.svg": charts_dir / "pipeline-flow.svg",
        "isolation-hierarchy.svg": charts_dir / "isolation-hierarchy.svg",
        "grader-flow.svg": charts_dir / "grader-flow.svg",
    }
    # Publication-quality rendering delegated to runner.figures (matplotlib).
    # The legacy hand-rolled _chart_* SVG helpers are kept for reference only.
    from runner import figures as _figs
    _figs.render_phase5_charts(out_dir=charts_dir)

    for i in range(1, len(_read_json(PHASE4_CASE_PACK).get("cases", [])) + 1):
        path = charts_dir / f"xai-case-card-{i:02d}.svg"
        generated_charts[path.name] = path

    for path in generated_charts.values():
        _strip_trailing_whitespace(path)

    generated_chart_paths = {name: _rel(path) for name, path in generated_charts.items()}
    chart_manifest = _chart_manifest(generated_chart_paths)
    _write_csv(tables_dir / "chart-manifest.csv", chart_manifest)
    table_paths["chart_manifest"] = _rel(tables_dir / "chart-manifest.csv")

    manifest = {
        "phase": data["phase"],
        "schema_version": data["schema_version"],
        "boundary": data["boundary"],
        "source_files": data["source_files"],
        "trace_inventory": data["trace_inventory"],
        "tables": table_paths,
        "charts": {
            "existing_phase4": EXISTING_PHASE4_CHARTS,
            "generated": generated_chart_paths,
        },
        "chart_manifest": _rel(tables_dir / "chart-manifest.csv"),
        "slide_map": _rel(out / "slide-data-map.json"),
        "readme": _rel(out / "README.md"),
    }
    _write_json(out / "manifest.json", manifest)
    _write_json(out / "slide-data-map.json", data["slide_map"])
    _write_json(out / "slide-ready-data.json", {
        "boundary": data["boundary"],
        "headline_stats": data["tables"]["headline_stats"],
        "slide_map": data["slide_map"],
        "chart_manifest": chart_manifest,
    })
    _write_readme(out / "README.md", data, manifest, chart_manifest)
    return {
        "pack_dir": out,
        "manifest": out / "manifest.json",
        "readme": out / "README.md",
        "slide_map": out / "slide-data-map.json",
        "slide_ready_data": out / "slide-ready-data.json",
        "tables": table_paths,
        "charts": generated_chart_paths,
        "chart_manifest": tables_dir / "chart-manifest.csv",
    }


def _write_readme(path: Path, data: dict[str, Any], manifest: dict[str, Any], chart_manifest: list[dict[str, Any]]) -> None:
    headline = {row["metric"]: row["presentation_text"] for row in data["tables"]["headline_stats"]}
    lines = [
        "# Phase 5 XAI Presentation Data Pack",
        "",
        "Scope: data, chart assets, source mapping, and slide-ready analysis for the XAI presentation only. No PPTX is generated here.",
        "",
        "Canonical deck basis: `analysis/phase5/xai-presentation-pack/deck/content-draft.md` (27 slides). The old 24-slide HTML deck is deprecated and must not be used as the PPT source.",
        "",
        "## Evidence Boundary",
        "",
        "- Baseline statistics use only formal Phase 2 repeats 1-3.",
        "- Pilot repeat 0 and Phase 3 counterfactual/extra repeats are case/method evidence, not baseline rates.",
        "- HCI human-study claims are intentionally excluded; this pack only preserves material that can later feed the HCI phase.",
        "- Faithfulness means observable attribution support from trace/prompt/tool/counterfactual evidence; hidden chain-of-thought is not exposed or claimed.",
        "- VPS authority: `/data/repos/xai-harness-faithfulness`; private/raw replay remains outside git under `/data/harness-lab/`.",
        "",
        "## Headline Numbers",
        "",
        f"- Formal traces: {headline['formal_trace_count']}.",
        f"- Overall success: {headline['overall_success']}.",
        f"- Task suite: {headline['task_suite']}.",
        f"- Public trace JSON inventory: {headline['public_trace_json_total']}.",
        f"- Disagreement vs success-gap association: {headline['sequence_disagreement_success_gap_r']}.",
        f"- Unanimous M1-M4 agreement: {headline['unanimous_m1_m4']}.",
        "",
        "## Main Files",
        "",
        f"- Manifest: `{_rel(path.parent / 'manifest.json')}`",
        f"- Slide data map: `{manifest['slide_map']}`",
        f"- Slide-ready compact JSON: `{_rel(path.parent / 'slide-ready-data.json')}`",
        f"- Table directory: `{_rel(path.parent / 'tables')}`",
        f"- Chart directory: `{_rel(path.parent / 'charts')}`",
        "",
        "## Chart Menu",
        "",
        "| Chart | Status | Use |",
        "|---|---|---|",
    ]
    for row in chart_manifest:
        lines.append(f"| `{row['path']}` | {row['status']} | {row['use']} |")
    lines.extend([
        "",
        "## Slide Use",
        "",
        "Use `slide-data-map.json` for the page-by-page mapping. It names the table(s), chart(s), source path, and caveat for each of the 27 canonical slides.",
        "",
        "## Do Not Mix Into XAI",
        "",
        "- Human-study participant results.",
        "- Trust calibration or perceived safety claims.",
        "- Claims that Phase 3 selected labels estimate prevalence over all traces.",
        "- Claims that the 20-task Python suite generalizes to all agentic coding work.",
        "- Claims that M1/M2 are uniform runtime ablations across all harnesses.",
        "- Claims that actionability/governability all-1.0 values are discriminative harness rankings.",
        "",
    ])
    path.write_text("\n".join(lines))


def build_and_write_phase5_xai_pack(output_dir: str | Path = DEFAULT_PACK_DIR) -> dict[str, Any]:
    data = build_phase5_xai_pack_data()
    return write_phase5_xai_pack(data, output_dir)
