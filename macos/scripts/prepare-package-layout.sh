#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
. "$SCRIPT_DIR/release-layout.sh"

TARGET="${1:-}"
if [ -z "$TARGET" ] || [ ! -d "$TARGET" ] || [ -L "$TARGET" ]; then
  /usr/bin/printf 'Usage: %s /absolute/staged-engine-directory\n' "$0" >&2
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd -P)"

rewrite_file() {
  local file="$1"
  shift
  local temporary="$file.package-layout.$$"
  /usr/bin/sed "$@" "$file" > "$temporary"
  /bin/mv "$temporary" "$file"
}

for evidence in \
  LICENSE NOTICE.md PROVENANCE.md SOURCES.md THIRD_PARTY_NOTICES.md \
  ASSET_RIGHTS.csv SECURITY.md; do
  /bin/cp "$BUGFIRE_PROJECT_ROOT/$evidence" "$TARGET/$evidence"
done

rewrite_file "$TARGET/SOURCES.md" -e 's#macos/##g'
rewrite_file "$TARGET/THIRD_PARTY_NOTICES.md" -e 's#macos/##g'
rewrite_file "$TARGET/ASSET_RIGHTS.csv" \
  -e 's#documented in macos/references/#documented in references/#g'

rewrite_file "$TARGET/README.md" \
  -e 's#cd macos#cd .#g' \
  -e 's#\.\./docs/#docs/#g' \
  -e 's#\.\./skills/#skills/#g' \
  -e 's#\.\./contest/#contest/#g'
rewrite_file "$TARGET/docs/USAGE.zh-CN.md" -e 's#cd macos#cd .#g'
rewrite_file "$TARGET/docs/SECURITY-ARCHITECTURE.zh-CN.md" \
  -e 's#cd macos#cd .#g' \
  -e 's#\.\./macos/#../#g'
rewrite_file "$TARGET/docs/CUSTOMIZATION.zh-CN.md" -e 's#macos/scripts/#scripts/#g'
rewrite_file "$TARGET/contest/bugfire/README.md" \
  -e 's#node macos/scripts/#node scripts/#g' \
  -e 's#cd macos#cd .#g'
