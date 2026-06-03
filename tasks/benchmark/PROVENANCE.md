# Benchmark 任務 provenance

本目錄的 benchmark 任務取自 **Aider polyglot benchmark** 的 Python track，原始題目來自 **Exercism**。

- 來源 repo：https://github.com/Aider-AI/polyglot-benchmark （`python/exercises/practice/`）
- 原始題庫：Exercism Python track（https://github.com/exercism/python），依 Exercism 開源授權使用
- 取用日期：2026-06-04
- 選用練習（4 題，依小模型可攻性與多樣性挑選）：`grade-school`、`phone-number`、`pig-latin`、`bottle-song`
- 每題 vendoring 內容：
  - `baseline/`：函式 stub（`<snake>.py`）+ `instructions.md`（agent 的 workdir）
  - `reference_example.py`：Exercism 參考解，僅供難度校準與 provenance，**不進 agent workdir**
  - 隱藏測試：`tasks/graders/bench-<slug>_test.py`（評分時才複製進 workdir）
- 難度校準（D3）：每題 stub baseline 跑隱藏測試為 fail、`reference_example.py` 為 pass。

## 為何用 Aider polyglot 而非 SWE-bench Verified（決策紀錄）

本研究依變項是「各 harness 對同一任務的 tool 選擇序列差異」，success 僅為次要共變項。SWE-bench Verified 整套機制服務的是「在釘死舊環境裡忠實判 patch 對錯」的評分保真度，與本研究 DV 錯位；且實證顯示在 aarch64、不上官方 docker harness 的前提下，舊版依賴漂移會弄壞測試 oracle（連 gold patch 都 import 失敗）。Aider polyglot（Exercism）為純標準庫、原生可跑、自含 stub+測試的 agentic coding 任務，能在四個 coding harness 上以原生工具攻、可靠評分，且符合本實驗環境。SWE-bench / AgentBench / τ-bench 在報告中作為任務設計血緣引用。
