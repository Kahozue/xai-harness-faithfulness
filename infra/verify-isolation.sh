#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-paths.sh"
echo "=== 生產 Hermes (/home/opc/.hermes) 應維持不變（凍結錨點：config.yaml）==="
echo "prod config.yaml mtime : $(stat -c '%y' /home/opc/.hermes/config.yaml 2>/dev/null || echo NA)"
echo "prod SOUL.md     mtime : $(stat -c '%y' /home/opc/.hermes/SOUL.md 2>/dev/null || echo NA)"
echo "prod MEMORY.md   mtime : $(stat -c '%y' /home/opc/.hermes/memories/MEMORY.md 2>/dev/null || echo NA)"
echo "  （註：MEMORY.md 可能因正式花帆自身活動而變動，非本實驗所致；config.yaml 為凍結錨點，須恆等於基準）"
echo "=== 生產 hermes gateway 仍在跑且未被干擾 ==="
echo "gateway: $(systemctl --user is-active hermes-gateway 2>/dev/null || echo unknown)"
echo "=== lab hermes 用獨立 HERMES_HOME（不等於 prod）==="
echo "lab HERMES_HOME      : $LAB_HOME/.hermes"
echo "lab .hermes exists   : $([ -d "$LAB_HOME/.hermes" ] && echo yes || echo no)"
echo "lab != prod home     : $([ "$LAB_HOME/.hermes" != "/home/opc/.hermes" ] && echo yes || echo no)"
