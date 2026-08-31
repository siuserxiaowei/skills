#!/bin/bash

set -euo pipefail

if [ -z "${HOME:-}" ]; then
  CURRENT_USER="$(/usr/bin/id -un)"
  HOME="$(/usr/bin/dscl . -read "/Users/$CURRENT_USER" NFSHomeDirectory 2>/dev/null | /usr/bin/awk '{print $2}')"
  [ -n "$HOME" ] || { printf 'Codex Dream Skin Studio: could not resolve the current macOS home directory.\n' >&2; exit 1; }
  export HOME
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
INJECTOR="$SCRIPT_DIR/injector.mjs"
INSTALL_ROOT="$HOME/.codex/codex-dream-skin-studio"
STATE_ROOT="$HOME/Library/Application Support/CodexDreamSkinStudio"
STATE_PATH="$STATE_ROOT/state.json"
THEME_BACKUP_PATH="$STATE_ROOT/theme-backup.json"
THEME_DIR="$STATE_ROOT/theme"
CONFIG_PATH="$HOME/.codex/config.toml"
INJECTOR_LOG="$STATE_ROOT/injector.log"
INJECTOR_ERROR_LOG="$STATE_ROOT/injector-error.log"
APP_LOG="$STATE_ROOT/codex-launch.log"
APP_ERROR_LOG="$STATE_ROOT/codex-launch-error.log"
START_ERROR_LOG="$STATE_ROOT/start-error.log"
CODEX_APP_JOB_LABEL="com.openai.codex-dream-skin-studio.app"
INJECTOR_JOB_LABEL="com.openai.codex-dream-skin-studio.injector"
EXPECTED_CODEX_TEAM_ID="${CODEX_EXPECTED_TEAM_ID:-2DC432GLL2}"
SKIN_VERSION="1.3.0-bugfire.1"

fail() {
  local message="$*"
  if [ -n "${START_ERROR_LOG:-}" ] && [ -n "${STATE_ROOT:-}" ]; then
    /bin/mkdir -p "$STATE_ROOT" 2>/dev/null || true
    printf '%s %s\n' "$(/bin/date -u '+%Y-%m-%dT%H:%M:%SZ')" "$message" >> "$START_ERROR_LOG" 2>/dev/null || true
  fi
  printf 'Codex Dream Skin Studio: %s\n' "$message" >&2
  exit 1
}

ensure_state_root() {
  /bin/mkdir -p "$STATE_ROOT"
  /bin/chmod 700 "$STATE_ROOT"
}

discover_codex_app() {
  local candidate=""
  local identifier=""
  local executable_name=""
  local configured="${CODEX_APP_BUNDLE:-}"

  for candidate in "$configured" "/Applications/ChatGPT.app" "$HOME/Applications/ChatGPT.app"; do
    [ -n "$candidate" ] || continue
    [ -f "$candidate/Contents/Info.plist" ] || continue
    identifier="$(/usr/bin/plutil -extract CFBundleIdentifier raw -o - "$candidate/Contents/Info.plist" 2>/dev/null || true)"
    if [ "$identifier" = "com.openai.codex" ]; then
      CODEX_BUNDLE="$candidate"
      break
    fi
  done

  if [ -z "${CODEX_BUNDLE:-}" ]; then
    candidate="$(/usr/bin/mdfind 'kMDItemCFBundleIdentifier == "com.openai.codex"' | /usr/bin/head -n 1)"
    if [ -n "$candidate" ] && [ -f "$candidate/Contents/Info.plist" ]; then
      identifier="$(/usr/bin/plutil -extract CFBundleIdentifier raw -o - "$candidate/Contents/Info.plist" 2>/dev/null || true)"
      [ "$identifier" = "com.openai.codex" ] && CODEX_BUNDLE="$candidate"
    fi
  fi

  [ -n "${CODEX_BUNDLE:-}" ] || fail "Could not find the official Codex app bundle (com.openai.codex)."
  executable_name="$(/usr/bin/plutil -extract CFBundleExecutable raw -o - "$CODEX_BUNDLE/Contents/Info.plist")"
  CODEX_EXE="$CODEX_BUNDLE/Contents/MacOS/$executable_name"
  CODEX_VERSION="$(/usr/bin/plutil -extract CFBundleShortVersionString raw -o - "$CODEX_BUNDLE/Contents/Info.plist")"
  [ -x "$CODEX_EXE" ] || fail "Codex executable is missing: $CODEX_EXE"
  export CODEX_BUNDLE CODEX_EXE CODEX_VERSION
}

