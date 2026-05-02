#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_DIR="${ZOTERO_PROFILE_DIR:-$ROOT/.local/zotero-oa-profile}"
PLUGIN_DIR="$ROOT/tools/zotero-oa-bridge"
EXT_DIR="$PROFILE_DIR/extensions"
PREFS="$PROFILE_DIR/prefs.js"

mkdir -p "$EXT_DIR"
rm -f "$EXT_DIR/oa-pipeline-bridge@local.xpi"
printf '%s\n' "$PLUGIN_DIR" > "$EXT_DIR/oa-pipeline-bridge@local"
if [ -f "$PREFS" ]; then
  sed -i '/extensions\.lastAppBuildId/d;/extensions\.lastAppVersion/d' "$PREFS"
fi
echo "Installed Zotero OA bridge proxy: $EXT_DIR/oa-pipeline-bridge@local -> $PLUGIN_DIR"
