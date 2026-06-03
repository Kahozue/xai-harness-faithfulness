#!/usr/bin/env bash
# 所有實驗 harness 的共用路徑與隔離環境。source 此檔後再呼叫各 harness。
set -euo pipefail
export LAB="/data/harness-lab"
export LAB_HOME="$LAB/home"          # 專屬 HOME：隔離所有 harness 的 dotfile 設定/狀態
export LAB_BIN="$LAB/bin"
export SECRETS="$HOME/.harness-exp"  # repo 外 secrets（git 不追蹤）
export ANTHROPIC_MODEL="claude-haiku-4-5-20251001"
export OPENAI_MODEL="gpt-5.4-mini-2026-03-17"
mkdir -p "$LAB" "$LAB_HOME" "$LAB_BIN" "$LAB/smoke"
# 載入 secrets（檔案需 chmod 600，已於既有流程建立）
set -a
[ -f "$SECRETS/anthropic.env" ] && . "$SECRETS/anthropic.env"
[ -f "$SECRETS/openai.env" ] && . "$SECRETS/openai.env"
set +a
