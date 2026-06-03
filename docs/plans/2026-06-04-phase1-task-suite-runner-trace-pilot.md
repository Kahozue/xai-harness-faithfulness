# Phase 1 — 任務套件、統一 Runner、正規化 Trace、Pilot 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建出可重現的實驗引擎——20 題受控且可自動評分的 agentic 任務套件、統一 Runner（對 (harness, model, task) 開乾淨副本、注入模型與 high effort、固定 timeout、擷取並正規化 trace、自動評分、不可變存檔）、四個 harness 介面卡、跨 harness 可比的正規化 Trace schema——並以 Pilot（2 configs × 3 tasks）端到端驗證管線、grader 與成本/時間，產出 Pilot 報告作為放大 Phase 2 的放行關。

**2026-06-04 實作修訂（Task 11 決策後）：** 任務套件實作定案為五類各 4 題、總數 20：
`bug_fix`、`rename`、`add_tests`、`add_logging`、`benchmark`。SWE-bench Verified / docker / qemu 路線已放棄，
benchmark 類改用 Aider-polyglot Python/Exercism 4 題。後續執行與 Phase 2 文件均以此分布為準。

**Architecture:** 引擎為一個 Python 套件 `runner/`（進 git），以 `/usr/bin/python3.11` 建專屬 venv（`/data/harness-lab/runner-venv`，repo 外）。任務套件 `tasks/` 採資料驅動：`tasks/registry.yaml` 定義每題（category、tier、baseline repo 狀態、prompt、隱藏 pytest 驗證檔、provenance）。Grader 為單一機制：把任務的隱藏測試在「agent 跑完的乾淨 workdir」內以 pytest 執行，全綠才 pass；隱藏測試**只在評分時**複製進 workdir，agent 工作期間看不到（contamination 控制）。四個 harness 以介面卡封裝差異（啟動指令、模型/effort/budget 注入、trace 來源各不同），全部 normalize 成同一 `NormalizedTrace`。raw log 與 workdir 留 `/data/harness-lab/runs/`（repo 外、不進 git）；sanitize 後的 `trace.json` commit 進 repo `traces/`。

**Tech Stack:** Python 3.11.13（`/usr/bin/python3.11`）、pytest、PyYAML、jsonschema；四 harness 啟動沿用 Phase 0 已驗證指令（claude-trace / codex exec / opencode run / hermes -z）；模型 `claude-haiku-4-5-20251001`（Anthropic 原生）、`gpt-5.4-mini-2026-03-17`（OpenAI 原生）。

**執行位置：** 全部在 server `opc@150.230.202.49`，repo `/data/repos/xai-harness-faithfulness`，分支 `main`。本機（Mac）僅用來編輯檔案後 scp，或直接於 server 編輯。所有指令以 `source infra/00-paths.sh` 取得 `LAB`/`LAB_HOME`/`LAB_BIN`/secrets。

**前置（已滿足）：** Phase 0 全 13 task 完成、`ENVIRONMENT.lock.md` 與 7 份 dossier 經使用者審閱通過（Phase 0 gate 已放行）。四 harness 已釘死安裝於 `/data/harness-lab/`，6 configs 的 smoke 已跑通並留有 trace 於 `/data/harness-lab/smoke/`（本計畫直接拿來當 adapter 的測試 fixtures）。

**Gate（Pilot 放行關）：** Task 1–15 完成且 Task 16 Pilot（2 configs × 3 tasks）端到端跑通、Pilot 報告經使用者審閱通過後，才進入 Phase 2 全量 factorial（6×20×3）。本計畫**只跑 Pilot 規模的真實 run**，不跑全量。

**設計決策（本 Phase 拍板，記入報告「決策紀錄」）：**
- D1：Tier-1/benchmark 取材＝Aider-polyglot Python/Exercism 4 題；受控 Tier-2 類別為 bug_fix / rename / add_tests / add_logging 各 4 題。SWE-bench Verified 不進 Phase 1 任務套件。
- D2：Tier-2 target repo 語言＝Python 3.11；grader 統一為「跑隱藏 pytest 驗證檔」。
- D3：難度校準必做——每題的隱藏測試須「在 baseline（未修）狀態下 fail、在 reference solution 下 pass」，且整體難度調到小模型能完成一部分（避免 success 觸底、無分歧訊號）。

---

## 檔案結構（本 Phase 產出）

repo `xai-harness-faithfulness/` 內（**進 git**）：

- `runner/__init__.py`、`runner/paths.py` — 路徑與 secrets 載入（鏡像 `infra/00-paths.sh`）
- `runner/trace_schema.py` — §6.3 `NormalizedTrace` 與驗證
- `runner/configs.py` — 6 configs 註冊表
- `runner/provision.py` — 每題開乾淨 workdir（baseline 複製 + setup patch；不含隱藏測試）
- `runner/grader.py` — 統一 grader（在 workdir 跑隱藏 pytest → pass/fail + detail）
- `runner/adapters/__init__.py`、`base.py`、`claude_code.py`、`codex.py`、`opencode.py`、`hermes.py`
- `runner/runner.py` — 單次 (config, task, repeat) 端到端編排
- `runner/persist.py` — 不可變存檔（raw 在 LAB、normalized trace.json commit 進 `traces/`）
- `runner/cli.py` — `python -m runner ...`
- `runner/requirements.txt` — 釘死相依
- `tasks/registry.yaml` — 20 題 metadata
- `tasks/target_repo/` — Tier-2 受控 Python 目標 repo baseline（釘死）
- `tasks/baselines/<task_id>.patch` — 把 baseline 變成各題初始狀態（如植入 bug、移除待加之物）
- `tasks/graders/<task_id>_test.py` — 各題隱藏 pytest 驗證檔
- `tasks/benchmark/<exercise>/` — Aider-polyglot Python/Exercism benchmark baseline 與 provenance
- `tests/` — 引擎自身的 pytest（用 smoke trace 當 fixtures，不花 API token）
- `traces/<config_id>/<task_id>/<repeat_index>.json` — Pilot 產出的正規化 trace（sanitized、committed）
- `docs/verification/2026-06-04-phase1-pilot-report.md` — Pilot 報告（放行關文件）

runtime（**repo 外、不進 git**）：

- `/data/harness-lab/runner-venv/` — 引擎 venv
- `/data/harness-lab/runs/<config_id>/<task_id>/<repeat_index>/workdir/` — 每次 run 的乾淨 repo 副本（agent 在此工作）
- `/data/harness-lab/runs/.../raw/` — 各 harness 原始 log（claude-trace jsonl、codex.log + rollout、oc.log、hermes session）

---

## Task 1: 引擎骨架 + 專屬 venv + paths + 相依釘死 + pytest scaffold

**Files:**
- Create: `runner/__init__.py`、`runner/paths.py`、`runner/requirements.txt`
- Create: `tests/__init__.py`、`tests/test_paths.py`
- Create: `pytest.ini`

- [ ] **Step 1: 寫 `runner/requirements.txt`（釘死值於 Step 3 安裝後回填確切版本）**

```
PyYAML
jsonschema
pytest
datasets
huggingface_hub
```

- [ ] **Step 2: 寫 `runner/paths.py`**

```python
"""實驗引擎的路徑與 secrets 載入，鏡像 infra/00-paths.sh（單一事實來源仍是該 shell 檔）。"""
from __future__ import annotations
import os
from pathlib import Path

REPO = Path("/data/repos/xai-harness-faithfulness")
LAB = Path("/data/harness-lab")
LAB_HOME = LAB / "home"
LAB_BIN = LAB / "bin"
RUNS = LAB / "runs"
RUNNER_VENV = LAB / "runner-venv"
SECRETS = Path.home() / ".harness-exp"

ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
HERMES_BIN = Path.home() / ".local" / "bin" / "hermes"  # 二進位在真實 HOME（見 smoke-hermes.sh）


def load_secrets() -> dict[str, str]:
    """從 ~/.harness-exp/{anthropic,openai}.env 讀 KEY=VALUE；不印出值。"""
    env: dict[str, str] = {}
    for name in ("anthropic.env", "openai.env"):
        p = SECRETS / name
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def has_secret(name: str) -> bool:
    return name in load_secrets()
```

- [ ] **Step 3: 建 venv 並安裝相依（釘死），回填 requirements.txt**

Run（於 server）:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
/usr/bin/python3.11 -m venv /data/harness-lab/runner-venv &&
/data/harness-lab/runner-venv/bin/pip install -q --upgrade pip &&
/data/harness-lab/runner-venv/bin/pip install -q PyYAML jsonschema pytest datasets huggingface_hub &&
/data/harness-lab/runner-venv/bin/python -c \"import yaml,jsonschema,pytest,datasets,huggingface_hub;print('\''deps-ok'\'')\" &&
/data/harness-lab/runner-venv/bin/pip freeze | grep -Ei \"^(PyYAML|jsonschema|pytest|datasets|huggingface-hub)==\"
"'
```
Expected: 印出 `deps-ok` 與五個 `==版本` 行。把這五行的確切版本回填到 `runner/requirements.txt`（每行 `pkg==x.y.z`），並把 Python 版本（3.11.13）與 venv 路徑追加記到 `ENVIRONMENT.lock.md` 的「執行環境」段（新增一列：`runner-venv: /data/harness-lab/runner-venv（python 3.11.13），相依見 runner/requirements.txt`）。

- [ ] **Step 4: 寫 `pytest.ini`**

```ini
[pytest]
testpaths = tests
addopts = -q
```

- [ ] **Step 5: 寫 `runner/__init__.py`（空）與失敗測試 `tests/test_paths.py`**

```python
from runner import paths


def test_lab_paths_are_absolute():
    assert paths.LAB.is_absolute()
    assert paths.RUNS == paths.LAB / "runs"
    assert paths.RUNNER_VENV.exists(), "venv 應已於 Task1 Step3 建好"


def test_models_pinned():
    assert paths.ANTHROPIC_MODEL == "claude-haiku-4-5-20251001"
    assert paths.OPENAI_MODEL == "gpt-5.4-mini-2026-03-17"


def test_secrets_loadable_without_leaking():
    s = paths.load_secrets()
    # 不斷言值，只斷言兩把 key 都載入得到（檔案存在於 server）
    assert "ANTHROPIC_API_KEY" in s
    assert "OPENAI_API_KEY" in s
