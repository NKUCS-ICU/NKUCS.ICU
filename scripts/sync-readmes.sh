#!/usr/bin/env bash
# sync-readmes.sh
# 从根目录 _sidebar.md 自动提取各年级课程列表，生成对应 README.md
# 这保证了课程列表只需要在 _sidebar.md 中维护一份即可
#
# 使用方式: bash scripts/sync-readmes.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIDEBAR="$REPO_ROOT/_sidebar.md"

if [[ ! -f "$SIDEBAR" ]]; then
  echo "错误: 找不到 $SIDEBAR"
  exit 1
fi

sync_section() {
  local keyword="$1"
  local target_dir="$2"
  local readme="$REPO_ROOT/$target_dir/README.md"

  mkdir -p "$REPO_ROOT/$target_dir"

  local in_section=0
  local section_indent=""
  local lines=""

  while IFS= read -r line; do
    if [[ "$line" == *"$keyword"* ]] && [[ "$line" == *"- ["* ]]; then
      in_section=1
      section_indent="${line%%[-]*}"
      continue
    fi

    if [[ $in_section -eq 1 ]]; then
      local current_indent="${line%%[-]*}"

      if [[ -z "${line// /}" ]]; then
        continue
      fi

      if [[ ${#current_indent} -le ${#section_indent} ]] && [[ "$line" == *"- ["* ]]; then
        break
      fi

      local trimmed
      trimmed="$(echo "$line" | sed 's/^[[:space:]]*//')"
      if [[ "$trimmed" == "- ["* ]]; then
        lines+="$trimmed"$'\n'
      fi
    fi
  done < "$SIDEBAR"

  if [[ -z "$lines" ]]; then
    echo "WARNING: section \"$keyword\" not found, skipping $target_dir"
    return
  fi

  printf '%s' "$lines" > "$readme"
  local count
  count="$(echo "$lines" | grep -c '^-' || true)"
  echo "OK: $readme ($count courses)"
}

echo "=== Syncing course README.md files from _sidebar.md ==="
echo ""

sync_section "大一课程" "courses/grade-1"
sync_section "大二课程" "courses/grade-2"
sync_section "大三课程" "courses/grade-3"
sync_section "大四课程" "courses/grade-4"

echo ""
echo "Done! All README.md files are now in sync with _sidebar.md."
echo "Tip: Only edit the root _sidebar.md, then run this script to sync."
