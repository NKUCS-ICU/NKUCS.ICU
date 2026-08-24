#!/usr/bin/env bash
# sync-readmes.sh
# 从根目录 _sidebar.md 自动生成全部课程 README.md。
#
# 使用方式: bash scripts/sync-readmes.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO_ROOT/scripts/site_tools.py" sync
