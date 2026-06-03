#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
CC_PREFIX="$LAB/claude-code/prefix"
mkdir -p "$CC_PREFIX"
# 以 lab-local prefix 安裝指定 tarball，絕不抓 npm 最新
npm install --prefix "$CC_PREFIX" "$LAB/claude-code/claude-code-2.1.88.tgz"
ln -sf "$CC_PREFIX/node_modules/.bin/claude" "$LAB_BIN/claude"
echo "installed claude at $LAB_BIN/claude"
