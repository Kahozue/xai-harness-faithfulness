#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
OC_PREFIX="$LAB/opencode/prefix"; mkdir -p "$OC_PREFIX"
npm install --prefix "$OC_PREFIX" "opencode-ai@1.15.13"   # 釘死版本（Task5 Step1 探得 latest=1.15.13）
ln -sf "$OC_PREFIX/node_modules/.bin/opencode" "$LAB_BIN/opencode"
HOME="$LAB_HOME" "$LAB_BIN/opencode" --version
# --- 隔離 config（$LAB_HOME/.config/opencode）：雙 provider 走原生端點 ---
# high effort 於 smoke/runner 以 `run --variant high` 逐次注入（provider-specific reasoning effort）。
mkdir -p "$LAB_HOME/.config/opencode"
# 註：gpt-5.4-mini-2026-03-17 不在 OpenCode 內建 models.dev catalog，須在此顯式宣告自訂 model
# 才能路由到 openai 原生端點（Anthropic Haiku 4.5 已在 catalog，免宣告）。
cat > "$LAB_HOME/.config/opencode/opencode.json" <<JSON
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "anthropic": { "options": { "apiKey": "{env:ANTHROPIC_API_KEY}" } },
    "openai": {
      "options": { "apiKey": "{env:OPENAI_API_KEY}" },
      "models": {
        "$OPENAI_MODEL": { "name": "GPT-5.4 mini 2026-03-17", "tools": true, "reasoning": true }
      }
    }
  }
}
JSON
echo "opencode installed + isolated dual-provider config written at $LAB_HOME/.config/opencode/opencode.json"