```

- [ ] **Step 6: 跑測試（先確認 import 與 venv 正確）**

Run（於 server，repo 根）:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && /data/harness-lab/runner-venv/bin/python -m pytest tests/test_paths.py -v'
```
Expected: 3 passed。若 `test_secrets_loadable` 失敗，先確認 `~/.harness-exp/{anthropic,openai}.env` 存在且格式為 `KEY=VALUE`（Phase 0 已建）。

- [ ] **Step 7: 確保 runtime 產物不進 git**

於 repo `.gitignore` 末尾追加（若尚未存在）:
```
# Phase 1 runtime（repo 外的 /data/harness-lab 本就不在 repo；此處僅防誤建同名目錄）
/runner-venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 8: Commit**

```bash
git add runner/__init__.py runner/paths.py runner/requirements.txt pytest.ini tests/__init__.py tests/test_paths.py .gitignore ENVIRONMENT.lock.md
git commit -m "feat(runner): engine skeleton, isolated python3.11 venv, paths + secrets loader


```

---

## Task 2: 正規化 Trace schema（§6.3）

**Files:**
- Create: `runner/trace_schema.py`
- Test: `tests/test_trace_schema.py`

- [ ] **Step 1: 寫失敗測試 `tests/test_trace_schema.py`**

```python
import pytest
from runner.trace_schema import NormalizedTrace, ToolCall, validate_trace


def _minimal_kwargs():
    return dict(
        run_id="cc__bugfix-t2-01__0",
        config_id=1,
        harness="claude_code",
        harness_version="2.1.88",
        model="claude-haiku-4-5-20251001",
        model_snapshot="claude-haiku-4-5-20251001",
        task_id="bugfix-t2-01",
        task_category="bug_fix",
        repeat_index=0,
        reasoning_effort="high",
        tool_calls=[ToolCall(step=1, tool_name="Read", args_summary="hello.py", ts=None)],
        reasoning_steps=[],
        decision_points=[],
        outcome={"success": True, "grader_detail": "3 passed", "final_diff_path": None},
        tokens={"input": None, "cached_input": None, "output": None},
        wall_time_s=12.3,
        turns=3,
        runtime_budget={"max_output_tokens": 64000, "thinking_budget_tokens": 63999,
                        "context_window_tokens": 200000, "effort_source": "cli --effort high"},
        raw_log_path="/data/harness-lab/runs/1/bugfix-t2-01/0/raw/claude-trace.jsonl",
        env_lock_ref="ENVIRONMENT.lock.md@<commit>",
        timestamp="2026-06-04T10:00:00Z",
    )


def test_trace_roundtrips_to_dict():
    t = NormalizedTrace(**_minimal_kwargs())
    d = t.to_dict()
    assert d["tool_calls"][0]["tool_name"] == "Read"
    assert d["runtime_budget"]["max_output_tokens"] == 64000


def test_validate_accepts_minimal():
    t = NormalizedTrace(**_minimal_kwargs())
    validate_trace(t.to_dict())  # 不應 raise


def test_validate_rejects_missing_required():
    d = NormalizedTrace(**_minimal_kwargs()).to_dict()
    del d["tool_calls"]
    with pytest.raises(Exception):
        validate_trace(d)


def test_tool_calls_are_ordered_by_step():
    kw = _minimal_kwargs()
    kw["tool_calls"] = [ToolCall(2, "Edit", "hello.py", None), ToolCall(1, "Read", "hello.py", None)]
    t = NormalizedTrace(**kw)
    steps = [tc["step"] for tc in t.to_dict()["tool_calls"]]
    assert steps == [1, 2], "to_dict 應依 step 排序，保證有序 tool 序列"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_trace_schema.py -v`
Expected: FAIL（`ModuleNotFoundError: runner.trace_schema`）。

- [ ] **Step 3: 寫 `runner/trace_schema.py`**

```python
"""§6.3 正規化 Trace schema：跨 harness 可比的單筆 run JSON。"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import jsonschema

VALID_CATEGORIES = {"rename", "add_tests", "add_logging", "bug_fix"}
VALID_HARNESSES = {"claude_code", "codex", "opencode", "hermes"}


@dataclass
class ToolCall:
    step: int
    tool_name: str
    args_summary: str
    ts: Optional[str]  # ISO8601 或 None（部分 harness 無逐工具時間戳）


@dataclass
class NormalizedTrace:
    run_id: str
    config_id: int
    harness: str
    harness_version: str
    model: str
    model_snapshot: str
    task_id: str
    task_category: str
    repeat_index: int
    reasoning_effort: str
    tool_calls: list[ToolCall]
    reasoning_steps: list[dict[str, Any]]
    decision_points: list[dict[str, Any]]
    outcome: dict[str, Any]            # {success: bool, grader_detail: str, final_diff_path: str|None}
    tokens: dict[str, Optional[int]]   # {input, cached_input, output}
    wall_time_s: Optional[float]
    turns: Optional[int]
    runtime_budget: dict[str, Any]     # {max_output_tokens, thinking_budget_tokens, context_window_tokens, effort_source}
    raw_log_path: str
    env_lock_ref: str
    timestamp: str
    # 跨 harness 誠實標註：每欄位的證據等級（見 dossier M4：direct/source-derived/inferred/unknown）
    evidence_levels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tool_calls"] = sorted(d["tool_calls"], key=lambda tc: tc["step"])
        return d


_SCHEMA = {
    "type": "object",
    "required": [
        "run_id", "config_id", "harness", "harness_version", "model", "model_snapshot",
        "task_id", "task_category", "repeat_index", "reasoning_effort", "tool_calls",
        "reasoning_steps", "decision_points", "outcome", "tokens", "runtime_budget",
        "raw_log_path", "env_lock_ref", "timestamp",
    ],
    "properties": {
        "harness": {"enum": sorted(VALID_HARNESSES)},
        "task_category": {"enum": sorted(VALID_CATEGORIES)},
        "reasoning_effort": {"const": "high"},
        "tool_calls": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step", "tool_name", "args_summary", "ts"],
                "properties": {"step": {"type": "integer"}, "tool_name": {"type": "string"}},
            },
        },
        "outcome": {"type": "object", "required": ["success", "grader_detail"]},
        "runtime_budget": {"type": "object", "required": ["effort_source"]},
    },
}


def validate_trace(d: dict[str, Any]) -> None:
    jsonschema.validate(instance=d, schema=_SCHEMA)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_trace_schema.py -v`
Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
git add runner/trace_schema.py tests/test_trace_schema.py
git commit -m "feat(runner): normalized cross-harness trace schema + validation


```

---

## Task 3: 6 configs 註冊表

**Files:**
- Create: `runner/configs.py`
- Test: `tests/test_configs.py`

- [ ] **Step 1: 寫失敗測試 `tests/test_configs.py`**

```python
from runner.configs import CONFIGS, get_config


def test_six_configs_exact():
    assert len(CONFIGS) == 6
    ids = [c.id for c in CONFIGS]
    assert ids == [1, 2, 3, 4, 5, 6]


def test_config_routing_matches_spec():
    by_id = {c.id: c for c in CONFIGS}
    assert (by_id[1].harness, by_id[1].provider) == ("claude_code", "anthropic")
    assert (by_id[2].harness, by_id[2].provider) == ("opencode", "anthropic")
    assert (by_id[3].harness, by_id[3].provider) == ("hermes", "anthropic")
    assert (by_id[4].harness, by_id[4].provider) == ("opencode", "openai")
    assert (by_id[5].harness, by_id[5].provider) == ("hermes", "openai")
    assert (by_id[6].harness, by_id[6].provider) == ("codex", "openai")


def test_haiku_configs_use_anthropic_native():
    for c in CONFIGS:
        if c.model_snapshot == "claude-haiku-4-5-20251001":
            assert c.provider == "anthropic"
        if c.model_snapshot == "gpt-5.4-mini-2026-03-17":
            assert c.provider == "openai"


def test_get_config():
    assert get_config(6).harness == "codex"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_configs.py -v`
Expected: FAIL（`ModuleNotFoundError`）。

- [ ] **Step 3: 寫 `runner/configs.py`**

```python
"""§4 的 6 configs（控制變數：同一模型固定走同一後端）。"""
from __future__ import annotations
from dataclasses import dataclass
from runner import paths


@dataclass(frozen=True)
class Config:
    id: int
    harness: str       # claude_code | codex | opencode | hermes
    model_role: str    # haiku | gptmini
    model_snapshot: str
    provider: str      # anthropic | openai（後端 = 原生）
    role: str          # 說明（anchor 等）


_HAIKU = paths.ANTHROPIC_MODEL
_GPTMINI = paths.OPENAI_MODEL

CONFIGS: list[Config] = [
    Config(1, "claude_code", "haiku", _HAIKU, "anthropic", "anchor: 橫向 harness 基準"),
    Config(2, "opencode", "haiku", _HAIKU, "anthropic", ""),
    Config(3, "hermes", "haiku", _HAIKU, "anthropic", ""),
    Config(4, "opencode", "gptmini", _GPTMINI, "openai", ""),
    Config(5, "hermes", "gptmini", _GPTMINI, "openai", ""),
    Config(6, "codex", "gptmini", _GPTMINI, "openai", "anchor"),
]


def get_config(config_id: int) -> Config:
    for c in CONFIGS:
        if c.id == config_id:
            return c
    raise KeyError(f"unknown config_id={config_id}")
```

- [ ] **Step 4: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_configs.py -v`
Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
git add runner/configs.py tests/test_configs.py
git commit -m "feat(runner): 6-config registry with pinned model routing


```

---

## Task 4: Tier-2 受控 target repo baseline + 任務 registry + provision

**Files:**
- Create: `tasks/target_repo/`（受控 Python 套件 baseline）
- Create: `tasks/registry.yaml`（先放結構與第 1 題）
- Create: `runner/provision.py`
- Test: `tests/test_provision.py`

說明：target repo 是一個釘死、contamination-free 的小型 Python 套件，內含足夠表面積讓四類任務（rename / add_tests / add_logging / bug_fix）都能在其上設計。每題的「初始狀態」＝ baseline 複製後套用該題的 `setup_patch`（例如把某函式改成有 bug、或刪掉待補的 log）。隱藏測試**不在** baseline 內，評分時才複製進去。

- [ ] **Step 1: 建 target repo baseline（受控 Python 套件）**

Create `tasks/target_repo/calckit/__init__.py`:
```python
"""calckit：受控目標套件（Phase 1 任務基座，contamination-free，2026-06-04 自撰）。"""
from .money import format_amount, parse_amount
from .stats import mean, median
__all__ = ["format_amount", "parse_amount", "mean", "median"]
```

Create `tasks/target_repo/calckit/money.py`:
```python
"""金額字串處理。"""
from __future__ import annotations


def parse_amount(s: str) -> float:
    """把 '$1,234.50' 解析成 1234.50。"""
    cleaned = s.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def format_amount(value: float) -> str:
    """把 1234.5 格式化成 '$1,234.50'。"""
    return f"${value:,.2f}"
```

Create `tasks/target_repo/calckit/stats.py`:
```python
"""基本統計。"""
from __future__ import annotations
from typing import Sequence


def mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("empty sequence")
    return sum(xs) / len(xs)


def median(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("empty sequence")
    ordered = sorted(xs)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2
```

Create `tasks/target_repo/tests/test_basic.py`（這是 repo 內公開測試，agent 看得到；隱藏驗證另放 `tasks/graders/`）:
```python
from calckit import parse_amount, format_amount, mean, median


def test_parse_amount():
    assert parse_amount("$1,234.50") == 1234.50


def test_format_amount():
    assert format_amount(1234.5) == "$1,234.50"


def test_mean():
    assert mean([1, 2, 3]) == 2


def test_median_odd():
    assert median([3, 1, 2]) == 2
```

Create `tasks/target_repo/pyproject.toml`:
```toml
[project]
name = "calckit"
version = "0.0.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["."]
include = ["calckit*"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: 驗證 baseline 自身可裝可測（健全性）**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'bash -lc "
cd /data/repos/xai-harness-faithfulness && cp -r tasks/target_repo /tmp/ck && cd /tmp/ck &&
/data/harness-lab/runner-venv/bin/pip install -q -e . &&
/data/harness-lab/runner-venv/bin/python -m pytest -q && rm -rf /tmp/ck"'
```
Expected: 4 passed。

- [ ] **Step 3: 寫 `tasks/registry.yaml`（結構 + 第 1 題 bug_fix Tier-2，作為唯一完整範本）**

```yaml
# 任務套件註冊表。每題：id / category / tier / source / repo_baseline /
# setup_patch（可選，把 baseline 變成初始狀態）/ prompt / grader / provenance
# grader.type=pytest：把 hidden_tests 複製進 workdir 後跑 pytest，全綠才 success。
tasks:
  - id: bugfix-t2-01
    category: bug_fix
    tier: 2
    source: controlled
    repo_baseline: tasks/target_repo
    setup_patch: tasks/baselines/bugfix-t2-01.patch
    prompt: |
      calckit/money.py 的 parse_amount 對帶括號的負數金額（例如 "($1,234.50)"，
      會計表示法代表 -1234.50）解析錯誤。請修正 parse_amount，使其正確回傳負值，
      且不破壞既有正數解析。只改 calckit/ 下的程式，用你的工具編輯檔案。
    grader:
      type: pytest
      hidden_tests: tasks/graders/bugfix-t2-01_test.py
    provenance: "controlled, DeepSWE-style behavior verifier, authored 2026-06-04"
```

- [ ] **Step 4: 建第 1 題的 setup_patch 與隱藏測試**

Create `tasks/baselines/bugfix-t2-01.patch`（在 baseline 上植入「不支援括號負數」的初始狀態——此處 baseline 本就不支援，故 patch 為空操作的標記檔；以註解說明初始狀態即 baseline）:
```diff
# bugfix-t2-01 的初始狀態即 target_repo baseline（parse_amount 尚不支援括號負數）。
# 無需改動 baseline；此檔存在表示「不套用額外 patch」。runner 遇到僅含註解/空 diff 時跳過套用。
```

Create `tasks/graders/bugfix-t2-01_test.py`（隱藏；驗證修好且不回歸）:
```python
from calckit import parse_amount


def test_parenthesized_negative():
    assert parse_amount("($1,234.50)") == -1234.50


def test_plain_negative_sign_still_works():
    assert parse_amount("-$50.00") == -50.00


def test_positive_unchanged():
    assert parse_amount("$1,234.50") == 1234.50
```

- [ ] **Step 5: 寫失敗測試 `tests/test_provision.py`**

```python
from pathlib import Path
import yaml
from runner.provision import load_tasks, provision_task


def test_registry_loads():
    tasks = load_tasks()
    assert any(t["id"] == "bugfix-t2-01" for t in tasks)


def test_provision_creates_clean_workdir_without_hidden_tests(tmp_path):
    tasks = {t["id"]: t for t in load_tasks()}
    wd = provision_task(tasks["bugfix-t2-01"], tmp_path / "wd")
    assert (wd / "calckit" / "money.py").exists()
    # 隱藏測試絕不可出現在 agent workdir
    assert not (wd / "graders").exists()
    assert not any(p.name == "bugfix-t2-01_test.py" for p in wd.rglob("*.py"))


def test_baseline_fails_hidden_test_before_fix(tmp_path):
    """難度校準前置：未修狀態下隱藏測試必須 fail（D3）。"""
    import subprocess, shutil
    from runner import paths
    tasks = {t["id"]: t for t in load_tasks()}
    wd = provision_task(tasks["bugfix-t2-01"], tmp_path / "wd")
    shutil.copy(paths.REPO / "tasks/graders/bugfix-t2-01_test.py", wd / "hidden_test.py")
    py = str(paths.RUNNER_VENV / "bin" / "python")
    subprocess.run([py, "-m", "pip", "install", "-q", "-e", "."], cwd=wd, check=True)
    r = subprocess.run([py, "-m", "pytest", "hidden_test.py", "-q"], cwd=wd, capture_output=True, text=True)
    assert r.returncode != 0, "baseline 應未通過隱藏測試（否則任務無區辨力）"
```

- [ ] **Step 6: 跑測試確認失敗**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_provision.py -v`
Expected: FAIL（`ModuleNotFoundError: runner.provision`）。

- [ ] **Step 7: 寫 `runner/provision.py`**

```python
"""每題開乾淨 workdir：複製 baseline、套用 setup_patch（若非空）。隱藏測試一律排除。"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
import yaml
from runner import paths

