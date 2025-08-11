#!/usr/bin/env bash
: '=======================================================
Application Launcher

Requires Python and UV to be installed
=========================================================='

set -euo pipefail

# --- config ---
ScriptName="main.py"

# Resolve script dir and cd there
HomeDir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$HomeDir"

# Find uv reliably (systemd often has a minimal PATH)
if command -v uv >/dev/null 2>&1; then
  UVCmd="$(command -v uv)"
elif [ -x "$HOME/.local/bin/uv" ]; then
  UVCmd="$HOME/.local/bin/uv"
else
  echo "[launcher] Error: 'uv' not found in PATH or at \$HOME/.local/bin/uv" >&2
  exit 1
fi

# On Raspberry Pi, enforce Python 3.13+ if requested
if [[ $(uname -m) == "armv7l" || $(uname -m) == "aarch64" ]]; then
  if ! "$UVCmd" python pin --resolved 2>/dev/null | grep -Eq '^(3\.1[3-9]|3\.[2-9][0-9]|[4-9])'; then
    echo "[launcher] Error: project must pin Python 3.13+ on Raspberry Pi. Run: uv python pin 3.13" >&2
    exit 1
  fi
fi

# Make sure deps are synced before starting
if ! "$UVCmd" sync; then
  echo "[launcher] uv sync failed — not starting app." >&2
  exit 2
fi

# Treat Ctrl-C or systemd stop (SIGTERM) as a clean, intentional shutdown
term_handler() {
  echo "[launcher] Caught termination — exiting cleanly so systemd does not restart."
  exit 0
}
trap term_handler SIGINT SIGTERM

echo "[launcher] Starting app with uv run $ScriptName ..."
"$UVCmd" run "$ScriptName"
app_rc=$?

if [ $app_rc -eq 0 ]; then
  echo "[launcher] App exited normally (0)."
  exit 0
else
  echo "[launcher] App exited with error ($app_rc) — signaling failure so systemd restarts."
  exit $app_rc
fi
