from runner.provision import load_tasks, provision_task
from runner.grader import run_grader


def _task(tid):
    return {t["id"]: t for t in load_tasks()}[tid]


def test_grader_fails_on_baseline(tmp_path):
    wd = provision_task(_task("bugfix-t2-01"), tmp_path / "wd")
    res = run_grader(_task("bugfix-t2-01"), wd)
    assert res.success is False
    assert "failed" in res.detail.lower() or "error" in res.detail.lower()


def test_grader_passes_on_reference_fix(tmp_path):
    wd = provision_task(_task("bugfix-t2-01"), tmp_path / "wd")
    # 套用 reference solution（修好 parse_amount）
    money = wd / "calckit" / "money.py"
    money.write_text(
        'from __future__ import annotations\n\n\n'
        'def parse_amount(s: str) -> float:\n'
        '    s = s.strip()\n'
        '    neg = s.startswith("(") and s.endswith(")")\n'
        '    if neg:\n'
        '        s = s[1:-1]\n'
        '    cleaned = s.replace("$", "").replace(",", "").strip()\n'
        '    v = float(cleaned)\n'
        '    return -v if neg else v\n\n\n'
        'def format_amount(value: float) -> str:\n'
        '    return f"${value:,.2f}"\n'
    )
    res = run_grader(_task("bugfix-t2-01"), wd)
    assert res.success is True, res.detail
