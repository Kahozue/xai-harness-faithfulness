#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
# 全新乾淨隔離 Hermes：用生產同版 0.13.0 二進位，但獨立 HERMES_HOME（乾淨 config + 空 memory）。
# 雙重隔離：HOME 與 HERMES_HOME 皆指向 lab，絕不碰 /home/opc/.hermes（正式花帆）。
export HOME="$LAB_HOME"
export HERMES_HOME="$LAB_HOME/.hermes"
mkdir -p "$HERMES_HOME"
# 認證 .env（key 從已載入環境注入；此檔在 repo 外、chmod 600、永不進 git）
cat > "$HERMES_HOME/.env" <<ENV
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
ENV
chmod 600 "$HERMES_HOME/.env"
# 乾淨 config：openai 原生(gpt-5.4-mini) + anthropic 原生(Haiku 4.5, anthropic_messages) + high effort。
# schema 依生產 /home/opc/.hermes/config.yaml 真實格式校正（model/providers/agent）。
cat > "$HERMES_HOME/config.yaml" <<YAML
model:
  default: ${OPENAI_MODEL}
  provider: openai
  base_url: https://api.openai.com/v1
providers:
  openai:
    name: OpenAI
    base_url: https://api.openai.com/v1
    key_env: OPENAI_API_KEY
    models:
    - ${OPENAI_MODEL}
  anthropic:
    name: Anthropic
    base_url: https://api.anthropic.com
    api_mode: anthropic_messages
    key_env: ANTHROPIC_API_KEY
    models:
    - ${ANTHROPIC_MODEL}
fallback_providers: []
toolsets:
- hermes-cli
agent:
  reasoning_effort: high
  max_turns: 100
YAML
echo "clean isolated hermes config written under $HERMES_HOME"
ls -la "$HERMES_HOME"