codesign_team_id() {
  /usr/bin/codesign -dv --verbose=4 "$1" 2>&1 \
    | /usr/bin/awk -F= '/^TeamIdentifier=/{print $2; exit}'
}

require_macos_runtime() {
  [ "$(/usr/bin/uname -s)" = "Darwin" ] || fail "This launcher requires macOS."
  [ -n "${CODEX_BUNDLE:-}" ] || fail "Discover the Codex app before validating its runtime."

  RUNTIME_NODE="$CODEX_BUNDLE/Contents/Resources/cua_node/bin/node"
  [ -x "$RUNTIME_NODE" ] || fail "The signed Node.js runtime bundled with Codex was not found: $RUNTIME_NODE"
  /usr/bin/codesign --verify --deep --strict "$CODEX_BUNDLE" >/dev/null 2>&1 \
    || fail "The Codex app signature is not valid. Restore or reinstall the official app before continuing."
  /usr/bin/codesign --verify --strict "$RUNTIME_NODE" >/dev/null 2>&1 \
    || fail "The Node.js runtime bundled with Codex failed code-signature validation."

  CODEX_TEAM_ID="$(codesign_team_id "$CODEX_BUNDLE")"
  NODE_TEAM_ID="$(codesign_team_id "$RUNTIME_NODE")"
  [ "$CODEX_TEAM_ID" = "$EXPECTED_CODEX_TEAM_ID" ] \
    || fail "Unexpected Codex signing team: ${CODEX_TEAM_ID:-missing}."
  [ "$NODE_TEAM_ID" = "$CODEX_TEAM_ID" ] \
    || fail "The bundled Node.js signer does not match the Codex app signer."

  local machine_arch
  local node_major
  machine_arch="$(/usr/bin/uname -m)"
  /usr/bin/file "$RUNTIME_NODE" | /usr/bin/grep -q "$machine_arch" \
    || fail "The Codex Node.js runtime does not match this Mac architecture ($machine_arch)."
  NODE_VERSION="$($RUNTIME_NODE --version)"
  node_major="${NODE_VERSION#v}"
  node_major="${node_major%%.*}"
  case "$node_major" in ''|*[!0-9]*) fail "Could not parse bundled Node.js version: $NODE_VERSION" ;; esac
  [ "$node_major" -ge 20 ] || fail "Codex bundled Node.js $NODE_VERSION is too old; version 20 or newer is required."

  NODE="$RUNTIME_NODE"
  export NODE RUNTIME_NODE NODE_VERSION CODEX_TEAM_ID NODE_TEAM_ID
}

codex_main_pids() {
  local pid
  local command_line
  while read -r pid command_line; do
    [ -n "$pid" ] || continue
    case "$command_line" in
      "$CODEX_EXE"*) printf '%s\n' "$pid" ;;
    esac
  done < <(/bin/ps -axo pid=,command=)
}

codex_is_running() {
  [ -n "$(codex_main_pids)" ]
}

process_started_at() {
  /bin/ps -p "$1" -o lstart= 2>/dev/null | /usr/bin/awk '{$1=$1; print}'
}

stop_codex() {
  local allow_force="${1:-false}"
  local deadline
  local pid

  release_codex_launchd_job
  codex_is_running || return 0
  /usr/bin/osascript -e 'tell application id "com.openai.codex" to quit' >/dev/null 2>&1 || true
  deadline=$((SECONDS + 15))
  while codex_is_running && [ "$SECONDS" -lt "$deadline" ]; do /bin/sleep 0.25; done
  codex_is_running || return 0

  [ "$allow_force" = "true" ] || fail "Codex did not close within 15 seconds; explicit restart authorization is required for a forced stop."
  while IFS= read -r pid; do
    [ -n "$pid" ] && /bin/kill -TERM "$pid" 2>/dev/null || true
  done < <(codex_main_pids)
  deadline=$((SECONDS + 5))
  while codex_is_running && [ "$SECONDS" -lt "$deadline" ]; do /bin/sleep 0.25; done
  if codex_is_running; then
    while IFS= read -r pid; do
      [ -n "$pid" ] && /bin/kill -KILL "$pid" 2>/dev/null || true
    done < <(codex_main_pids)
  fi
  /bin/sleep 0.5
  codex_is_running && fail "Codex could not be stopped safely."
  return 0
}