REGISTRY = paths.REPO / "tasks" / "registry.yaml"


def load_tasks() -> list[dict]:
    data = yaml.safe_load(REGISTRY.read_text())
    return data["tasks"]


def _patch_is_effective(patch_path: Path) -> bool:
    """僅含註解/空白的 patch 視為 no-op。"""
    for line in patch_path.read_text().splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return True
    return False


def provision_task(task: dict, dest: Path) -> Path:
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    baseline = paths.REPO / task["repo_baseline"]
    shutil.copytree(baseline, dest)
    # 安全網：絕不把 graders/ 帶進 workdir
    for g in dest.rglob("*_test.py"):
        if "graders" in g.parts:
            g.unlink()
    sp = task.get("setup_patch")
    if sp:
        patch_path = paths.REPO / sp
        if patch_path.exists() and _patch_is_effective(patch_path):
            subprocess.run(["git", "apply", str(patch_path)], cwd=dest, check=True)
    return dest
```

- [ ] **Step 8: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_provision.py -v`
Expected: 3 passed（含 baseline-fails 校準）。

- [ ] **Step 9: Commit**

```bash
git add tasks/ runner/provision.py tests/test_provision.py
git commit -m "feat(tasks): controlled target repo + registry + provision (hidden-test isolation)


```

---

## Task 5: 統一 Grader（隱藏 pytest → pass/fail）

**Files:**
- Create: `runner/grader.py`
- Test: `tests/test_grader.py`

- [ ] **Step 1: 寫失敗測試 `tests/test_grader.py`**

```python
import shutil
from pathlib import Path
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
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_grader.py -v`
Expected: FAIL（`ModuleNotFoundError: runner.grader`）。

- [ ] **Step 3: 寫 `runner/grader.py`**

```python
"""統一 grader：把隱藏測試複製進 workdir 後跑 pytest，全綠才 success。"""
from __future__ import annotations
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from runner import paths


@dataclass
class GradeResult:
    success: bool
    detail: str  # pytest summary 尾段（sanitized：不含 secrets）


def run_grader(task: dict, workdir: Path, timeout_s: int = 300) -> GradeResult:
    workdir = Path(workdir)
    g = task["grader"]
    if g["type"] != "pytest":
        raise ValueError(f"unsupported grader type: {g['type']}")
    hidden_src = paths.REPO / g["hidden_tests"]
    hidden_dst = workdir / "_hidden_grader_test.py"
    shutil.copy(hidden_src, hidden_dst)
    py = str(paths.RUNNER_VENV / "bin" / "python")
    # 確保 target package 可 import（editable install；Tier-1 instance 自帶安裝方式見其 registry）
    install = task.get("grader", {}).get("install", "-e .")
    if install:
        subprocess.run([py, "-m", "pip", "install", "-q", *install.split()],
                       cwd=workdir, capture_output=True, text=True)
    try:
        r = subprocess.run([py, "-m", "pytest", "_hidden_grader_test.py", "-q"],
                           cwd=workdir, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return GradeResult(False, f"grader timeout after {timeout_s}s")
    finally:
        hidden_dst.unlink(missing_ok=True)
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-8:])
    return GradeResult(r.returncode == 0, tail)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_grader.py -v`
Expected: 2 passed。

- [ ] **Step 5: Commit**

```bash
git add runner/grader.py tests/test_grader.py
git commit -m "feat(runner): unified hidden-pytest grader with baseline/reference calibration


```

---

## Task 6: 任務套件 — rename 類 ×4（Tier-2）

**Files:**
- Modify: `tasks/registry.yaml`（追加 4 題）
- Create: `tasks/graders/rename-t2-0{1..4}_test.py`、`tasks/baselines/rename-t2-0{1..4}.patch`（如需初始狀態改動）

每題契約（與 Task 4/5 同模板）：固定 baseline 狀態、明確 prompt（要 agent 把某符號改名並更新所有引用）、隱藏測試斷言「新名稱可用、舊名稱已不存在、行為不變」。每題都必須通過 D3 校準（baseline fail、reference pass）。

- [ ] **Step 1: 完整範本題 `rename-t2-01`（其餘 3 題照此格式，prompt 與隱藏測試各自具體列出）**

registry.yaml 追加:
```yaml
  - id: rename-t2-01
    category: rename
    tier: 2
    source: controlled
    repo_baseline: tasks/target_repo
    setup_patch: tasks/baselines/rename-t2-01.patch
    prompt: |
      請把 calckit/stats.py 內的函式 mean 更名為 average，並更新套件內所有引用
      （__init__.py 的 export、其他模組、tests/test_basic.py），使外部以
      `from calckit import average` 可用，且 calckit 不再匯出 mean。行為需完全不變。
    grader:
      type: pytest
      hidden_tests: tasks/graders/rename-t2-01_test.py
    provenance: "controlled, authored 2026-06-04"
```

