import subprocess
import sys
from pathlib import Path

TARGET = "tests/test_median_extra.py"


def test_file_exists():
    assert Path(TARGET).exists(), f"agent 應建立 {TARGET}"


def test_meaningful_and_green():
    body = Path(TARGET).read_text()
    assert "median" in body, "新增測試應實際呼叫 median"
    assert "2.5" in body, "應涵蓋偶數長度中位平均（2.5）"
    r = subprocess.run([sys.executable, "-m", "pytest", TARGET, "-q"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