listener_pids() {
  /usr/sbin/lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | /usr/bin/sort -u || true
}

port_is_available() {
  [ -z "$(listener_pids "$1")" ]
}

pid_is_codex_descendant() {
  local current="$1"
  local command_line=""
  local parent=""
  local depth=0
  while [ "$current" -gt 1 ] 2>/dev/null && [ "$depth" -lt 32 ]; do
    command_line="$(/bin/ps -p "$current" -o command= 2>/dev/null || true)"
    case "$command_line" in "$CODEX_EXE"*) return 0 ;; esac
    parent="$(/bin/ps -p "$current" -o ppid= 2>/dev/null | /usr/bin/awk '{$1=$1; print}')"
    case "$parent" in ''|*[!0-9]*) return 1 ;; esac
    [ "$parent" -ne "$current" ] || return 1
    current="$parent"
    depth=$((depth + 1))
  done
  return 1
}

port_belongs_to_codex() {
  local port="$1"
  local found_direct="false"
  local pid
  local command_line
  while IFS= read -r pid; do
    [ -n "$pid" ] || continue
    command_line="$(/bin/ps -p "$pid" -o command= 2>/dev/null || true)"
    case "$command_line" in
      "$CODEX_EXE"*) found_direct="true" ;;
      *) pid_is_codex_descendant "$pid" || return 1 ;;
    esac
  done < <(listener_pids "$port")
  [ "$found_direct" = "true" ]
}

# Cheap: can we talk to a loopback DevTools HTTP endpoint?
cdp_http_ready() {
  local port="$1"
  /usr/bin/curl --noproxy '*' --silent --fail --max-time 1 \
    "http://127.0.0.1:${port}/json/version" >/dev/null 2>&1
}

verified_cdp_endpoint() {
  local port="$1"
  # Prefer identity check, but accept loopback CDP if HTTP is healthy and a
  # ChatGPT/Codex process is listening (path case / helper PIDs can fail belongs).
  if port_belongs_to_codex "$port"; then
    cdp_http_ready "$port" || return 1
    return 0
  fi
  cdp_http_ready "$port" || return 1
  # Fallback: listener must still be ChatGPT-related.
  local pid command_line
  while IFS= read -r pid; do
    [ -n "$pid" ] || continue
    command_line="$(/bin/ps -p "$pid" -o command= 2>/dev/null || true)"
    case "$command_line" in
      *ChatGPT*|*Codex*|*codex*) return 0 ;;
    esac
  done < <(listener_pids "$port")
  return 1
}

select_available_port() {
  local preferred="$1"
  local candidate="$preferred"
  local last=$((preferred + 100))
  [ "$last" -le 65535 ] || last=65535
  while [ "$candidate" -le "$last" ]; do
    if port_is_available "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
    candidate=$((candidate + 1))
  done
  fail "No free loopback port was found between $preferred and $last."
}

wait_for_cdp() {
  local port="$1"
  local deadline=$((SECONDS + 45))
  local last_note=0
  while [ "$SECONDS" -lt "$deadline" ]; do
    # Fast path: HTTP up is enough to proceed once process identity is soft-ok.
    if cdp_http_ready "$port"; then
      if verified_cdp_endpoint "$port" || cdp_http_ready "$port"; then
        # If HTTP is up and ChatGPT is running, accept.
        if codex_is_running || verified_cdp_endpoint "$port"; then
          return 0
        fi
      fi
    fi
    if [ $((SECONDS - last_note)) -ge 8 ]; then
      last_note=$SECONDS
      printf 'Waiting for Codex debug port %s… (%ss)\n' "$port" "$SECONDS" >&2
    fi
    /bin/sleep 0.35
  done
  return 1
}

state_field() {
  local key="$1"
  "$NODE" -e '
    const fs = require("node:fs");
    const value = JSON.parse(fs.readFileSync(process.argv[1], "utf8"))[process.argv[2]];
    if (value !== undefined && value !== null) process.stdout.write(String(value));
  ' "$STATE_PATH" "$key"
}