`tasks/baselines/rename-t2-01.patch`：no-op 標記（初始狀態即 baseline，函式名為 `mean`）:
```diff
# rename-t2-01 初始狀態即 baseline（calckit 匯出 mean）。無額外 patch。
```

`tasks/graders/rename-t2-01_test.py`（隱藏）:
```python
import importlib
import pytest
import calckit


def test_average_available():
    importlib.reload(calckit)
    assert calckit.average([1, 2, 3]) == 2


def test_mean_removed():
    importlib.reload(calckit)
    assert not hasattr(calckit, "mean"), "舊名 mean 應已不存在"


def test_behavior_unchanged():
    importlib.reload(calckit)
    assert calckit.average([10, 20]) == 15
```

- [ ] **Step 2: 其餘 3 題（各自具體 prompt + 隱藏測試斷言；非「同前」）**

依下表逐題建 registry 條目（格式同 Step 1）、no-op 或具體 `setup_patch`、隱藏測試檔。每題的隱藏測試需明確斷言新名可用、舊名移除、行為不變：

| id | 改名標的 | 新名 | 隱藏測試重點 |
|----|---------|------|-------------|
| rename-t2-02 | `median` (stats.py) | `mid_value` | `mid_value([3,1,2])==2`、`not hasattr(calckit,'median')`、偶數長度行為不變 |
| rename-t2-03 | `parse_amount` (money.py) | `to_float` | `to_float("$1,234.50")==1234.5`、舊名移除、`format_amount` 仍可用 |
| rename-t2-04 | `format_amount` (money.py) | `to_string` | `to_string(1234.5)=="$1,234.50"`、舊名移除 |

- [ ] **Step 3: 逐題校準（D3）—— baseline fail、reference pass**

Run（對每個 rename-t2-0N）:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && /data/harness-lab/runner-venv/bin/python -m pytest tests/test_calibration.py -q'
```
（`tests/test_calibration.py` 於本步建立：對 registry 中所有 `tier:2` 任務，斷言「baseline 套用後跑隱藏測試為 fail」。reference-pass 不在自動測試內逐題寫，而是於本步以人工套用一次參考改名驗證一次即可，記錄於 commit message。）

`tests/test_calibration.py`:
```python
import shutil, subprocess
import pytest
from runner.provision import load_tasks, provision_task
from runner.grader import run_grader

TIER2 = [t for t in load_tasks() if t["tier"] == 2]


@pytest.mark.parametrize("task", TIER2, ids=[t["id"] for t in TIER2])
def test_baseline_fails(task, tmp_path):
    wd = provision_task(task, tmp_path / task["id"])
    assert run_grader(task, wd).success is False, f"{task['id']} baseline 未 fail，無區辨力"
```

Expected: 全部 parametrized case passed（代表每題 baseline 確實 fail）。

- [ ] **Step 4: Commit**

```bash
git add tasks/registry.yaml tasks/graders/rename-* tasks/baselines/rename-* tests/test_calibration.py
git commit -m "feat(tasks): rename category x4 (Tier-2) + baseline-fails calibration


```

---

## Task 7: 任務套件 — add_tests 類 ×4（Tier-2）

**Files:** Modify `tasks/registry.yaml`；Create `tasks/graders/addtests-t2-0{1..4}_test.py`、`tasks/baselines/addtests-t2-0{1..4}.patch`

設計要點：此類要 agent「為既有但未被測到的行為補測試」。隱藏 grader 不是檢查 agent 寫的測試內容，而是**驗證 agent 產生的測試檔存在且能跑、且覆蓋指定行為**——做法：隱藏測試以 `subprocess` 跑 agent 在指定路徑新增的測試檔並要求通過，同時 import 被測函式直接驗證 agent「沒有把測試寫成空殼」。

- [ ] **Step 1: 完整範本題 `addtests-t2-01`**

registry.yaml 追加:
```yaml
  - id: addtests-t2-01
    category: add_tests
    tier: 2
    source: controlled
    repo_baseline: tasks/target_repo
    setup_patch: tasks/baselines/addtests-t2-01.patch
    prompt: |
      calckit/money.py 的 parse_amount 目前沒有針對「含千分位逗號與小數」的測試。
      請在 tests/test_money_extra.py 新增 pytest 測試，至少涵蓋：
      parse_amount("$1,234.50")==1234.50 與 parse_amount("$0.05")==0.05。
      用你的工具建立檔案。
    grader:
      type: pytest
      hidden_tests: tasks/graders/addtests-t2-01_test.py
    provenance: "controlled, authored 2026-06-04"
```

`tasks/baselines/addtests-t2-01.patch`：no-op 標記。

`tasks/graders/addtests-t2-01_test.py`（隱藏；驗證 agent 真的補了能跑且有意義的測試）:
```python
import subprocess, sys
from pathlib import Path


def test_agent_test_file_exists():
    assert Path("tests/test_money_extra.py").exists(), "agent 應建立 tests/test_money_extra.py"


def test_agent_tests_pass_and_are_nonempty():
    p = Path("tests/test_money_extra.py")
    body = p.read_text()
    assert "parse_amount" in body, "新增測試應實際呼叫 parse_amount"
    assert "1,234.50" in body or "1234.50" in body
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_money_extra.py", "-q"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 2: 其餘 3 題（具體 prompt + 隱藏斷言）**

| id | 要求補測之行為 | 隱藏測試重點 |
|----|---------------|-------------|
| addtests-t2-02 | `format_amount` 的負數與零 | 存在 `tests/test_format_extra.py`、實呼叫 `format_amount`、跑綠 |
| addtests-t2-03 | `median` 偶數長度取中位平均 | 存在指定檔、含 `median(`、跑綠 |
| addtests-t2-04 | `mean` 空序列 raise ValueError | agent 測試以 `pytest.raises(ValueError)` 斷言、跑綠 |

- [ ] **Step 3: 校準** — `tests/test_calibration.py` 已 parametrize 全 Tier-2；跑一次確認新增 4 題的 baseline 皆 fail（baseline 無這些測試檔，隱藏 grader 應 fail）。

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_calibration.py -q`
Expected: 全綠。

- [ ] **Step 4: Commit**

```bash
git add tasks/registry.yaml tasks/graders/addtests-* tasks/baselines/addtests-*
git commit -m "feat(tasks): add_tests category x4 (Tier-2)


```

---

## Task 8: 任務套件 — add_logging 類 ×4（Tier-2）

**Files:** Modify `tasks/registry.yaml`；Create `tasks/graders/addlog-t2-0{1..4}_test.py`、`tasks/baselines/addlog-t2-0{1..4}.patch`

設計要點：要 agent 在指定函式加入標準 `logging`（不可改變回傳值）。隱藏 grader 用 `caplog`/`logging` 擷取，斷言「呼叫後有預期 log 記錄且原行為不變」。

- [ ] **Step 1: 完整範本題 `addlog-t2-01`**

registry.yaml 追加:
```yaml
  - id: addlog-t2-01
    category: add_logging
    tier: 2
    source: controlled
    repo_baseline: tasks/target_repo
    setup_patch: tasks/baselines/addlog-t2-01.patch
    prompt: |
      請在 calckit/money.py 的 parse_amount 內加入 logging：使用標準 logging 模組，
      於函式開頭以 logger.debug 記錄收到的原始字串（含 "parse_amount" 字樣）。
      不可改變回傳值與既有行為。logger 名稱用模組名（logging.getLogger(__name__)）。
    grader:
      type: pytest
      hidden_tests: tasks/graders/addlog-t2-01_test.py
    provenance: "controlled, authored 2026-06-04"
```

`tasks/baselines/addlog-t2-01.patch`：no-op 標記。

`tasks/graders/addlog-t2-01_test.py`（隱藏）:
```python
import logging
from calckit import parse_amount


def test_logs_on_parse(caplog):
    with caplog.at_level(logging.DEBUG):
        result = parse_amount("$1,234.50")
    assert result == 1234.50, "行為不可改變"
    assert any("parse_amount" in rec.getMessage() for rec in caplog.records), "應有含 parse_amount 的 log"


def test_no_print_used():
    # logging 而非 print：間接檢查模組原始碼引用了 logging
    import calckit.money as m, inspect
    assert "logging" in inspect.getsource(m)
```

- [ ] **Step 2: 其餘 3 題**

| id | 加 log 標的 | 隱藏測試重點 |
|----|------------|-------------|
| addlog-t2-02 | `format_amount` | caplog 有含 "format_amount" 的記錄、回傳不變、源碼用 logging |
| addlog-t2-03 | `mean` | 記錄輸入長度（含 "mean"）、回傳不變 |
| addlog-t2-04 | `median` | 記錄（含 "median"）、回傳不變 |

- [ ] **Step 3: 校準** — 跑 `tests/test_calibration.py`，確認新增 4 題 baseline 皆 fail（baseline 無 logging）。

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_calibration.py -q`
Expected: 全綠。

- [ ] **Step 4: Commit**

```bash
git add tasks/registry.yaml tasks/graders/addlog-* tasks/baselines/addlog-*
git commit -m "feat(tasks): add_logging category x4 (Tier-2)


```

---

## Task 9: 任務套件 — benchmark 類定案 + bug_fix 補到 4（實作修訂）

**2026-06-04 實作結果：** 原 SWE-bench Verified Tier-1 計畫已 superseded。aarch64 上不上官方 docker harness 會遇到依賴漂移與 oracle 不穩，且 SWE-bench 的 patch-correctness 目標與本研究的 tool-sequence divergence 依變項錯位。

**最終任務分布：** total 20；五類各 4：`bug_fix`、`rename`、`add_tests`、`add_logging`、`benchmark`。

**benchmark 類：** 改採 Aider-polyglot benchmark 的 Python/Exercism 4 題：`bench-grade-school`、`bench-phone-number`、`bench-pig-latin`、`bench-bottle-song`。provenance 寫於 `tasks/benchmark/PROVENANCE.md`，baseline 與 hidden pytest grader 皆在 repo 內可重現。

**bug_fix 類：** 使用受控 Tier-2 `bugfix-t2-01..04`：

