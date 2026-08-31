#!/bin/bash

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
. "$SCRIPT_DIR/release-layout.sh"
ROOT="$BUGFIRE_ENGINE_ROOT"
PROJECT_ROOT="$BUGFIRE_PROJECT_ROOT"
VERSION="$(/usr/bin/tr -d '[:space:]' < "$ROOT/VERSION")"
SKIP_TESTS="false"
if [ "${1:-}" = "--skip-tests" ]; then SKIP_TESTS="true"; shift; fi
if [ "$#" -gt 1 ]; then
  /usr/bin/printf 'Usage: %s [--skip-tests] [output.zip]\n' "$0" >&2
  exit 1
fi
OUTPUT="${1:-$HOME/Desktop/Codex 主题编辑器.zip}"
TMP="$(/usr/bin/mktemp -d /tmp/codex-dream-client.XXXXXX)"
CLIENT_ROOT="$TMP/Codex 主题编辑器"
ENGINE="$CLIENT_ROOT/.codex-dream-skin-studio"
trap '/bin/rm -rf "$TMP"' EXIT

if [ "$SKIP_TESTS" != "true" ]; then "$ROOT/tests/run-tests.sh"; fi
/bin/mkdir -p "$ENGINE"
/usr/bin/rsync -a \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  --exclude 'release/' \
  --exclude 'runtime/' \
  "$ROOT/" "$ENGINE/"
/bin/mkdir -p "$ENGINE/skills/codex-bugfire-customizer"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$PROJECT_ROOT/skills/codex-bugfire-customizer/" \
  "$ENGINE/skills/codex-bugfire-customizer/"
/bin/mkdir -p "$ENGINE/contest/bugfire"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$PROJECT_ROOT/contest/bugfire/" \
  "$ENGINE/contest/bugfire/"
/bin/mkdir -p "$ENGINE/docs"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$PROJECT_ROOT/docs/" \
  "$ENGINE/docs/"
"$ROOT/scripts/prepare-package-layout.sh" "$ENGINE"

/usr/bin/printf '%s\n' \
  '#!/bin/bash' \
  'set -euo pipefail' \
  'ROOT="$(cd "$(dirname "$0")" && pwd -P)"' \
  'exec "$ROOT/.codex-dream-skin-studio/scripts/install-dream-skin-macos.sh"' \
  > "$CLIENT_ROOT/安装 Codex 主题编辑器.command"

/usr/bin/printf '%s\n' \
  "Codex BUGFIRE 补丁兽 $VERSION" \
  '' \
  '推荐方式：把这个完整 ZIP、你喜欢的图片和“给 Codex 的部署提示词.md”一起发给自己的 Codex。' \
  '' \
  '手动方式：双击“安装 Codex 主题编辑器.command”。安装完成后，桌面会出现启动、定制、验证和恢复四个入口。' \
  '' \
  '不要只复制图片或 CSS。隐藏目录 .codex-dream-skin-studio 是完整运行引擎，请勿删除。' \
  > "$CLIENT_ROOT/使用说明.txt"

/bin/cp "$ROOT/CLIENT_DEPLOY_PROMPT.md" "$CLIENT_ROOT/给 Codex 的部署提示词.md"
/bin/chmod 755 "$CLIENT_ROOT/安装 Codex 主题编辑器.command"
/bin/chmod 755 "$ENGINE"/*.command "$ENGINE"/scripts/*.sh "$ENGINE"/tests/*.sh
/bin/chmod 755 "$ENGINE"/skills/codex-bugfire-customizer/scripts/*.sh
/bin/chmod 755 "$ENGINE"/contest/bugfire/*.sh
/usr/bin/xattr -cr "$CLIENT_ROOT"
/usr/bin/find "$CLIENT_ROOT" -type f \( -name '.DS_Store' -o -name '._*' \) -delete
/bin/mkdir -p "$(dirname "$OUTPUT")"
/bin/rm -f "$OUTPUT"
COPYFILE_DISABLE=1 /usr/bin/ditto -c -k --keepParent --norsrc --noextattr "$CLIENT_ROOT" "$OUTPUT"
SHA256="$(/usr/bin/shasum -a 256 "$OUTPUT" | /usr/bin/awk '{print $1}')"
/usr/bin/printf 'Created %s\nSHA-256 %s\n' "$OUTPUT" "$SHA256"