write_state() {
  local port="$1"
  local injector_pid="$2"
  local injector_started_at="$3"
  local codex_pid="$4"
  local node_ver="${NODE_VERSION:-unknown}"
  local bundle="${CODEX_BUNDLE:-}"
  local exe="${CODEX_EXE:-}"
  local app_ver="${CODEX_VERSION:-}"
  local team="${CODEX_TEAM_ID:-}"
  "$NODE" -e '
    const fs = require("node:fs");
    const [file, version, port, pid, startedAt, injector, node, nodeVersion, bundle, exe, appVersion, teamId, root, themeDir, codexPid, arch] = process.argv.slice(1);
    const state = {
      schemaVersion: 4,
      platform: `darwin-${arch}`,
      skinVersion: version,
      port: Number(port),
      injectorPid: Number(pid),
      injectorStartedAt: startedAt,
      injectorPath: injector,
      nodePath: node,
      nodeVersion,
      codexBundle: bundle,
      codexExe: exe,
      codexVersion: appVersion,
      codexTeamId: teamId,
      codexPid: Number(codexPid || 0),
      projectRoot: root,
      themeDir,
      createdAt: new Date().toISOString()
    };
    const temporary = `${file}.${process.pid}.tmp`;
    fs.writeFileSync(temporary, `${JSON.stringify(state, null, 2)}\n`, { mode: 0o600 });
    fs.renameSync(temporary, file);
  ' "$STATE_PATH" "$SKIN_VERSION" "$port" "$injector_pid" "$injector_started_at" "$INJECTOR" "$NODE" "$node_ver" "$bundle" "$exe" "$app_ver" "$team" "$PROJECT_ROOT" "$THEME_DIR" "$codex_pid" "$(/usr/bin/uname -m)"
}

process_matches_snapshot() {
  local pid="$1"
  local expected_start="$2"
  local expected_command="$3"
  local start_before=""
  local actual_command=""
  local start_after=""
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  [ -n "$expected_start" ] && [ -n "$expected_command" ] || return 1

  start_before="$(process_started_at "$pid")"
  [ -n "$start_before" ] && [ "$start_before" = "$expected_start" ] || return 1
  actual_command="$(/bin/ps -p "$pid" -o command= 2>/dev/null || true)"
  [ -n "$actual_command" ] && [ "$actual_command" = "$expected_command" ] || return 1
  start_after="$(process_started_at "$pid")"
  [ -n "$start_after" ] && [ "$start_after" = "$expected_start" ] || return 1
}

known_injector_command() {
  local command_line="$1"
  local prefix="${NODE} ${INJECTOR} --watch --port "
  local suffix=""
  local port=""
  case "$command_line" in
    "$prefix"*) ;;
    *) return 1 ;;
  esac
  suffix="${command_line#"$prefix"}"
  port="${suffix%% *}"
  case "$port" in ''|*[!0-9]*) return 1 ;; esac
  [ "$port" -ge 1 ] 2>/dev/null && [ "$port" -le 65535 ] 2>/dev/null || return 1
  [ "$suffix" = "$port --theme-dir $THEME_DIR" ]
}

known_injector_snapshot() {
  local pid="$1"
  local start_before=""
  local command_line=""
  local start_after=""
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac

  start_before="$(process_started_at "$pid")"
  [ -n "$start_before" ] || return 1
  command_line="$(/bin/ps -p "$pid" -o command= 2>/dev/null || true)"
  known_injector_command "$command_line" || return 1
  start_after="$(process_started_at "$pid")"
  [ -n "$start_after" ] && [ "$start_after" = "$start_before" ] || return 1
  printf '%s\t%s\t%s\n' "$pid" "$start_before" "$command_line"
}

stop_process_snapshot() {
  local pid="$1"
  local expected_start="$2"
  local expected_command="$3"
  local deadline=$((SECONDS + 6))

  # Every signal is preceded by a fresh start-time + exact-command check.
  process_matches_snapshot "$pid" "$expected_start" "$expected_command" || return 0
  /bin/kill -TERM "$pid" 2>/dev/null || return 0
  while [ "$SECONDS" -lt "$deadline" ]; do
    process_matches_snapshot "$pid" "$expected_start" "$expected_command" || return 0
    /bin/sleep 0.2
  done
  process_matches_snapshot "$pid" "$expected_start" "$expected_command" || return 0
  /bin/kill -KILL "$pid" 2>/dev/null || true
}