| id | 植入 bug | hidden grader 重點 |
|----|----------|--------------------|
| `bugfix-t2-01` | `parse_amount` 不支援括號負數金額 | 會計括號負數解析為負值，正數不破壞 |
| `bugfix-t2-02` | `median` 偶數長度回傳較大中間值 | 偶數取兩中間值平均，奇數不破壞 |
| `bugfix-t2-03` | `format_amount` 對負數遺失負號 | 負數保留負號，正數不破壞 |
| `bugfix-t2-04` | `mean` 使用整數除法 | 小數平均值正確，空序列仍 raise `ValueError` |

**驗證命令：**

```bash
cd /data/repos/xai-harness-faithfulness
/data/harness-lab/runner-venv/bin/python -c "from runner.provision import load_tasks; from collections import Counter; ts=load_tasks(); print(len(ts), dict(Counter(t['category'] for t in ts)))"
/data/harness-lab/runner-venv/bin/python -m pytest tests/test_calibration.py -q
```

Expected: `20 {'bug_fix': 4, 'rename': 4, 'add_tests': 4, 'add_logging': 4, 'benchmark': 4}`；baseline-fail calibration 20 題全綠。

---

## Task 10: Adapter base + Claude Code 介面卡

**Files:**
- Create: `runner/adapters/__init__.py`、`runner/adapters/base.py`、`runner/adapters/claude_code.py`
- Create: `tests/fixtures/`（複製 smoke trace 樣本作 fixture）
- Test: `tests/test_adapter_claude_code.py`

- [ ] **Step 1: 把現有 smoke trace 複製成 sanitized fixtures（不花 API token）**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && mkdir -p tests/fixtures && \
cp "$(ls -t /data/harness-lab/smoke/cc/.claude-trace/*.jsonl | head -1)" tests/fixtures/cc.smoke.jsonl && \
cp /data/harness-lab/smoke/codex/codex.log tests/fixtures/codex.smoke.log && \
cp /data/harness-lab/smoke/opencode-haiku/oc.log tests/fixtures/opencode-haiku.smoke.log && \
cp /data/harness-lab/smoke/opencode-gptmini/oc.log tests/fixtures/opencode-gptmini.smoke.log && \
cp /data/harness-lab/smoke/hermes-haiku/trace.session.json tests/fixtures/hermes-haiku.smoke.json && \
cp /data/harness-lab/smoke/hermes-gptmini/trace.session.json tests/fixtures/hermes-gptmini.smoke.json && \
ls -la tests/fixtures/'
```
Expected: 列出 6 個 fixture 檔。

> **重要（sanitization）：** fixture 為真實 API 流量，可能含 request metadata。提交前**逐檔人工檢視**確認無 `sk-`/`api_key`/`authorization`/`bearer` 等。若有，於本步以遮罩（把值換成 `<redacted>`）後再提交；adapter 解析的是結構（tool 名、budget、system 是否存在），不依賴 secret 值。

Run（敏感字掃描）:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && grep -riE "sk-[a-z0-9]|api[_-]?key|authorization|bearer" tests/fixtures/ | head'
```
Expected: 無輸出（或將命中的值遮罩後再次確認無輸出）。

- [ ] **Step 2: 寫 `runner/adapters/base.py`**

```python
"""harness 介面卡抽象：封裝啟動指令、環境、trace 來源、正規化。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from runner import paths


class HarnessAdapter(ABC):
    name: str          # 對應 NormalizedTrace.harness
    version: str       # 釘死版本（記入 trace）

    @abstractmethod
    def env(self, secrets: dict, model_snapshot: str) -> dict:
        """回傳此次 run 的環境變數（含隔離 HOME、API key、budget）。"""

    @abstractmethod
    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        """回傳非互動啟動指令（argv）。"""

    @abstractmethod
    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        """run 結束後，回傳原始 trace 檔案路徑（供存檔與 normalize）。"""

    @abstractmethod
    def normalize(self, workdir: Path) -> dict:
        """解析原始 trace → 部分 NormalizedTrace 欄位：
        {tool_calls, reasoning_steps, decision_points, tokens, turns,
         runtime_budget, system_present(bool), evidence_levels}。"""
```

- [ ] **Step 2b: 寫 `runner/adapters/__init__.py`（registry，於各 adapter 完成後補齊）**

```python
from runner.adapters.claude_code import ClaudeCodeAdapter

ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    # codex / opencode / hermes 於 Task 11-13 加入
}


def get_adapter(harness: str):
    return ADAPTERS[harness]()
```

- [ ] **Step 3: 寫失敗測試 `tests/test_adapter_claude_code.py`（用 fixture）**

```python
from pathlib import Path
from runner.adapters.claude_code import ClaudeCodeAdapter

FIX = Path(__file__).parent / "fixtures" / "cc.smoke.jsonl"


def test_command_shape():
    a = ClaudeCodeAdapter()
    cmd = a.command("FIX BUG", "claude-haiku-4-5-20251001", "anthropic")
    assert cmd[0].endswith("claude-trace")
    assert "--model" in cmd and "claude-haiku-4-5-20251001" in cmd
    assert "--effort" in cmd


def test_env_sets_budgets():
    a = ClaudeCodeAdapter()
    env = a.env({"ANTHROPIC_API_KEY": "x"}, "claude-haiku-4-5-20251001")
    assert env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "64000"
    assert env["MAX_THINKING_TOKENS"] == "63999"
    assert env["HOME"].endswith("/home")


def test_normalize_extracts_tool_sequence_from_fixture(tmp_path):
    # 把 fixture 擺成 adapter 預期的 .claude-trace 結構
    td = tmp_path / ".claude-trace"
    td.mkdir()
    (td / "log.jsonl").write_text(FIX.read_text())
    out = ClaudeCodeAdapter().normalize(tmp_path)
    names = [tc["tool_name"] for tc in out["tool_calls"]]
    assert names, "應從 trace 解析出至少一個 tool_use"
    assert out["runtime_budget"]["max_output_tokens"] == 64000
    assert out["system_present"] is True
```

- [ ] **Step 4: 跑測試確認失敗**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_adapter_claude_code.py -v`
Expected: FAIL。

- [ ] **Step 5: 寫 `runner/adapters/claude_code.py`**

```python
"""Claude Code 2.1.88 介面卡：經 claude-trace 攔截 API 流量。
trace 格式：.claude-trace/*.jsonl，每行一筆 {request:{model,max_tokens,thinking,system,tools,messages},
response:{...}}（claude-trace 1.0.4 已二次解析 SSE）。tool 序列＝assistant 回應中的 tool_use blocks。"""
from __future__ import annotations
import json
from pathlib import Path
from runner import paths
from runner.adapters.base import HarnessAdapter


class ClaudeCodeAdapter(HarnessAdapter):
    name = "claude_code"
    version = "2.1.88"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        return {
            "HOME": str(paths.LAB_HOME),
            "PATH": f"{paths.LAB_BIN}:" + __import__("os").environ.get("PATH", ""),
            "ANTHROPIC_API_KEY": secrets["ANTHROPIC_API_KEY"],
            "CLAUDE_CODE_EFFORT_LEVEL": "high",
            "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000",
            "MAX_THINKING_TOKENS": "63999",
        }

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [
            str(paths.LAB_BIN / "claude-trace"), "--include-all-requests", "--run-with",
            "-p", prompt, "--model", model_snapshot,
            "--effort", "high", "--permission-mode", "acceptEdits",
        ]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        td = workdir / ".claude-trace"
        jsonls = sorted(td.glob("*.jsonl")) if td.exists() else []
        return {"trace_jsonl": jsonls[-1]} if jsonls else {}

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls, reasoning_steps = [], []
        max_tokens = thinking_budget = None
        system_present = False
        out_tokens = in_tokens = cached_in = None
        turns = 0
        step = 0
        if "trace_jsonl" in arts:
            for line in arts["trace_jsonl"].read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                req = rec.get("request") or {}
                if req:
                    turns += 1
                    max_tokens = max_tokens or req.get("max_tokens")
                    th = req.get("thinking") or {}
                    thinking_budget = thinking_budget or th.get("budget_tokens")
                    if req.get("system"):
                        system_present = True
                resp = rec.get("response") or {}
                usage = resp.get("usage") or {}
                if usage:
                    in_tokens = usage.get("input_tokens", in_tokens)
                    out_tokens = usage.get("output_tokens", out_tokens)
                    cached_in = usage.get("cache_read_input_tokens", cached_in)
                for block in (resp.get("content") or []):
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            step += 1
                            tool_calls.append({
                                "step": step, "tool_name": block.get("name", "?"),
                                "args_summary": _summarize(block.get("input")), "ts": None,
                            })
                        elif block.get("type") == "thinking":
                            reasoning_steps.append({"type": "thinking", "present": True})
        return {
            "tool_calls": tool_calls,
            "reasoning_steps": reasoning_steps,
            "decision_points": [],
            "tokens": {"input": in_tokens, "cached_input": cached_in, "output": out_tokens},
            "turns": turns,
            "runtime_budget": {
                "max_output_tokens": max_tokens, "thinking_budget_tokens": thinking_budget,
                "context_window_tokens": 200000, "effort_source": "cli --effort high + env budgets",
            },
            "system_present": system_present,
            "evidence_levels": {"tool_calls": "direct", "system_present": "direct",
                                "reasoning_steps": "direct", "tokens": "direct"},
        }


def _summarize(inp) -> str:
    if not isinstance(inp, dict):
        return ""
    for k in ("file_path", "path", "command", "pattern"):
        if k in inp:
            return f"{k}={str(inp[k])[:80]}"
    return ",".join(list(inp.keys())[:4])
```

- [ ] **Step 6: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_adapter_claude_code.py -v`
Expected: 3 passed。若 fixture 的實際 JSON 欄位名與假設不同（例如 `response.content` 巢狀於別處），於本步依 fixture 真實結構就地修正解析路徑後再驗證。

- [ ] **Step 7: Commit**

```bash
git add runner/adapters/__init__.py runner/adapters/base.py runner/adapters/claude_code.py tests/fixtures/ tests/test_adapter_claude_code.py
git commit -m "feat(adapters): base interface + Claude Code adapter (claude-trace jsonl normalizer)


```

---

## Task 11: Codex CLI 介面卡

**Files:** Create `runner/adapters/codex.py`；Modify `runner/adapters/__init__.py`；Test `tests/test_adapter_codex.py`

