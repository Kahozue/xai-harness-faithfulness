#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
CT_PREFIX="$LAB/trace/prefix"
mkdir -p "$CT_PREFIX"
npm install --prefix "$CT_PREFIX" "@loki-zhou/claude-trace@1.0.4"
ln -sf "$CT_PREFIX/node_modules/.bin/claude-trace" "$LAB_BIN/claude-trace"
"$LAB_BIN/claude-trace" --version 2>/dev/null || echo "claude-trace installed (no --version)"