remove_injector_launchd_job() {
  /bin/launchctl remove "gui/$(/usr/bin/id -u)/$INJECTOR_JOB_LABEL" >/dev/null 2>&1 || true
  /bin/launchctl remove "$INJECTOR_JOB_LABEL" >/dev/null 2>&1 || true
}

stop_recorded_injector() {
  [ -f "$STATE_PATH" ] || return 0
  local pid=""
  local saved_start=""
  local saved_node=""
  local saved_injector=""
  local saved_port=""
  local saved_theme_dir=""
  local expected_command=""

  pid="$(state_field injectorPid 2>/dev/null || true)"
  saved_start="$(state_field injectorStartedAt 2>/dev/null || true)"
  saved_node="$(state_field nodePath 2>/dev/null || true)"
  saved_injector="$(state_field injectorPath 2>/dev/null || true)"
  saved_port="$(state_field port 2>/dev/null || true)"
  saved_theme_dir="$(state_field themeDir 2>/dev/null || true)"

  # The fixed label belongs to this installation; removing it never targets
  # an arbitrary PID. A direct fallback process is handled below.
  remove_injector_launchd_job
  case "$pid" in ''|0|*[!0-9]*) return 0 ;; esac
  case "$saved_port" in ''|*[!0-9]*) return 0 ;; esac
  [ -n "$saved_start" ] && [ -n "$saved_node" ] && [ -n "$saved_injector" ] \
    && [ -n "$saved_theme_dir" ] || return 0
  expected_command="$saved_node $saved_injector --watch --port $saved_port --theme-dir $saved_theme_dir"
  stop_process_snapshot "$pid" "$saved_start" "$expected_command"
}

stop_known_injectors() {
  local pid=""
  local command_line=""
  local snapshot=""
  local records=""
  local expected_start=""
  local expected_command=""

  # The fixed launchd label is owned by this installation and is safe to remove
  # even when state.json is missing or stale.
  remove_injector_launchd_job

  # Direct nohup fallback processes have no launchd label. Keep a full process
  # identity snapshot; a numeric PID by itself is never sufficient to signal.
  while read -r pid command_line; do
    [ -n "$pid" ] || continue
    known_injector_command "$command_line" || continue
    if snapshot="$(known_injector_snapshot "$pid")"; then
      if [ -n "$records" ]; then
        records="$records
$snapshot"
      else
        records="$snapshot"
      fi
    fi
  done < <(/bin/ps -axo pid=,command=)

  [ -n "$records" ] || return 0
  while IFS=$'\t' read -r pid expected_start expected_command; do
    [ -n "$pid" ] || continue
    stop_process_snapshot "$pid" "$expected_start" "$expected_command"
  done <<< "$records"
}

launch_injector_daemon() {
  local port="$1"
  local pid=""
  local deadline=$((SECONDS + 10))
  : > "$INJECTOR_LOG"
  : > "$INJECTOR_ERROR_LOG"
  /bin/launchctl remove "$INJECTOR_JOB_LABEL" >/dev/null 2>&1 || true

  # Prefer a direct background process — launchctl submit is unreliable on newer macOS.
  /usr/bin/nohup "$NODE" "$INJECTOR" --watch --port "$port" --theme-dir "$THEME_DIR" \
    >>"$INJECTOR_LOG" 2>>"$INJECTOR_ERROR_LOG" &
  pid="$!"
  /bin/sleep 0.4
  if [ -n "$pid" ] && /bin/kill -0 "$pid" 2>/dev/null; then
    printf '%s\n' "$pid"
    return 0
  fi

  # Fallback: launchctl submit
  /bin/launchctl submit -l "$INJECTOR_JOB_LABEL" -o "$INJECTOR_LOG" -e "$INJECTOR_ERROR_LOG" -- \
    "$NODE" "$INJECTOR" --watch --port "$port" --theme-dir "$THEME_DIR" >/dev/null 2>&1 || true
  /bin/launchctl kickstart -k "gui/$(/usr/bin/id -u)/$INJECTOR_JOB_LABEL" >/dev/null 2>&1 || true
  while [ "$SECONDS" -lt "$deadline" ]; do
    pid="$(/bin/launchctl print "gui/$(/usr/bin/id -u)/$INJECTOR_JOB_LABEL" 2>/dev/null \
      | /usr/bin/awk '/^[[:space:]]*pid = [0-9]+/{print $3; exit}')"
    if [ -n "$pid" ] && /bin/kill -0 "$pid" 2>/dev/null; then
      printf '%s\n' "$pid"
      return 0
    fi
    # Also detect the nohup node process by command line
    pid="$(/bin/ps -axo pid=,command= | /usr/bin/awk -v inj="$INJECTOR" -v port="$port" '
      index($0, inj) && index($0, "--watch") && index($0, port) { print $1; exit }
    ')"
    if [ -n "$pid" ] && /bin/kill -0 "$pid" 2>/dev/null; then
      printf '%s\n' "$pid"
      return 0
    fi
    /bin/sleep 0.2
  done
  fail "The injector did not start. See $INJECTOR_ERROR_LOG and $INJECTOR_LOG"
}

