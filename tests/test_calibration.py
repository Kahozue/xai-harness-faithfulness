"""D3 難度校準：對 registry 中所有任務，斷言 baseline（未修）狀態下隱藏測試為 fail。
保證每題都有區辨力（不會 success 觸底/觸頂）。涵蓋受控套件與 benchmark。"""
import pytest
from runner.provision import load_tasks, provision_task
from runner.grader import run_grader

ALL_TASKS = load_tasks()


@pytest.mark.parametrize("task", ALL_TASKS, ids=[t["id"] for t in ALL_TASKS])
def test_baseline_fails(task, tmp_path):
    wd = provision_task(task, tmp_path / task["id"])
    assert run_grader(task, wd).success is False, f"{task['id']} baseline 未 fail，無區辨力"
