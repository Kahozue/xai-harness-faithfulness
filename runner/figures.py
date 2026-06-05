"""Publication-quality figure rendering for the xAI report and slide deck.

Single rendering authority for every committed figure. Replaces the earlier
hand-rolled SVG output (bright "toy" blocks) with a restrained academic style:
muted, colorblind-safe palette, consistent proportions, clean axes/typography,
vector SVG with selectable text.

Inputs are the committed Phase 2/3/4 analysis artifacts; this module is
read-only with respect to them. Repo root is `paths.REPO`, overridable with the
`XAI_REPO` environment variable (so it runs on the VPS and on a mirror checkout).

Run: `python -m runner.figures` (regenerates all figures in place).
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from runner import paths
from runner.configs import CONFIGS

REPO = Path(os.environ.get("XAI_REPO", str(paths.REPO)))
PHASE4_FIG = REPO / "analysis" / "phase4" / "figures"
PACK_CHARTS = REPO / "analysis" / "phase5" / "xai-presentation-pack" / "charts"
METRICS = REPO / "analysis" / "phase4" / "metrics-summary.json"
CASE_PACK = REPO / "analysis" / "phase4" / "hci-case-pack.json"

# ── locked publication style ──────────────────────────────────────────────
INK = "#1a1a1a"
GRID = "#e9e9e9"
BLUE = "#36618e"          # primary single-series
STEEL = "#4c78a8"
PALETTE = ["#4c78a8", "#e0913b", "#5a9367", "#9b6fb0", "#8c8c8c"]  # muted qualitative
OKABE = {                # colorblind-safe categories
    "bug_fix": "#0072B2", "rename": "#009E73", "add_tests": "#E69F00",
    "add_logging": "#CC79A7", "benchmark": "#D55E00",
}
SEQ = "Blues"

CFG_LABEL = {1: "c1 Claude Code", 2: "c2 OpenCode", 3: "c3 Hermes",
             4: "c4 OpenCode", 5: "c5 Hermes", 6: "c6 Codex"}


def _setup() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10.5,
        "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlecolor": INK,
        "axes.labelsize": 11, "axes.labelcolor": INK,
        "axes.edgecolor": "#555555", "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": "#333", "ytick.color": "#333", "text.color": INK,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.bbox": "tight", "svg.fonttype": "none", "svg.hashsalt": "xai-figures",
    })


def _load(path: Path) -> Any:
    return json.loads(path.read_text())


def _save(fig, directory: Path, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / name, metadata={"Date": None})
    plt.close(fig)


def _title(ax, text: str) -> None:
    ax.set_title(text, loc="left", pad=10)


def _grid_x(ax) -> None:
    ax.xaxis.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _grid_y(ax) -> None:
    ax.yaxis.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _heatmap(ax, matrix, row_labels, col_labels, *, vmin, vmax, cmap=SEQ,
             fmt="{:.2f}", thresh=None) -> Any:
    im = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_yticks(range(len(row_labels)))
    ax.set_xticklabels(col_labels, rotation=40, ha="right", fontsize=9)
    ax.set_yticklabels(row_labels, fontsize=9)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cut = thresh if thresh is not None else (vmin + (vmax - vmin) * 0.6)
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            v = matrix[i][j]
            if v is None:
                continue
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=8.5,
                    color=("white" if v > cut else "#222"))
    return im


# ── PHASE 4 FIGURES ───────────────────────────────────────────────────────
def fig_jaccard(m) -> None:
    cfgs = [c["config_id"] for c in m["config_metadata"]]
    idx = {c: i for i, c in enumerate(cfgs)}
    M = [[1.0 if i == j else None for j in range(len(cfgs))] for i in range(len(cfgs))]
    for r in m["pairwise"]["by_config_pair"]:
        a, b = (int(x) for x in r["pair_label"].replace("c", "").split("-"))
        M[idx[a]][idx[b]] = M[idx[b]][idx[a]] = r["mean_jaccard"]
    fig, ax = plt.subplots(figsize=(5.7, 4.9))
    im = _heatmap(ax, M, [CFG_LABEL[c] for c in cfgs], [CFG_LABEL[c] for c in cfgs],
                  vmin=0.5, vmax=1.0, thresh=0.8)
    _title(ax, "Tool-family Jaccard similarity across configs")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Jaccard similarity", fontsize=9.5)
    cb.ax.tick_params(labelsize=8.5)
    _save(fig, PHASE4_FIG, "jaccard-matrix.svg")


def fig_factorial(m) -> None:
    rows = sorted(m["factorial_decomposition"]["contrast_summary"],
                  key=lambda r: r["mean_sequence_disagreement"])
    names = {"harness_same_model": "Harness effect\n(same model)",
             "mixed_harness_model": "Mixed harness × model",
             "model_swap_same_harness": "Model effect\n(same harness)"}
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    y = range(len(rows))
    ax.barh(list(y), [r["mean_sequence_disagreement"] for r in rows],
            color=BLUE, height=0.6, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels([names[r["contrast_family"]] for r in rows])
    ax.set_xlim(0, 0.62)
    ax.set_xlabel("Mean tool-sequence disagreement")
    _grid_x(ax)
    for yi, r in zip(y, rows):
        ax.text(r["mean_sequence_disagreement"] + 0.012, yi,
                f'{r["mean_sequence_disagreement"]:.3f}  (n={r["n"]})',
                va="center", fontsize=9.5, color="#333")
    _title(ax, "Tool-sequence disagreement by contrast family")
    _save(fig, PHASE4_FIG, "factorial-contrast-bars.svg")


def fig_scatter(m) -> None:
    obs = m["pairwise"]["observations"]
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for cat, col in OKABE.items():
        xs = [o["mean_sequence_disagreement"] for o in obs if o["task_category"] == cat]
        ys = [o["success_gap"] for o in obs if o["task_category"] == cat]
        ax.scatter(xs, ys, s=26, color=col, alpha=0.62, edgecolors="none",
                   label=cat.replace("_", " "), zorder=3)
    ax.set_xlim(-0.02, 1.0)
    ax.set_ylim(-0.03, 1.0)
    ax.set_xlabel("Tool-sequence disagreement")
    ax.set_ylabel("Task success-rate gap")
    ax.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    a = m["success_association"]
    ax.text(0.97, 0.96, f"Pearson r = {a['pearson_sequence_disagreement_vs_success_gap']:.3f}"
            f"  (n={a['n']})", transform=ax.transAxes, ha="right", va="top",
            fontsize=9.5, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=0.8))
    ax.legend(title="Task category", fontsize=8.5, title_fontsize=9, loc="upper left", frameon=False)
    _title(ax, "Disagreement vs. success gap (per config-pair × task)")
    _save(fig, PHASE4_FIG, "disagreement-success-scatter.svg")


def fig_method_consistency(m) -> None:
    cross = m["phase3_method_consistency"]["factorial_label_by_decision_kind"]
    rows = sorted(cross)
    cols = sorted({c for r in cross.values() for c in r})
    M = [[cross[r].get(c, 0) for c in cols] for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    im = _heatmap(ax, M, [r.replace("_", " ") for r in rows],
                  [c.replace("_", " ") for c in cols],
                  vmin=0, vmax=max(max(r) for r in M) or 1, cmap="Blues",
                  fmt="{:.0f}", thresh=(max(max(r) for r in M) or 1) * 0.6)
    p3 = m["phase3_method_consistency"]
    _title(ax, f"Phase 3 attribution labels  (M1–M4 unanimous {p3['unanimous_count']}/{p3['hci_label_count']})")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("label count", fontsize=9.5)
    cb.ax.tick_params(labelsize=8.5)
    _save(fig, PHASE4_FIG, "method-consistency.svg")


def fig_agent_card(m) -> None:
    dims = ["fidelity", "stability", "robustness", "actionability", "governability"]
    cards = sorted(m["agent_cards"], key=lambda c: c["config_id"])
    M = [[c["dimensions"][d] for d in dims] for c in cards]
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    im = _heatmap(ax, M, [CFG_LABEL[c["config_id"]] for c in cards],
                  [d.capitalize() for d in dims], vmin=0, vmax=1.0, cmap="Blues", thresh=0.6)
    _title(ax, "Agent-card matrix  (descriptive proxies, 0–1)")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("score", fontsize=9.5)
    cb.ax.tick_params(labelsize=8.5)
    _save(fig, PHASE4_FIG, "agent-card-matrix.svg")


# ── helpers for diagrams ──────────────────────────────────────────────────
def _box(ax, x, y, w, h, head, sub="", *, fill="#eef2f7", edge="#c4d0de", tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                linewidth=1.0, edgecolor=edge, facecolor=fill, mutation_aspect=0.5))
    ax.text(x + w / 2, y + h * 0.62, head, ha="center", va="center", fontsize=11.5,
            fontweight="bold", color=tc)
    if sub:
        ax.text(x + w / 2, y + h * 0.3, sub, ha="center", va="center", fontsize=8.6, color="#5a6573")


def _arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.4, color="#8794a3"))


def _blank(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


# ── PACK DATA CHARTS ──────────────────────────────────────────────────────
def fig_trace_inventory() -> None:
    by = Counter()
    for p in (REPO / "traces").glob("*/*/*.json"):
        r = p.stem
        if r in {"1", "2", "3"}:
            by["Formal baseline\n(repeats 1–3)"] += 1
        elif r == "0":
            by["Pilot\n(repeat 0)"] += 1
        else:
            by["Phase 3 counterfactual\n/ extra"] += 1
    order = ["Formal baseline\n(repeats 1–3)", "Pilot\n(repeat 0)", "Phase 3 counterfactual\n/ extra"]
    vals = [by.get(k, 0) for k in order]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ax.barh(range(len(order)), vals, color=BLUE, height=0.6, zorder=3)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_xlabel("Number of trace JSON files")
    ax.set_xlim(0, max(vals) * 1.18)
    _grid_x(ax)
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.01, i, str(v), va="center", fontsize=10, color="#333")
    _title(ax, "Trace inventory and evidence boundary")
    _save(fig, PACK_CHARTS, "trace-inventory.svg")


def fig_config_success(m) -> None:
    cards = sorted(m["agent_cards"], key=lambda c: c["config_id"])
    labels = [CFG_LABEL[c["config_id"]] for c in cards]
    vals = [c["dimensions"]["fidelity"] for c in cards]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.bar(range(len(cards)), vals, color=STEEL, width=0.62, zorder=3)
    ax.set_xticks(range(len(cards)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Success rate")
    _grid_y(ax)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v*100:.0f}%", ha="center", fontsize=9.5, color="#333")
    _title(ax, "Task success by config  (60 formal runs each)")
    _save(fig, PACK_CHARTS, "config-success-bars.svg")


def fig_controlled_vs_benchmark(m) -> None:
    sp = {s["split"]: s for s in m["overall"]["task_splits"]}
    order = ["controlled", "benchmark"]
    succ = [sp[k]["success_rate"] for k in order]
    tools = [sp[k]["mean_tool_calls"] for k in order]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.4))
    a1.bar(order, succ, color=[STEEL, "#d1894a"], width=0.55, zorder=3)
    a1.set_ylim(0, 1.0)
    a1.set_ylabel("Success rate")
    a1.yaxis.grid(True, color=GRID, linewidth=0.7)
    a1.set_axisbelow(True)
    a1.tick_params(length=0)
    for i, v in enumerate(succ):
        a1.text(i, v + 0.02, f"{v*100:.1f}%", ha="center", fontsize=10, color="#333")
    a1.set_title("Success rate", loc="left", fontsize=11)
    a2.bar(order, tools, color=[STEEL, "#d1894a"], width=0.55, zorder=3)
    a2.set_ylabel("Mean tool calls / run")
    a2.yaxis.grid(True, color=GRID, linewidth=0.7)
    a2.set_axisbelow(True)
    a2.tick_params(length=0)
    for i, v in enumerate(tools):
        a2.text(i, v + 0.15, f"{v:.1f}", ha="center", fontsize=10, color="#333")
    a2.set_title("Tool-call effort", loc="left", fontsize=11)
    fig.suptitle("Controlled vs. benchmark split", x=0.012, ha="left", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _save(fig, PACK_CHARTS, "controlled-vs-benchmark.svg")


def fig_category_success_cost(m) -> None:
    rows = sorted(m["category_summaries"], key=lambda r: r["success_rate"], reverse=True)
    cats = [r["category"].replace("_", " ") for r in rows]
    succ = [r["success_rate"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.bar(range(len(rows)), succ, color=[OKABE.get(r["category"], STEEL) for r in rows],
           width=0.62, zorder=3)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(cats, fontsize=9.5)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Success rate")
    _grid_y(ax)
    for i, r in enumerate(rows):
        ax.text(i, r["success_rate"] + 0.02, f"{r['success_rate']*100:.0f}%", ha="center", fontsize=9.5, color="#333")
    _title(ax, "Success rate by task category")
    _save(fig, PACK_CHARTS, "category-success-cost.svg")


def fig_task_difficulty(m) -> None:
    rows = sorted(m["task_summaries"], key=lambda r: r["success_rate"])
    fig, ax = plt.subplots(figsize=(6.8, 6.4))
    y = range(len(rows))
    ax.barh(list(y), [r["success_rate"] for r in rows],
            color=[OKABE.get(r["task_category"], STEEL) for r in rows], height=0.72, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels([r["task_id"] for r in rows], fontsize=8.5)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Success rate (across 6 configs × 3 repeats)")
    _grid_x(ax)
    handles = [plt.Line2D([0], [0], marker="s", linestyle="", color=c, label=k.replace("_", " "))
               for k, c in OKABE.items()]
    ax.legend(handles=handles, fontsize=8, loc="lower right", frameon=False)
    _title(ax, "Per-task difficulty ranking")
    _save(fig, PACK_CHARTS, "task-difficulty-ranked.svg")


def fig_task_success_heatmap(m) -> None:
    cfgs = [c["config_id"] for c in m["config_metadata"]]
    idx = {c: i for i, c in enumerate(cfgs)}
    rows = sorted(m["task_summaries"], key=lambda r: (r["task_category"], r["task_id"]))
    M = [[0.0] * len(cfgs) for _ in rows]
    for ri, r in enumerate(rows):
        for bc in r["by_config"]:
            M[ri][idx[bc["config_id"]]] = bc["success_rate"]
    fig, ax = plt.subplots(figsize=(6.4, 7.2))
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(cfgs)))
    ax.set_xticklabels([f"c{c}" for c in cfgs], fontsize=9)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r["task_id"] for r in rows], fontsize=8)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    _title(ax, "Per-task success rate by config")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("success rate", fontsize=9.5)
    cb.ax.tick_params(labelsize=8.5)
    _save(fig, PACK_CHARTS, "task-success-heatmap.svg")


def fig_first_tool_stacked(m) -> None:
    cfgs = [c["config_id"] for c in m["config_metadata"]]
    per = {c: Counter() for c in cfgs}
    for cell in m["cell_summaries"]:
        per[int(cell["config_id"])].update(cell.get("first_tool_families", {}))
    fams = [f for f, _ in Counter(
        {k: sum(per[c].get(k, 0) for c in cfgs) for k in set().union(*[set(per[c]) for c in cfgs])}
    ).most_common(6)]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bottom = [0] * len(cfgs)
    cmap = ["#4c78a8", "#e0913b", "#5a9367", "#9b6fb0", "#8c8c8c", "#7aa7c7"]
    for k, fam in enumerate(fams):
        vals = [per[c].get(fam, 0) for c in cfgs]
        ax.bar(range(len(cfgs)), vals, bottom=bottom, color=cmap[k % len(cmap)],
               width=0.66, label=fam, zorder=3)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(range(len(cfgs)))
    ax.set_xticklabels([f"c{c}" for c in cfgs], fontsize=9.5)
    ax.set_ylabel("First-tool count (20 tasks × 3 repeats)")
    _grid_y(ax)
    ax.legend(title="First tool family", fontsize=8, title_fontsize=8.5, frameon=False,
              loc="upper left", bbox_to_anchor=(1.0, 1.0))
    _title(ax, "First-action tool family by config")
    _save(fig, PACK_CHARTS, "first-tool-family-stacked-by-config.svg")


def fig_phase3_label_summary(m) -> None:
    p3 = m["phase3_method_consistency"]
    ld = p3["label_distribution"]
    dk = p3["decision_kind_distribution"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.4))
    a1.bar([k.replace("_", " ") for k in ld], list(ld.values()),
           color=PALETTE[:len(ld)], width=0.6, zorder=3)
    a1.set_ylabel("label count")
    a1.set_title("Factorial label", loc="left", fontsize=11)
    a1.tick_params(axis="x", rotation=20, length=0)
    a1.yaxis.grid(True, color=GRID, linewidth=0.7)
    a1.set_axisbelow(True)
    for i, v in enumerate(ld.values()):
        a1.text(i, v + 0.1, str(v), ha="center", fontsize=9.5, color="#333")
    a2.bar([k.replace("_", " ") for k in dk], list(dk.values()),
           color=PALETTE[:len(dk)], width=0.6, zorder=3)
    a2.set_title("Decision kind", loc="left", fontsize=11)
    a2.tick_params(axis="x", rotation=20, length=0)
    a2.yaxis.grid(True, color=GRID, linewidth=0.7)
    a2.set_axisbelow(True)
    for i, v in enumerate(dk.values()):
        a2.text(i, v + 0.1, str(v), ha="center", fontsize=9.5, color="#333")
    fig.suptitle("Phase 3 attribution label distributions", x=0.012, ha="left",
                 fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, PACK_CHARTS, "phase3-label-summary.svg")


def fig_factorial_by_split(m) -> None:
    rows = m["factorial_decomposition"]["contrast_by_split"]
    fams = sorted({r["contrast_family"] for r in rows})
    splits = ["controlled", "benchmark"]
    data = {(r["contrast_family"], r["task_split"]): r["mean_sequence_disagreement"] for r in rows}
    import numpy as np
    x = np.arange(len(fams))
    w = 0.36
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    for k, sp in enumerate(splits):
        ax.bar(x + (k - 0.5) * w, [data.get((f, sp), 0) for f in fams], width=w,
               color=[STEEL, "#d1894a"][k], label=sp, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f.replace("_", "\n") for f in fams], fontsize=9)
    ax.set_ylabel("Mean sequence disagreement")
    _grid_y(ax)
    ax.legend(frameon=False, fontsize=9)
    _title(ax, "Contrast disagreement by task split")
    _save(fig, PACK_CHARTS, "factorial-by-split.svg")


def fig_task_suite(m) -> None:
    rows = sorted(m["category_summaries"], key=lambda r: r["category"])
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.bar(range(len(rows)), [r["task_count"] for r in rows],
           color=[OKABE.get(r["category"], STEEL) for r in rows], width=0.62, zorder=3)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([r["category"].replace("_", " ") for r in rows], fontsize=9.5)
    ax.set_ylabel("Number of tasks")
    ax.set_ylim(0, 5)
    _grid_y(ax)
    for i, r in enumerate(rows):
        ax.text(i, r["task_count"] + 0.08, str(r["task_count"]), ha="center", fontsize=10, color="#333")
    _title(ax, "Task-suite composition  (5 categories × 4 = 20 tasks)")
    _save(fig, PACK_CHARTS, "task-suite-composition.svg")


# ── STRUCTURAL DIAGRAMS ───────────────────────────────────────────────────
def fig_research_design_pipeline() -> None:
    steps = [("6 configs", "harness × model"), ("20 tasks", "5 cats × 4"),
             ("360 traces", "3 formal repeats"), ("M1–M4", "white-box attribution"),
             ("Agent cards", "governance proxies")]
    fig, ax = _blank((9.6, 2.6))
    ax.text(0.0, 0.92, "Research design pipeline", fontsize=13, fontweight="bold", color=INK)
    w, h, y = 0.165, 0.42, 0.26
    xs = [0.02 + i * 0.197 for i in range(len(steps))]
    for i, (head, sub) in enumerate(steps):
        _box(ax, xs[i], y, w, h, head, sub)
        if i < len(steps) - 1:
            _arrow(ax, xs[i] + w + 0.004, y + h / 2, xs[i + 1] - 0.004, y + h / 2)
    _save(fig, PACK_CHARTS, "research-design-pipeline.svg")


def fig_method_ladder() -> None:
    methods = [("M1", "System prompt", "source / dossier"),
               ("M2", "Tool affordance", "source / tool surface"),
               ("M3", "Behavioral counterfactual", "executed repeats 301–312 / 401–404"),
               ("M4", "Planning-loop trace", "public trace + private replay")]
    fig, ax = _blank((9.4, 3.0))
    ax.text(0.0, 0.93, "M1–M4 attribution evidence ladder", fontsize=13, fontweight="bold", color=INK)
    ax.text(0.0, 0.83, "Each method answers a different boundary; hidden chain-of-thought omitted.",
            fontsize=9.5, color="#5a6573")
    w, h, y = 0.225, 0.5, 0.18
    for i, (m, name, ev) in enumerate(methods):
        x = 0.02 + i * 0.245
        _box(ax, x, y, w, h, "", "", fill="#eef2f7", edge="#c4d0de")
        ax.text(x + 0.02, y + h * 0.74, m, fontsize=14, fontweight="bold", color=BLUE)
        ax.text(x + 0.02, y + h * 0.5, name, fontsize=10, color=INK)
        for j, line in enumerate(_wrap(ev, 24)[:2]):
            ax.text(x + 0.02, y + h * 0.28 - j * 0.085, line, fontsize=8.2, color="#5a6573")
    _save(fig, PACK_CHARTS, "method-evidence-ladder.svg")


def fig_trace_schema() -> None:
    fields = [("identity", "config_id · harness · model · task · repeat"),
              ("tool path", "tool_calls · turns · wall_time_s"),
              ("outcome", "success · grader_detail · final diff"),
              ("replay refs", "raw_log_path · private_audit_path"),
              ("boundary", "runtime_budget · hidden CoT omitted")]
    fig, ax = _blank((9.4, 3.2))
    ax.text(0.0, 0.93, "Normalized trace schema", fontsize=13, fontweight="bold", color=INK)
    ax.text(0.0, 0.83, "Four harnesses become comparable through one sanitized JSON shape.",
            fontsize=9.5, color="#5a6573")
    w, h = 0.30, 0.30
    for i, (head, desc) in enumerate(fields):
        col, row = i % 3, i // 3
        x = 0.02 + col * 0.328
        y = 0.40 - row * 0.36
        _box(ax, x, y, w, h, "", "", fill="#f4f7fa", edge="#c8d3e0")
        ax.text(x + 0.018, y + h * 0.66, head, fontsize=10.5, fontweight="bold", color=INK)
        for j, line in enumerate(_wrap(desc, 34)[:2]):
            ax.text(x + 0.018, y + h * 0.34 - j * 0.1, line, fontsize=8.2, color="#5a6573")
    _save(fig, PACK_CHARTS, "trace-schema-evidence.svg")


def fig_config_routing_grid() -> None:
    hlabel = {"claude_code": "Claude Code", "opencode": "OpenCode", "hermes": "Hermes", "codex": "Codex"}
    plabel = {"anthropic": "Anthropic native", "openai": "OpenAI native"}
    harnesses, models, prov, cell = [], [], {}, {}
    for c in CONFIGS:
        if c.harness not in harnesses:
            harnesses.append(c.harness)
        if c.model_role not in models:
            models.append(c.model_role)
        prov[c.model_role] = c.provider
        cell[(c.model_role, c.harness)] = c
    crossed = {h for h in harnesses if sum((mo, h) in cell for mo in models) > 1}
    fig, ax = _blank((9.0, 3.8))
    ax.text(0.0, 0.95, "6 configs: harness × model routing grid", fontsize=13, fontweight="bold", color=INK)
    ax.text(0.0, 0.86, "Same model keeps one provider route; OpenCode/Hermes are crossed cells, "
            "Claude Code/Codex are anchors.", fontsize=9, color="#5a6573")
    x0, cw, gap = 0.20, 0.185, 0.012
    for ci, h in enumerate(harnesses):
        ax.text(x0 + ci * (cw + gap) + cw / 2, 0.76, hlabel.get(h, h), ha="center", fontsize=9.5, color=INK)
    rh = 0.30
    for ri, mo in enumerate(models):
        y = 0.40 - ri * (rh + 0.06)
        lbl = "Haiku 4.5" if mo == "haiku" else "GPT-5.4-mini"
        ax.text(0.0, y + rh * 0.6, lbl, fontsize=10, fontweight="bold", color=INK)
        ax.text(0.0, y + rh * 0.32, plabel.get(prov.get(mo, ""), ""), fontsize=8, color="#5a6573")
        for ci, h in enumerate(harnesses):
            x = x0 + ci * (cw + gap)
            c = cell.get((mo, h))
            if c is None:
                ax.add_patch(FancyBboxPatch((x, y), cw, rh, boxstyle="round,pad=0.006,rounding_size=0.02",
                             linewidth=1.0, edgecolor="#c9c9c9", facecolor="white", linestyle=(0, (4, 4)), mutation_aspect=0.5))
                ax.text(x + cw / 2, y + rh / 2, "not run", ha="center", va="center", fontsize=8.5, color="#9aa3ad")
                continue
            is_x = h in crossed
            _box(ax, x, y, cw, rh, "", "", fill=("#e7eef6" if is_x else "#fbeacf"),
                 edge=("#bcd0e6" if is_x else "#e6c997"))
            ax.text(x + 0.016, y + rh * 0.66, f"c{c.id}", fontsize=12.5, fontweight="bold", color=INK)
            ax.text(x + 0.016, y + rh * 0.4, hlabel.get(h, h), fontsize=8.6, color=INK)
            ax.text(x + 0.016, y + rh * 0.18, "crossed (interaction)" if is_x else "anchor",
                    fontsize=7.6, color="#5a6573")
    _save(fig, PACK_CHARTS, "config-routing-grid.svg")


ACTIONS = [
    ("Tool path diverges even when success is unchanged", "Show evidence path, not only pass/fail status."),
    ("First-tool strategies differ by harness", "Expose or standardize initial discovery affordances."),
    ("Benchmark failures cluster by category", "Separate high-risk task classes; require replay inspection."),
    ("M1–M4 agreement is partial (10/20)", "Carry confidence labels and caveats on agent cards."),
]


def fig_attribution_action_map() -> None:
    fig, ax = _blank((9.2, 4.2))
    ax.text(0.0, 0.95, "From attribution to action", fontsize=13, fontweight="bold", color=INK)
    ax.text(0.0, 0.87, "Each XAI finding maps to a concrete prompt / tool-surface governance action.",
            fontsize=9, color="#5a6573")
    ax.text(0.02, 0.79, "Finding (XAI evidence)", fontsize=8.6, color="#8794a3")
    ax.text(0.56, 0.79, "Governance action", fontsize=8.6, color="#8794a3")
    n = len(ACTIONS)
    h, top = 0.135, 0.74
    for i, (finding, action) in enumerate(ACTIONS):
        y = top - i * (h + 0.05) - h
        _box(ax, 0.02, y, 0.46, h, "", "", fill="#f4f7fa", edge="#c8d3e0")
        for j, line in enumerate(_wrap(finding, 40)[:2]):
            ax.text(0.035, y + h * (0.62 - j * 0.42), line, fontsize=9, color=INK, va="center")
        _arrow(ax, 0.49, y + h / 2, 0.55, y + h / 2)
        _box(ax, 0.56, y, 0.42, h, "", "", fill="#eaf3ec", edge="#bcd9c2")
        for j, line in enumerate(_wrap(action, 38)[:2]):
            ax.text(0.575, y + h * (0.62 - j * 0.42), line, fontsize=9, color=INK, va="center")
    _save(fig, PACK_CHARTS, "attribution-action-map.svg")


def fig_environment_controls(m) -> None:
    cfgs = m["environment_controls"]["configs"]
    rows = []
    for c in cfgs:
        ver = ", ".join(c.get("harness_versions_observed", []))[:22]
        eff = ", ".join(c.get("reasoning_efforts_observed", []))
        rows.append([f"c{c['config_id']}", c["harness"], c["model_role"], c["provider"], ver, eff, str(c["n"])])
    cols = ["Config", "Harness", "Model", "Provider", "Version", "Effort", "n"]
    fig, ax = _blank((9.6, 3.0))
    ax.text(0.0, 0.95, "Environment locks per config", fontsize=13, fontweight="bold", color=INK)
    tb = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="left", bbox=[0, 0, 1, 0.82])
    tb.auto_set_font_size(False)
    tb.set_fontsize(9)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#dde3ea")
        cell.set_linewidth(0.8)
        if r == 0:
            cell.set_facecolor("#36618e")
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#ffffff" if r % 2 else "#f5f8fb")
    _save(fig, PACK_CHARTS, "environment-controls-matrix.svg")


# ── CASE CARDS ────────────────────────────────────────────────────────────
def fig_pipeline_flow() -> None:
    steps = [
        ("1  Provision", "clean target repo;\nstrip hidden graders"),
        ("2  Fresh HOME", "new isolated HOME\nfor this run"),
        ("3  Launch", "inject model / route /\neffort=high; timeout 900s"),
        ("4  Capture", "raw + private +\npublic trace"),
        ("5  Repo guard", "detect & revert\nbaseline mutation"),
        ("6  Grade", "hidden pytest;\nall-green = pass"),
        ("7  Normalize", "unified trace +\nevidence levels"),
        ("8  Persist", "immutable trace +\nprivate audit"),
    ]
    fig, ax = _blank((10.4, 4.2))
    ax.text(0.0, 0.95, "Per-run pipeline — one (harness, model, task) run", fontsize=13, fontweight="bold", color=INK)
    w, h = 0.215, 0.30
    xs = [0.02 + i * 0.247 for i in range(4)]
    row_y = [0.50, 0.08]

    def place(i):
        return (xs[i], row_y[0]) if i < 4 else (xs[7 - i], row_y[1])

    for i, (head, sub) in enumerate(steps):
        x, y = place(i)
        _box(ax, x, y, w, h, "", "", fill="#eef2f7", edge="#c4d0de")
        ax.text(x + 0.014, y + h * 0.66, head, fontsize=10.5, fontweight="bold", color=INK)
        for j, line in enumerate(sub.split("\n")[:2]):
            ax.text(x + 0.014, y + h * 0.36 - j * 0.105, line, fontsize=8.0, color="#5a6573")
    for i in range(3):
        x0, y0 = place(i)
        x1, y1 = place(i + 1)
        _arrow(ax, x0 + w + 0.004, y0 + h / 2, x1 - 0.004, y1 + h / 2)
    x3, y3 = place(3)
    x4, y4 = place(4)
    _arrow(ax, x3 + w / 2, y3 - 0.004, x4 + w / 2, y4 + h + 0.004)
    for i in range(4, 7):
        x0, y0 = place(i)
        x1, y1 = place(i + 1)
        _arrow(ax, x0 - 0.004, y0 + h / 2, x1 + w + 0.004, y1 + h / 2)
    _save(fig, PACK_CHARTS, "pipeline-flow.svg")


def fig_isolation_hierarchy() -> None:
    fig, ax = _blank((9.6, 4.2))
    ax.text(0.0, 0.95, "Isolation: clean per-run environment, production untouched", fontsize=13, fontweight="bold", color=INK)
    ax.add_patch(FancyBboxPatch((0.02, 0.10), 0.62, 0.74, boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=1.2, edgecolor="#9fb2c8", facecolor="#f4f7fa"))
    ax.text(0.05, 0.785, "Execution root  /data/harness-lab", fontsize=11, fontweight="bold", color=INK)
    ax.text(0.05, 0.735, "all 4 harnesses installed, versions pinned", fontsize=8.4, color="#5a6573")
    _box(ax, 0.05, 0.45, 0.56, 0.21, "", "")
    ax.text(0.07, 0.605, "Per-run fresh HOME", fontsize=10, fontweight="bold", color=INK)
    for j, line in enumerate(["runs/<config>/<task>/<repeat>/home — reset every run;", "no shared session / memory / log / cache"]):
        ax.text(0.07, 0.555 - j * 0.046, line, fontsize=8.2, color="#5a6573")
    _box(ax, 0.05, 0.15, 0.56, 0.22, "", "", fill="#eef3ee", edge="#bcd0c2")
    ax.text(0.07, 0.325, "Hermes: independent HERMES_HOME", fontsize=10, fontweight="bold", color=INK)
    for j, line in enumerate(["clean instance, same v0.13.0 as production,", "but separate state — never writes production dir"]):
        ax.text(0.07, 0.275 - j * 0.046, line, fontsize=8.2, color="#5a6573")
    ax.plot([0.68, 0.68], [0.12, 0.82], color="#c0392b", linewidth=1.4, linestyle=(0, (5, 4)))
    ax.text(0.69, 0.85, "no-touch barrier", fontsize=8, color="#c0392b")
    ax.add_patch(FancyBboxPatch((0.72, 0.33), 0.26, 0.32, boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=1.2, edgecolor="#e0b4ad", facecolor="#fbf0ee"))
    ax.text(0.745, 0.585, "Production Hermes", fontsize=10, fontweight="bold", color=INK)
    for j, line in enumerate(["/home/opc/.hermes", "(production Discord bot)", "config frozen,", "service undisturbed"]):
        ax.text(0.745, 0.525 - j * 0.05, line, fontsize=8.2, color="#5a6573")
    _save(fig, PACK_CHARTS, "isolation-hierarchy.svg")


def fig_grader_flow() -> None:
    steps = [
        ("Hidden test", "tasks/graders/<task>_test.py\nkept out of workdir"),
        ("Copy in", "as _hidden_grader_test.py\ninto the run workdir"),
        ("Run pytest", "python -m pytest -q\n(runner venv)"),
        ("All green?", "returncode 0 = pass\nelse = fail"),
        ("Clean up", "delete hidden test\nafter grading"),
    ]
    fig, ax = _blank((10.2, 2.9))
    ax.text(0.0, 0.93, "Grading — deterministic hidden pytest (no LLM judge)", fontsize=13, fontweight="bold", color=INK)
    w, h = 0.17, 0.42
    xs = [0.02 + i * 0.197 for i in range(5)]
    for i, (head, sub) in enumerate(steps):
        x, y = xs[i], 0.30
        _box(ax, x, y, w, h, "", "")
        ax.text(x + 0.012, y + h * 0.74, head, fontsize=10, fontweight="bold", color=INK)
        for j, line in enumerate(sub.split("\n")[:2]):
            ax.text(x + 0.012, y + h * 0.46 - j * 0.11, line, fontsize=7.6, color="#5a6573")
        if i < 4:
            _arrow(ax, x + w + 0.003, y + h / 2, xs[i + 1] - 0.003, y + h / 2)
    ax.text(0.0, 0.06, "Tier 1: Exercism unittest    ·    Tier 2: behavior verifier (property, not patch text)", fontsize=8.8, color="#5a6573")
    _save(fig, PACK_CHARTS, "grader-flow.svg")


def _case_panel(ax, x, side, title):
    _box(ax, x, 0.06, 0.46, 0.66, "", "", fill="#f6f8fb", edge="#cdd8e4")
    ax.text(x + 0.02, 0.66, f"{title}: c{side['config']} {side['harness']}", fontsize=10.5, fontweight="bold", color=INK)
    ax.text(x + 0.02, 0.60, side["model"], fontsize=8.4, color="#5a6573")
    ax.text(x + 0.02, 0.52, f"Outcome: {side['success_count']}/{side['n']} successful repeats",
            fontsize=9.2, color=INK)
    ax.text(x + 0.02, 0.45, "Dominant tool-family path", fontsize=8.4, color="#5a6573")
    seq = " → ".join(side.get("dominant_tool_family_sequence", []))
    for j, line in enumerate(_wrap(seq, 40)[:6]):
        ax.text(x + 0.02, 0.39 - j * 0.055, line, fontsize=8.6, color=INK, family="DejaVu Sans")


def fig_case_cards() -> None:
    cases = _load(CASE_PACK).get("cases", [])
    for i, case in enumerate(cases, start=1):
        fig, ax = _blank((9.0, 4.6))
        ma = case.get("method_agreement", {})
        ax.text(0.0, 0.95, f"Case {i}: {case['task_id']} · {case['factorial_label'].replace('_',' ')}",
                fontsize=13, fontweight="bold", color=INK)
        ax.text(0.0, 0.86, f"{case['decision_kind'].replace('_',' ')} · {case.get('confidence','')} confidence "
                f"· M1–M4 agreement {ma.get('agreement_count','?')}/{ma.get('method_count','?')}",
                fontsize=9.2, color="#5a6573")
        _case_panel(ax, 0.02, case.get("left", {}), "Left")
        _case_panel(ax, 0.52, case.get("right", {}), "Right")
        _save(fig, PACK_CHARTS, f"xai-case-card-{i:02d}.svg")


def _wrap(text: str, n: int):
    words = str(text).split()
    out, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= n:
            cur += " " + w
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [""]


def render_phase4_figures(m, out_dir=None) -> None:
    """Render the 5 Phase 4 figures from a metrics/analysis dict (no disk read)."""
    global PHASE4_FIG
    _setup()
    if out_dir is not None:
        PHASE4_FIG = Path(out_dir)
    fig_jaccard(m); fig_factorial(m); fig_scatter(m); fig_method_consistency(m); fig_agent_card(m)


def render_phase5_charts(m=None, out_dir=None) -> None:
    """Render the Phase 5 pack charts (data plots, diagrams, case cards)."""
    global PACK_CHARTS
    _setup()
    if out_dir is not None:
        PACK_CHARTS = Path(out_dir)
    m = m if m is not None else _load(METRICS)
    fig_trace_inventory(); fig_config_success(m); fig_controlled_vs_benchmark(m)
    fig_category_success_cost(m); fig_task_difficulty(m); fig_task_success_heatmap(m)
    fig_first_tool_stacked(m); fig_phase3_label_summary(m); fig_factorial_by_split(m); fig_task_suite(m)
    fig_research_design_pipeline(); fig_method_ladder(); fig_trace_schema()
    fig_config_routing_grid(); fig_attribution_action_map(); fig_environment_controls(m)
    fig_pipeline_flow(); fig_isolation_hierarchy(); fig_grader_flow()
    fig_case_cards()


def render_all() -> list[str]:
    m = _load(METRICS)
    render_phase4_figures(m)
    render_phase5_charts(m)
    out = sorted([str(p.relative_to(REPO)) for p in PHASE4_FIG.glob("*.svg")] +
                 [str(p.relative_to(REPO)) for p in PACK_CHARTS.glob("*.svg")])
    return out


if __name__ == "__main__":
    files = render_all()
    print(json.dumps({"ok": True, "repo": str(REPO), "figure_count": len(files), "figures": files},
                     ensure_ascii=False, indent=2))