# Resolve Node quickly: prefer known Codex path, else full runtime check.
ensure_node_runtime() {
  if [ -n "${NODE:-}" ] && [ -x "${NODE:-}" ]; then
    if [ -z "${NODE_VERSION:-}" ]; then
      NODE_VERSION="$("$NODE" --version 2>/dev/null || echo unknown)"
      export NODE_VERSION
    fi
    # Fill CODEX_* if missing so write_state does not explode under set -u
    : "${CODEX_BUNDLE:=}"
    : "${CODEX_EXE:=}"
    : "${CODEX_VERSION:=}"
    : "${CODEX_TEAM_ID:=}"
    return 0
  fi
  local candidate
  for candidate in \
    "/Applications/Codex.app/Contents/Resources/cua_node/bin/node" \
    "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node" \
    "$HOME/Applications/Codex.app/Contents/Resources/cua_node/bin/node"
  do
    if [ -x "$candidate" ]; then
      NODE="$candidate"
      NODE_VERSION="$("$NODE" --version 2>/dev/null || echo unknown)"
      export NODE NODE_VERSION
      : "${CODEX_BUNDLE:=/Applications/Codex.app}"
      : "${CODEX_EXE:=/Applications/Codex.app/Contents/MacOS/ChatGPT}"
      : "${CODEX_VERSION:=}"
      : "${CODEX_TEAM_ID:=}"
      # Soft-fill from state if present
      if [ -f "$STATE_PATH" ]; then
        eval "$(/usr/bin/python3 -c 'import json,sys
try:
  s=json.load(open(sys.argv[1]))
  for k,env in [("codexBundle","CODEX_BUNDLE"),("codexExe","CODEX_EXE"),("codexVersion","CODEX_VERSION"),("codexTeamId","CODEX_TEAM_ID")]:
    v=s.get(k) or ""
    if v: print(f"export {env}={json.dumps(v)}")
except Exception: pass' "$STATE_PATH" 2>/dev/null || true)"
      fi
      return 0
    fi
  done
  discover_codex_app
  require_macos_runtime
}