trace 來源：`codex.log`（stdout JSONL：`{"type":"command_execution"...}`、`{"type":"file_change"...}`）＋ session `rollout-*.jsonl`（base_instructions、items、tool calls `exec_command`/`apply_patch`、reasoning、effort）。model/effort 來自 `$LAB_HOME/.codex/config.toml`。

- [ ] **Step 1: 寫失敗測試 `tests/test_adapter_codex.py`**

```python
from pathlib import Path
from runner.adapters.codex import CodexAdapter

FIX = Path(__file__).parent / "fixtures" / "codex.smoke.log"


def test_command_shape():
    cmd = CodexAdapter().command("FIX", "gpt-5.4-mini-2026-03-17", "openai")
    assert cmd[0].endswith("codex")
    assert "exec" in cmd and "--json" in cmd


def test_env_sets_isolated_home_and_key():
    env = CodexAdapter().env({"OPENAI_API_KEY": "x"}, "gpt-5.4-mini-2026-03-17")
    assert env["HOME"].endswith("/home")
    assert env["OPENAI_API_KEY"] == "x"


def test_normalize_reads_command_and_file_change_events(tmp_path):
    (tmp_path / "codex.log").write_text(FIX.read_text())
    out = CodexAdapter().normalize(tmp_path)
    names = [tc["tool_name"] for tc in out["tool_calls"]]
    assert any(n in ("exec_command", "command_execution", "apply_patch", "file_change") for n in names)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_adapter_codex.py -v`
Expected: FAIL。

- [ ] **Step 3: 寫 `runner/adapters/codex.py`**

```python
"""Codex CLI 0.136.0 介面卡。tool 序列由 codex.log 的 command_execution/file_change 事件構成；
session rollout-*.jsonl（$LAB_HOME/.codex/sessions 下）含 base_instructions/reasoning，作補充。"""
from __future__ import annotations
import json
from pathlib import Path
from runner import paths
from runner.adapters.base import HarnessAdapter

_TOOL_EVENTS = {"command_execution": "exec_command", "file_change": "apply_patch"}


class CodexAdapter(HarnessAdapter):
    name = "codex"
    version = "0.136.0"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        return {"HOME": str(paths.LAB_HOME), "OPENAI_API_KEY": secrets["OPENAI_API_KEY"]}

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [str(paths.LAB_BIN / "codex"), "exec", "--skip-git-repo-check",
                "--dangerously-bypass-approvals-and-sandbox", "--json", prompt]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        arts = {}
        if (workdir / "codex.log").exists():
            arts["codex_log"] = workdir / "codex.log"
        sess_dir = paths.LAB_HOME / ".codex" / "sessions"
        rolls = sorted(sess_dir.rglob("rollout-*.jsonl")) if sess_dir.exists() else []
        if rolls:
            arts["rollout"] = rolls[-1]
        return arts

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls, reasoning_steps = [], []
        step = 0
        system_present = False
        if "codex_log" in arts:
            for line in arts["codex_log"].read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = rec.get("type")
                if t in _TOOL_EVENTS:
                    step += 1
                    tool_calls.append({"step": step, "tool_name": _TOOL_EVENTS[t],
                                       "args_summary": _summ(rec), "ts": rec.get("ts")})
        if "rollout" in arts:
            for line in arts["rollout"].read_text().splitlines():
                if '"base_instructions"' in line or '"developer"' in line:
                    system_present = True
                if '"reasoning"' in line:
                    reasoning_steps.append({"type": "reasoning", "present": True})
        return {
            "tool_calls": tool_calls, "reasoning_steps": reasoning_steps, "decision_points": [],
            "tokens": {"input": None, "cached_input": None, "output": None},
            "turns": len(tool_calls),
            "runtime_budget": {"max_output_tokens": None, "thinking_budget_tokens": None,
                               "context_window_tokens": None,
                               "effort_source": "$LAB_HOME/.codex/config.toml (model_reasoning_effort=high)"},
            "system_present": system_present,
            "evidence_levels": {"tool_calls": "direct", "system_present": "direct",
                                "reasoning_steps": "inferred", "tokens": "unknown"},
        }


def _summ(rec) -> str:
    for k in ("command", "path", "changes", "cmd"):
        if k in rec:
            return f"{k}={str(rec[k])[:80]}"
    return rec.get("type", "")
```

- [ ] **Step 4: 把 Codex 加入 registry**

Modify `runner/adapters/__init__.py`：import `CodexAdapter`、`ADAPTERS["codex"] = CodexAdapter`。

- [ ] **Step 5: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_adapter_codex.py -v`
Expected: 3 passed。依 fixture 真實欄位名就地校正。

- [ ] **Step 6: Commit**

```bash
git add runner/adapters/codex.py runner/adapters/__init__.py tests/test_adapter_codex.py
git commit -m "feat(adapters): Codex CLI adapter (codex.log + rollout normalizer)


```

---

## Task 12: OpenCode 介面卡

**Files:** Create `runner/adapters/opencode.py`；Modify `runner/adapters/__init__.py`；Test `tests/test_adapter_opencode.py`

trace 來源：`oc.log`（`opencode run --format json` 的事件流 JSONL，含 `{"type":"tool_use",...}`，tool 名如 `read`/`edit`/`glob`/`apply_patch`）。模型注入：`--model anthropic/<haiku>` 或 `openai/<gptmini>`，effort 用 `--variant high`。

- [ ] **Step 1: 寫失敗測試 `tests/test_adapter_opencode.py`**

```python
from pathlib import Path
from runner.adapters.opencode import OpenCodeAdapter

FIX_H = Path(__file__).parent / "fixtures" / "opencode-haiku.smoke.log"
FIX_G = Path(__file__).parent / "fixtures" / "opencode-gptmini.smoke.log"


def test_command_routes_model_with_provider_prefix():
    cmd = OpenCodeAdapter().command("FIX", "claude-haiku-4-5-20251001", "anthropic")
    assert "run" in cmd and "--variant" in cmd and "high" in cmd
    assert "anthropic/claude-haiku-4-5-20251001" in cmd
    cmd2 = OpenCodeAdapter().command("FIX", "gpt-5.4-mini-2026-03-17", "openai")
    assert "openai/gpt-5.4-mini-2026-03-17" in cmd2


def test_normalize_haiku_tool_path(tmp_path):
    (tmp_path / "oc.log").write_text(FIX_H.read_text())
    out = OpenCodeAdapter().normalize(tmp_path)
    names = [tc["tool_name"] for tc in out["tool_calls"]]
    assert "read" in names or "edit" in names


def test_normalize_gptmini_tool_path(tmp_path):
    (tmp_path / "oc.log").write_text(FIX_G.read_text())
    out = OpenCodeAdapter().normalize(tmp_path)
    assert len(out["tool_calls"]) >= 1
```

- [ ] **Step 2: 跑測試確認失敗** — Run: `... pytest tests/test_adapter_opencode.py -v` → FAIL。

- [ ] **Step 3: 寫 `runner/adapters/opencode.py`**

```python
"""OpenCode 1.15.13 介面卡。trace=oc.log（--format json 事件流）。
注意 dossier M1：OpenCode 的 full system prompt 未由 export 完整暴露 → system 可見度標 partial。"""
from __future__ import annotations
import json
from pathlib import Path
from runner import paths
from runner.adapters.base import HarnessAdapter


class OpenCodeAdapter(HarnessAdapter):
    name = "opencode"
    version = "1.15.13"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        return {"HOME": str(paths.LAB_HOME),
                "ANTHROPIC_API_KEY": secrets.get("ANTHROPIC_API_KEY", ""),
                "OPENAI_API_KEY": secrets.get("OPENAI_API_KEY", "")}

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [str(paths.LAB_BIN / "opencode"), "run",
                "--model", f"{provider}/{model_snapshot}",
                "--variant", "high", "--format", "json", prompt]

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        return {"oc_log": workdir / "oc.log"} if (workdir / "oc.log").exists() else {}

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls = []
        step = 0
        if "oc_log" in arts:
            for line in arts["oc_log"].read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") == "tool_use":
                    step += 1
                    tool_calls.append({"step": step,
                                       "tool_name": rec.get("tool") or rec.get("name") or "?",
                                       "args_summary": _summ(rec), "ts": rec.get("ts")})
        return {
            "tool_calls": tool_calls, "reasoning_steps": [], "decision_points": [],
            "tokens": {"input": None, "cached_input": None, "output": None},
            "turns": len(tool_calls),
            "runtime_budget": {"max_output_tokens": None, "thinking_budget_tokens": None,
                               "context_window_tokens": None, "effort_source": "cli --variant high"},
            "system_present": None,  # partial：export 不完整暴露 system prompt（dossier M1）
            "evidence_levels": {"tool_calls": "direct", "system_present": "partial",
                                "reasoning_steps": "unknown", "tokens": "unknown"},
        }


def _summ(rec) -> str:
    args = rec.get("args") or rec.get("input") or {}
    if isinstance(args, dict):
        for k in ("filePath", "file_path", "path", "pattern", "command"):
            if k in args:
                return f"{k}={str(args[k])[:80]}"
    return rec.get("tool") or ""
```

- [ ] **Step 4: 加入 registry**（`ADAPTERS["opencode"] = OpenCodeAdapter`）。

- [ ] **Step 5: 跑測試確認通過** — Run: `... pytest tests/test_adapter_opencode.py -v` → 3 passed。依 fixture 真實欄位名校正 tool 名取值路徑。

- [ ] **Step 6: Commit**

```bash
git add runner/adapters/opencode.py runner/adapters/__init__.py tests/test_adapter_opencode.py
git commit -m "feat(adapters): OpenCode adapter (oc.log event normalizer, system=partial)


```

---

## Task 13: Hermes 介面卡

**Files:** Create `runner/adapters/hermes.py`；Modify `runner/adapters/__init__.py`；Test `tests/test_adapter_hermes.py`

trace 來源：run 結束後取 `$HERMES_HOME/sessions/session_*.json` 最新一個（含 top-level `system_prompt`、18 個 tools 定義、有序 `tool_calls`，如 `read_file`/`patch`）。二進位在真實 HOME `~/.local/bin/hermes`；config/state 以 `HERMES_HOME=$LAB_HOME/.hermes` 隔離。模型用分開形式 `-m <model> --provider <provider>`（合併式對 snapshot id 會靜默失敗）。

- [ ] **Step 1: 寫失敗測試 `tests/test_adapter_hermes.py`**

```python
from pathlib import Path
from runner.adapters.hermes import HermesAdapter

