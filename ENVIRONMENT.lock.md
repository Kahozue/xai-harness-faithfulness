# ENVIRONMENT.lock — 凍結實驗環境（版本全釘死）

> 所有 harness 與模型版本在此釘死。任何變更須更新本檔並記錄日期與理由。

## 平台
- Host: Oracle Linux (aarch64), VPS tokyo-a1
- node: v22.22.2 | npm: 10.9.7 | python: 3.11.13 | git: 2.47.3
- 隔離：LAB=/data/harness-lab，LAB_HOME=/data/harness-lab/home（專屬 HOME），secrets 於 ~/.harness-exp（repo 外）

## 模型（帶日期 snapshot）
- Haiku 4.5: `claude-haiku-4-5-20251001`（Anthropic 原生 api.anthropic.com）
- GPT-5.4-mini: `gpt-5.4-mini-2026-03-17`（OpenAI 原生 api.openai.com）
- reasoning effort: high（全部）

## Harness 版本（Task 2-7 填入確切值）
| Harness | 版本 | 安裝來源 | 安裝路徑 | 安裝日期 |
|---------|------|----------|----------|----------|
| Claude Code | 2.1.88 | local tarball | (TBD Task2) | (TBD) |
| claude-trace | 1.0.4 | npm @loki-zhou/claude-trace | (TBD Task3) | (TBD) |
| Codex CLI | (TBD Task4) | npm | (TBD) | (TBD) |
| OpenCode | (TBD Task5) | npm | (TBD) | (TBD) |
| Hermes | 0.13.0 | clean isolated instance | (TBD Task6) | (TBD) |
