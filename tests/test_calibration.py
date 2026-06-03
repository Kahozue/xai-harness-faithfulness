"""D3 難度校準：對 registry 中所有 Tier-2 任務，斷言 baseline（未修）狀態下隱藏測試為 fail。
保證每題都有區辨力（不會 success 觸底/觸頂）。"""
import pytest
from runner.provision import load_tasks, provision_task
from runner.grader import run_grader

TIER2 = [t for t in load_tasks() if t["tier"] == 2]


@pytest.mark.parametrize("task", TIER2, ids=[t["id"] for t in TIER2])
def test_baseline_fails(task, tmp_path):
    wd = provision_task(task, tmp_path / task["id"])
    assert run_grader(task, wd).success is False, f"{task['id']} baseline 未 fail，無區辨力"