FIX_H = Path(__file__).parent / "fixtures" / "hermes-haiku.smoke.json"
FIX_G = Path(__file__).parent / "fixtures" / "hermes-gptmini.smoke.json"


def test_command_uses_separate_model_provider():
    cmd = HermesAdapter().command("FIX", "claude-haiku-4-5-20251001", "anthropic")
    assert "-z" in cmd and "--yolo" in cmd
    assert "-m" in cmd and "claude-haiku-4-5-20251001" in cmd
    assert "--provider" in cmd and "anthropic" in cmd


def test_normalize_reads_session_json(tmp_path):
    (tmp_path / "trace.session.json").write_text(FIX_H.read_text())
    out = HermesAdapter().normalize(tmp_path)
    assert out["system_present"] is True
    assert len(out["tool_calls"]) >= 1


def test_normalize_gptmini(tmp_path):
    (tmp_path / "trace.session.json").write_text(FIX_G.read_text())
    out = HermesAdapter().normalize(tmp_path)
    assert isinstance(out["tool_calls"], list)
```

- [ ] **Step 2: 跑測試確認失敗** — Run: `... pytest tests/test_adapter_hermes.py -v` → FAIL。

- [ ] **Step 3: 寫 `runner/adapters/hermes.py`**

```python
"""Hermes 0.13.0（全新隔離實例）介面卡。trace=最新 session_*.json（含 system_prompt/tools/tool_calls）。
runner 須在 run 後把該 session 複製成 workdir/trace.session.json（見 runner.py 對 hermes 的特例）。"""
from __future__ import annotations
import json
from pathlib import Path
from runner import paths
from runner.adapters.base import HarnessAdapter

HERMES_HOME = paths.LAB_HOME / ".hermes"


class HermesAdapter(HarnessAdapter):
    name = "hermes"
    version = "0.13.0"

    def env(self, secrets: dict, model_snapshot: str) -> dict:
        return {"HOME": str(paths.LAB_HOME), "HERMES_HOME": str(HERMES_HOME),
                "ANTHROPIC_API_KEY": secrets.get("ANTHROPIC_API_KEY", ""),
                "OPENAI_API_KEY": secrets.get("OPENAI_API_KEY", "")}

    def command(self, prompt: str, model_snapshot: str, provider: str) -> list[str]:
        return [str(paths.HERMES_BIN), "-z", prompt,
                "-m", model_snapshot, "--provider", provider, "--yolo"]

    def latest_session(self) -> Path | None:
        d = HERMES_HOME / "sessions"
        sess = sorted(d.glob("session_*.json"), key=lambda p: p.stat().st_mtime) if d.exists() else []
        return sess[-1] if sess else None

    def raw_artifacts(self, workdir: Path) -> dict[str, Path]:
        f = workdir / "trace.session.json"
        return {"session": f} if f.exists() else {}

    def normalize(self, workdir: Path) -> dict:
        arts = self.raw_artifacts(workdir)
        tool_calls, reasoning_steps = [], []
        system_present = False
        step = 0
        if "session" in arts:
            data = json.loads(arts["session"].read_text())
            system_present = bool(data.get("system_prompt"))
            for msg in data.get("messages", []):
                for call in (msg.get("tool_calls") or []):
                    step += 1
                    fn = (call.get("function") or {})
                    tool_calls.append({"step": step,
                                       "tool_name": fn.get("name") or call.get("name") or "?",
                                       "args_summary": _summ(fn.get("arguments") or call.get("arguments")),
                                       "ts": msg.get("ts")})
                if msg.get("role") == "assistant" and msg.get("reasoning"):
                    reasoning_steps.append({"type": "reasoning", "present": True})
        return {
            "tool_calls": tool_calls, "reasoning_steps": reasoning_steps, "decision_points": [],
            "tokens": {"input": None, "cached_input": None, "output": None},
            "turns": len(tool_calls),
            "runtime_budget": {"max_output_tokens": None, "thinking_budget_tokens": None,
                               "context_window_tokens": None, "effort_source": "provider default + high (config)"},
            "system_present": system_present,
            "evidence_levels": {"tool_calls": "direct", "system_present": "direct",
                                "reasoning_steps": "source-derived", "tokens": "unknown"},
        }


def _summ(arguments) -> str:
    if isinstance(arguments, str):
        return arguments[:80]
    if isinstance(arguments, dict):
        for k in ("path", "file_path", "patch", "query"):
            if k in arguments:
                return f"{k}={str(arguments[k])[:80]}"
    return ""
```

- [ ] **Step 4: 加入 registry**（`ADAPTERS["hermes"] = HermesAdapter`）。

- [ ] **Step 5: 跑測試確認通過** — Run: `... pytest tests/test_adapter_hermes.py -v` → 3 passed。依 fixture 真實 JSON 結構（`messages`/`tool_calls` 的實際巢狀）校正。

- [ ] **Step 6: 全 adapter 一起跑迴歸**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/ -q`
Expected: 全綠（schema/configs/provision/grader/4 adapters）。

- [ ] **Step 7: Commit**

```bash
git add runner/adapters/hermes.py runner/adapters/__init__.py tests/test_adapter_hermes.py
git commit -m "feat(adapters): Hermes adapter (session_*.json normalizer); all 4 adapters green


```

---

## Task 14: 統一 Runner 編排 + 不可變存檔 + CLI

**Files:**
- Create: `runner/persist.py`、`runner/runner.py`、`runner/cli.py`
- Test: `tests/test_runner.py`（用 dry-run/mock adapter，不啟動真 harness）

- [ ] **Step 1: 寫 `runner/persist.py`**

```python
"""不可變存檔：raw 留 LAB/runs；normalized trace.json 寫進 repo traces/（sanitized、committed）。"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from runner import paths


def run_dir(config_id: int, task_id: str, repeat_index: int) -> Path:
    return paths.RUNS / str(config_id) / task_id / str(repeat_index)


def trace_path(config_id: int, task_id: str, repeat_index: int) -> Path:
    return paths.REPO / "traces" / str(config_id) / task_id / f"{repeat_index}.json"


def save_raw(config_id, task_id, repeat_index, artifacts: dict[str, Path]) -> dict[str, str]:
    raw = run_dir(config_id, task_id, repeat_index) / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    saved = {}
    for name, src in artifacts.items():
        if src and Path(src).exists():
            dst = raw / Path(src).name
            shutil.copy(src, dst)
            saved[name] = str(dst)
    return saved


def save_trace(trace: dict) -> Path:
    p = trace_path(trace["config_id"], trace["task_id"], trace["repeat_index"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(trace, ensure_ascii=False, indent=2))
    return p
```

- [ ] **Step 2: 寫 `runner/runner.py`**

```python
"""單次 (config, task, repeat) 端到端：provision → launch → capture → normalize → grade → persist。"""
from __future__ import annotations
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from runner import paths, persist
from runner.configs import Config, get_config
from runner.adapters import get_adapter
from runner.adapters.hermes import HermesAdapter
from runner.grader import run_grader
from runner.provision import load_tasks
from runner.trace_schema import NormalizedTrace, ToolCall, validate_trace

DEFAULT_TIMEOUT_S = 900


def _env_lock_ref() -> str:
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=paths.REPO,
                         capture_output=True, text=True).stdout.strip()
    return f"ENVIRONMENT.lock.md@{sha}"


def run_once(config_id: int, task_id: str, repeat_index: int,
             timeout_s: int = DEFAULT_TIMEOUT_S, secrets: dict | None = None) -> dict:
    cfg = get_config(config_id)
    task = {t["id"]: t for t in load_tasks()}[task_id]
    adapter = get_adapter(cfg.harness)
    secrets = secrets if secrets is not None else paths.load_secrets()

    wd = persist.run_dir(config_id, task_id, repeat_index) / "workdir"
    from runner.provision import provision_task
    provision_task(task, wd)

    env = dict(os.environ)
    env.update(adapter.env(secrets, cfg.model_snapshot))
    cmd = adapter.command(task["prompt"], cfg.model_snapshot, cfg.provider)

    t0 = time.time()
    try:
        subprocess.run(cmd, cwd=wd, env=env, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        pass
    wall = round(time.time() - t0, 2)

    # Hermes：session 在 HERMES_HOME，需複製進 workdir 供 adapter 解析
    if isinstance(adapter, HermesAdapter):
        sess = adapter.latest_session()
        if sess:
            (wd / "trace.session.json").write_text(sess.read_text())

    grade = run_grader(task, wd)
    norm = adapter.normalize(wd)
    saved_raw = persist.save_raw(config_id, task_id, repeat_index, adapter.raw_artifacts(wd))

    trace = NormalizedTrace(
        run_id=f"{cfg.harness}__{task_id}__{repeat_index}",
        config_id=config_id, harness=cfg.harness, harness_version=adapter.version,
        model=cfg.model_snapshot, model_snapshot=cfg.model_snapshot,
        task_id=task_id, task_category=task["category"], repeat_index=repeat_index,
        reasoning_effort="high",
        tool_calls=[ToolCall(**tc) for tc in norm["tool_calls"]],
        reasoning_steps=norm["reasoning_steps"], decision_points=norm["decision_points"],
        outcome={"success": grade.success, "grader_detail": grade.detail, "final_diff_path": None},
        tokens=norm["tokens"], wall_time_s=wall, turns=norm["turns"],
        runtime_budget=norm["runtime_budget"],
        raw_log_path=str(persist.run_dir(config_id, task_id, repeat_index) / "raw"),
        env_lock_ref=_env_lock_ref(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        evidence_levels=norm.get("evidence_levels", {}),
    ).to_dict()
    validate_trace(trace)
    persist.save_trace(trace)
    return trace
```

- [ ] **Step 3: 寫 `runner/cli.py`**

```python
"""CLI：python -m runner run --config N --task T --repeat R [--timeout S]
           python -m runner pilot   # 2 configs x 3 tasks（見 Task 15）"""
from __future__ import annotations
import argparse, json
from runner.runner import run_once


def main():
    ap = argparse.ArgumentParser(prog="runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", type=int, required=True)
    r.add_argument("--task", required=True)
    r.add_argument("--repeat", type=int, default=0)
    r.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    if args.cmd == "run":
        tr = run_once(args.config, args.task, args.repeat, args.timeout)
        print(json.dumps({"run_id": tr["run_id"], "success": tr["outcome"]["success"],
                          "tools": [t["tool_name"] for t in tr["tool_calls"]],
                          "wall_s": tr["wall_time_s"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

並建 `runner/__main__.py`:
```python
from runner.cli import main
main()
```

- [ ] **Step 4: 寫測試 `tests/test_runner.py`（mock adapter，不啟動真 harness）**

```python
import types
from runner import runner as R
from runner.trace_schema import validate_trace


