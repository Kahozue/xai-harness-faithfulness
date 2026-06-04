from __future__ import annotations

import json
from pathlib import Path

from runner.phase5_xai_pack import build_phase5_xai_pack_data, write_phase5_xai_pack


def test_phase5_pack_data_keeps_xai_boundary():
    data = build_phase5_xai_pack_data()

    assert data["boundary"]["pptx_created"] is False
    assert "HCI human-study" in data["boundary"]["scope"]
    assert data["trace_inventory"]["classes"]["formal_baseline"] == 360
    assert data["trace_inventory"]["classes"]["pilot"] == 6
    assert data["trace_inventory"]["classes"]["phase3_counterfactual_or_extra"] == 30
    assert len(data["slide_map"]) == 27
    assert data["boundary"]["canonical_deck_basis"].endswith("content-draft.md (27 slides)")
    assert data["boundary"]["deprecated_deck"].endswith("index.html is not a canonical source.")
    assert any(
        "HCI human-study" in slide["note"]
        for slide in data["slide_map"]
    )
    case_slide = next(slide for slide in data["slide_map"] if slide["slide"] == 22)
    assert case_slide["charts"] == ["charts/xai-case-card-03.svg"]
    assert "OpenCode vs Hermes" in case_slide["note"]
    assert all("_" not in table for slide in data["slide_map"] for table in slide["tables"])


def test_write_phase5_pack_outputs_tables_charts_and_no_pptx(tmp_path):
    data = build_phase5_xai_pack_data()
    outputs = write_phase5_xai_pack(data, tmp_path / "pack")

    assert outputs["manifest"].exists()
    assert outputs["readme"].exists()
    assert outputs["slide_map"].exists()
    assert outputs["slide_ready_data"].exists()
    assert outputs["chart_manifest"].exists()
    assert not list(outputs["pack_dir"].glob("*.pptx"))

    manifest = json.loads(outputs["manifest"].read_text())
    assert manifest["boundary"]["pptx_created"] is False
    assert "headline_stats" in manifest["tables"]
    assert "trace-inventory.svg" in manifest["charts"]["generated"]
    assert len(manifest["charts"]["generated"]) >= 14
    assert (outputs["pack_dir"] / "tables" / "headline-stats.csv").exists()
    assert (outputs["pack_dir"] / "charts" / "task-success-heatmap.svg").exists()

    repo = Path(__file__).resolve().parents[1]
    slide_map = json.loads(outputs["slide_map"].read_text())
    for slide in slide_map:
        for table in slide["tables"]:
            assert (outputs["pack_dir"] / "tables" / table).exists(), (slide["slide"], table)
        for chart in slide["charts"]:
            if chart.startswith("analysis/"):
                assert (repo / chart).exists(), (slide["slide"], chart)
            else:
                assert (outputs["pack_dir"] / chart).exists(), (slide["slide"], chart)
