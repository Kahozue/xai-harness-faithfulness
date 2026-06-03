import subprocess
import sys
from pathlib import Path

TARGET = "tests/test_mean_errors.py"


def test_file_exists():
    assert Path(TARGET).exists(), f"agent 應建立 {TARGET}"


def test_meaningful_and_green():
    body = Path(TARGET).read_text()
    assert "mean" in body, "新增測試應實際呼叫 mean"
    assert "ValueError" in body or "raises" in body, "應斷言 raise ValueError"
    r = subprocess.run([sys.executable, "-m", "pytest", TARGET, "-q"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