# Copy a fully validated theme into a same-filesystem staging directory, then
# replace the active directory with atomic renames. The old active directory is
# retained inside the transaction until the new directory is in place, so a
# failed second rename can be rolled back without exposing a partial theme.
activate_theme_from_directory() {
  local source_dir="$1"
  local transaction_dir=""
  local staged_dir=""
  local previous_dir=""
  local had_previous="false"

  [ -d "$source_dir" ] || fail "Theme source is missing: $source_dir"
  [ -f "$source_dir/theme.json" ] || fail "Theme source is missing theme.json: $source_dir"
  ensure_state_root
  ensure_node_runtime

  transaction_dir="$(/usr/bin/mktemp -d "$STATE_ROOT/.theme-swap.XXXXXX")" \
    || fail "Could not create a theme activation transaction."
  staged_dir="$transaction_dir/staged"
  previous_dir="$transaction_dir/previous"
  /bin/mkdir "$staged_dir" || {
    /bin/rm -rf "$transaction_dir" 2>/dev/null || true
    fail "Could not create the staged theme directory."
  }
  if ! /bin/chmod 700 "$transaction_dir" "$staged_dir"; then
    /bin/rm -rf "$transaction_dir" 2>/dev/null || true
    fail "Could not secure the staged theme directory."
  fi

  if ! /bin/cp -R "$source_dir/." "$staged_dir/"; then
    /bin/rm -rf "$transaction_dir" 2>/dev/null || true
    fail "Could not stage the selected theme."
  fi
  if ! /usr/bin/find "$staged_dir" -type d -exec /bin/chmod 700 {} + \
    || ! /usr/bin/find "$staged_dir" -type f -exec /bin/chmod 600 {} +; then
    /bin/rm -rf "$transaction_dir" 2>/dev/null || true
    fail "Could not secure the staged theme contents."
  fi

  # Validate the exact staged bytes. This closes the gap between validating the
  # library copy and activating a second, potentially incomplete copy.
  if ! "$NODE" "$INJECTOR" --check-payload --theme-dir "$staged_dir" >/dev/null; then
    /bin/rm -rf "$transaction_dir" 2>/dev/null || true
    fail "The staged theme failed payload validation; the active theme was not changed."
  fi

  if [ -e "$THEME_DIR" ] || [ -L "$THEME_DIR" ]; then
    if ! /bin/mv "$THEME_DIR" "$previous_dir"; then
      /bin/rm -rf "$transaction_dir" 2>/dev/null || true
      fail "Could not preserve the active theme before activation."
    fi
    had_previous="true"
  fi

  if ! /bin/mv "$staged_dir" "$THEME_DIR"; then
    if [ "$had_previous" = "true" ]; then
      if ! /bin/mv "$previous_dir" "$THEME_DIR"; then
        fail "Theme activation failed and automatic rollback failed; the previous theme remains at $previous_dir"
      fi
    fi
    /bin/rm -rf "$transaction_dir" 2>/dev/null || true
    fail "Theme activation failed; the previous theme was restored."
  fi

  /bin/rm -rf "$transaction_dir" \
    || fail "Theme activated, but its temporary transaction could not be removed: $transaction_dir"
}

# Fast path when CDP is already open: restart injector + one-shot inject.
# Returns 0 on success, 1 if CDP is not ready (caller should full-start).
hot_reapply_theme() {
  local port="${1:-9341}"
  local timeout_ms="${2:-8000}"

  cdp_http_ready "$port" || return 1
  ensure_node_runtime || return 1

  stop_recorded_injector 2>/dev/null || true
  stop_known_injectors

  local inj_pid
  inj_pid="$(launch_injector_daemon "$port")"
  /bin/sleep 0.25
  /bin/kill -0 "$inj_pid" 2>/dev/null || return 1

  # One-shot reloads theme files from disk (watch may still be starting).
  if ! "$NODE" "$INJECTOR" --once --port "$port" --theme-dir "$THEME_DIR" --timeout-ms "$timeout_ms" >/dev/null 2>&1; then
    # Soft: keep watch running even if once flaked
    :
  fi

  local started_at codex_pid
  started_at="$(process_started_at "$inj_pid")"
  codex_pid="$(codex_main_pids 2>/dev/null | /usr/bin/head -n 1)"
  [ -n "$started_at" ] || started_at="$(/bin/date)"
  write_state "$port" "$inj_pid" "$started_at" "${codex_pid:-0}"
  return 0
}

# Always tear down any leftover launchd babysitter for the themed Codex process.
# Older builds used `launchctl submit` which can relaunch Codex after the user quits
# or after SwiftBar exits — that is unexpected and unwanted.
release_codex_launchd_job() {
  /bin/launchctl remove "gui/$(/usr/bin/id -u)/$CODEX_APP_JOB_LABEL" >/dev/null 2>&1 || true
  /bin/launchctl remove "$CODEX_APP_JOB_LABEL" >/dev/null 2>&1 || true
}

launch_codex_with_cdp() {
  local port="$1"
  : > "$APP_LOG"
  : > "$APP_ERROR_LOG"
  release_codex_launchd_job
  # Start as a normal user process (NOT launchctl submit). submit keeps a job
  # that will restart Codex when the window is closed.
  /usr/bin/open -na "$CODEX_BUNDLE" --args \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$port" \
    >>"$APP_LOG" 2>>"$APP_ERROR_LOG" || true
  # Fallback if open failed to pass args on some builds
  if ! codex_is_running; then
    /usr/bin/nohup "$CODEX_EXE" \
      --remote-debugging-address=127.0.0.1 \
      --remote-debugging-port="$port" \
      >>"$APP_LOG" 2>>"$APP_ERROR_LOG" &
  fi
}

launch_codex_normally() {
  release_codex_launchd_job
  /usr/bin/open -na "$CODEX_BUNDLE"
}
