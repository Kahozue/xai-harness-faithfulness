"""harness 介面卡抽象：封裝啟動指令、環境、trace 來源、正規化。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path


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
         runtime_budget, system_present, evidence_levels}。"""