class _MockAdapter:
    name = "claude_code"; version = "2.1.88"
    def env(self, secrets, model): return {}
    def command(self, prompt, model, provider): return ["true"]  # no-op
    def raw_artifacts(self, wd): return {}
    def normalize(self, wd):
        return {"tool_calls": [{"step": 1, "tool_name": "Read", "args_summary": "x", "ts": None}],
                "reasoning_steps": [], "decision_points": [],
                "tokens": {"input": None, "cached_input": None, "output": None}, "turns": 1,
                "runtime_budget": {"max_output_tokens": 64000, "thinking_budget_tokens": 63999,
                                   "context_window_tokens": 200000, "effort_source": "test"},
                "system_present": True, "evidence_levels": {}}


def test_run_once_produces_valid_trace(monkeypatch):
    monkeypatch.setattr(R, "get_adapter", lambda h: _MockAdapter())
    monkeypatch.setattr(R, "run_grader", lambda task, wd: types.SimpleNamespace(success=False, detail="baseline"))
    tr = R.run_once(1, "bugfix-t2-01", 0, secrets={"ANTHROPIC_API_KEY": "x"})
    validate_trace(tr)
    assert tr["config_id"] == 1
    assert tr["tool_calls"][0]["tool_name"] == "Read"
    assert tr["outcome"]["success"] is False
```

- [ ] **Step 5: 跑測試確認通過**

Run: `/data/harness-lab/runner-venv/bin/python -m pytest tests/test_runner.py -v`
Expected: 1 passed（trace 通過 schema 驗證、欄位正確）。再跑全套 `pytest tests/ -q` 確認全綠。

- [ ] **Step 6: 確保 raw/workdir 不進 git、traces/ 進 git**

`.gitignore` 確認不含 `traces/`；確認 `/data/harness-lab/runs/` 在 repo 外（本就如此）。

- [ ] **Step 7: Commit**

```bash
git add runner/persist.py runner/runner.py runner/cli.py runner/__main__.py tests/test_runner.py
git commit -m "feat(runner): end-to-end orchestration + immutable persistence + CLI (mock-tested)


```

---

## Task 16: Pilot（2 configs × 3 tasks）— 真實 run + Pilot 報告（放行關）

**Files:**
- Create: `docs/verification/2026-06-04-phase1-pilot-report.md`
- Create（產出）: `traces/<config>/<task>/0.json`（6 筆）

Pilot 選樣（§6.4）：2 configs × 3 tasks。configs 取 **#1 Claude Code/Haiku（anchor）** 與 **#6 Codex/GPT-mini（anchor）**（兩 anchor 跨模型、跨後端，最能暴露管線問題）。tasks 取**跨三類各一**：`bugfix-t2-01`（bug_fix）、`rename-t2-01`（rename）、`bench-grade-school`（benchmark）。共 6 次真實 run（會耗 API token，屬 Pilot 預期成本）。

- [ ] **Step 1: 先單跑 1 次（config 1 × bugfix-t2-01）做端到端煙霧**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && source infra/00-paths.sh && /data/harness-lab/runner-venv/bin/python -m runner run --config 1 --task bugfix-t2-01 --repeat 0'
```
Expected: 印出 JSON，含 `run_id`、`success`（true/false 皆可，重點是管線跑通）、非空 `tools` 序列、`wall_s`。並確認 `traces/1/bugfix-t2-01/0.json` 生成且通過 schema。若 adapter 解析不到 tool 序列或 grader 異常，**STOP**：依真實 raw（`/data/harness-lab/runs/1/bugfix-t2-01/0/raw/`）就地修正對應 adapter/grader，再重跑。

- [ ] **Step 2: 跑完整 Pilot 矩陣（2×3=6 次）**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && source infra/00-paths.sh && for c in 1 6; do for t in bugfix-t2-01 rename-t2-01 bench-grade-school; do echo "=== config $c task $t ==="; /data/harness-lab/runner-venv/bin/python -m runner run --config $c --task $t --repeat 0; done; done'
```
Expected: 6 行 JSON，皆有非空 tool 序列；6 個 `traces/{1,6}/<task>/0.json` 生成。記錄每次 success 與 wall_s。

- [ ] **Step 3: 驗證 Pilot 通過 §6.4 四項準則**

Run（彙整檢查）:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && /data/harness-lab/runner-venv/bin/python -c "
import json, glob
from runner.trace_schema import validate_trace
files = sorted(glob.glob(\"traces/*/*/0.json\"))
print(\"trace files:\", len(files))
for f in files:
    d = json.load(open(f)); validate_trace(d)
    print(f, \"| tools:\", len(d[\"tool_calls\"]), \"| success:\", d[\"outcome\"][\"success\"], \"| wall:\", d[\"wall_time_s\"])
"'
```
Expected: 6 個檔、全部通過 `validate_trace`、每個 `tools` 數 ≥ 1。四項準則：(a) 介面卡能擷取 tool 序列（tools≥1）、(b) grader 正確（success 反映實際修好與否；至少不全部觸底）、(c) trace 正規化無遺漏（schema 全過）、(d) 成本/時間在預期內（wall_s 合理、無逾時）。

- [ ] **Step 4: 寫 Pilot 報告 `docs/verification/2026-06-04-phase1-pilot-report.md`**

內容須含（無佔位、以實際數據填寫）：
- Scope：Phase 1 Pilot，2 configs（#1, #6）× 3 tasks，6 真實 run；未跑 Phase 2 全量。
- 環境：引用 `ENVIRONMENT.lock.md@<commit>`、runner-venv、相依版本。
- 結果表：每 run 的 config/task/tool 序列/success/wall_s/tokens（可得者）。
- 四項準則逐項「通過/未通過＋證據」。
- 跨 harness 觀察：同任務 #1 vs #6 的 tool 路徑差異（呼應研究問題）、各 harness trace 可見度（引 dossier M4 evidence level）。
- 成本/時間外推：以 Pilot 單次平均估 Phase 2 全量（6×20×3=360 次）的時間與 token 量級。
- 已知限制與待辦（若有 adapter 欄位為 unknown/partial，明列）。
- 放行建議：是否可進 Phase 2。

- [ ] **Step 5: 把 Pilot 產物與報告 commit（traces sanitized）**

先確認 committed traces 不含 secret:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && grep -riE "sk-[a-z0-9]{8}|api[_-]?key.*[a-z0-9]{12}|bearer " traces/ | head'
```
Expected: 無輸出。

```bash
git add traces/ docs/verification/2026-06-04-phase1-pilot-report.md
git commit -m "test(pilot): Phase 1 pilot 2 configs x 3 tasks end-to-end + pilot report (Phase 2 gate)


```

---

## Task 17: Phase 1 完成稽核 + 推上 GitHub + Gate

**Files:** Create `docs/verification/2026-06-04-phase1-completion-audit.md`

- [ ] **Step 1: 全測試與計數總驗**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && /data/harness-lab/runner-venv/bin/python -m pytest tests/ -q && /data/harness-lab/runner-venv/bin/python -c "
from runner.provision import load_tasks
from collections import Counter
ts=load_tasks(); print(\"tasks\",len(ts),dict(Counter(t[\"category\"] for t in ts)),dict(Counter(t[\"tier\"] for t in ts)))"'
```
Expected: 全測試綠；tasks=20、五類各 4。

- [ ] **Step 2: 寫完成稽核文件**（仿 Phase 0 audit）：列出 Phase 1 交付物（task suite 20、runner、4 adapters、trace schema、pilot 6 traces + 報告）、四 harness 啟動指令、grader 機制、sanitization 政策、HCI ground-truth 依賴狀態（Phase 2 產出後才供 HCI），並明記「Pilot gate 待使用者審閱放行才進 Phase 2」。

- [ ] **Step 3: push 上 GitHub**

Run:
```bash
ssh -i ~/.ssh/SSH_Tokyo_A1_Private.key opc@150.230.202.49 'cd /data/repos/xai-harness-faithfulness && git add docs/verification/2026-06-04-phase1-completion-audit.md && git commit -m "docs(verification): Phase 1 completion audit + Phase 2 gate

 && git push origin main && git log --oneline -8'
```
Expected: push 成功，最近 commit 為 Phase 1 稽核。

- [ ] **Step 4: Gate — 交付使用者審閱**

向使用者報告：Phase 1 全部完成、Pilot 跑通、4 項準則證據、Phase 2 全量成本/時間外推。**等待使用者審閱 Pilot 報告通過後，才進入 Phase 2（6×20×3 全量 factorial）。** 不自動開跑 Phase 2。

---

## Self-Review（對照 spec §6）

- §6.1 任務套件（20 = 5 類 ×4、Aider-polyglot benchmark + Tier-2 受控、自動 grader、baseline-fail 難度校準）→ Task 4–9 與 Task 11 修訂。SWE-bench Verified 已明確放棄，不進 Phase 1 任務來源。
- §6.2 統一 Runner（provision/launch/budget 注入/timeout/capture/grade/不可變存檔、四 harness 介面卡）→ Task 10–14；啟動指令與 budget 全取自 Phase 0 已驗證 smoke。
- §6.3 正規化 Trace schema（所有列出欄位）→ Task 2（含 evidence_levels 為跨 harness 誠實性增補）。
- §6.4 Pilot（2 configs × 3 tasks、四項驗證、報告經確認才放大）→ Task 16–17。
- 隔離鐵則：全程用 `LAB_HOME` 隔離、Hermes 用全新實例、secrets 不進 git、raw 不進 git → adapters/persist 已遵循；Pilot commit 前掃 secret。

**型別一致性檢查：** `NormalizedTrace`/`ToolCall` 欄位名在 schema、adapters、runner、tests 一致；`Config` 欄位（id/harness/model_role/model_snapshot/provider/role）一致；`get_adapter`/`ADAPTERS` 鍵 = harness 名一致；grader `GradeResult(success, detail)` 一致。

**待執行時就地確認的點（非佔位，為真實資料依賴）：** 各 adapter 的 `normalize` 解析路徑須對照 `tests/fixtures/` 真實欄位名校正（Task 10–13 各 Step 已註明）；Tier-1 instance 的確切 `instance_id` 與安裝指令於 Task 9 Step 2–3 依下載結果決定。
