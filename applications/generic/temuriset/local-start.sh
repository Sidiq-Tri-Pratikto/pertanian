#!/usr/bin/env bash
# Start the whole local stack: Postgres, API and the web app. Ctrl+C stops everything.
#
#   ./local-start.sh                       web app on http://localhost:3020
#   API_PORT=8030 WEB_PORT=3030 ./local-start.sh   when something else holds the ports
set -euo pipefail

cd "$(dirname "$0")"

API_DIR=applications/temuriset-api
WEB_DIR=applications/temuriset-web
API_PORT="${API_PORT:-8020}"
WEB_PORT="${WEB_PORT:-3020}"

say() { printf '\n==> %s\n' "$1"; }
die() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }
port_in_use() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

use_project_node() {
  local wanted
  wanted="$(cat "$WEB_DIR/.nvmrc")"
  if [ -s "$HOME/.nvm/nvm.sh" ]; then
    # nvm is not written for strict mode.
    set +eu
    . "$HOME/.nvm/nvm.sh"
    nvm use "$wanted" >/dev/null 2>&1 || nvm install "$wanted" >/dev/null
    set -eu
  fi
  [ "$(node -v 2>/dev/null | sed 's/^v\([0-9]*\).*/\1/')" = "$wanted" ] ||
    die "Node $wanted is required, found $(node -v 2>/dev/null || echo none). Install nvm, or Node $wanted directly."
}

check_requirements() {
  command -v curl >/dev/null || die "curl is required to check that the API started."
  command -v uv >/dev/null || die "uv is required: https://docs.astral.sh/uv/getting-started/installation/"
  command -v docker >/dev/null || die "Docker is required: https://docs.docker.com/get-started/get-docker/"
  docker info >/dev/null 2>&1 || die "Docker is not running. Start Docker, then run this again."
  use_project_node
  port_in_use "$API_PORT" && die "Port $API_PORT is in use. Try: API_PORT=8030 ./local-start.sh"
  port_in_use "$WEB_PORT" && die "Port $WEB_PORT is in use. Try: WEB_PORT=3030 ./local-start.sh"
  return 0
}

cleanup() {
  trap - EXIT INT TERM
  say "Stopping"
  if [ -n "${API_PID:-}" ]; then kill -- "-$API_PID" 2>/dev/null || true; fi
  make -C "$API_DIR" stop-dependencies >/dev/null 2>&1 || true
}

check_requirements

say "[1/4] Installing dependencies"
make -C "$API_DIR" install >/dev/null
# npm ci deletes node_modules, so run it only when the lockfile changed.
[ "$WEB_DIR/node_modules/.package-lock.json" -nt "$WEB_DIR/package-lock.json" ] || make -C "$WEB_DIR" install

trap cleanup EXIT
trap 'cleanup; exit 0' INT TERM

say "[2/4] Starting Postgres on port 5442 and applying migrations"
make -C "$API_DIR" run-dependencies >/dev/null 2>&1 || die "Postgres did not start. Is port 5442 already in use?"
make -C "$API_DIR" migrate >/dev/null

say "[3/4] Starting API on port $API_PORT"
set -m # Own process group, so cleanup also stops uvicorn's reloader.
WEB_ORIGIN="http://localhost:$WEB_PORT" make -C "$API_DIR" run PORT="$API_PORT" &
API_PID=$!
set +m

for _ in $(seq 1 30); do
  curl -sf "http://127.0.0.1:$API_PORT/health/ready" >/dev/null && break
  sleep 1
done
curl -sf "http://127.0.0.1:$API_PORT/health/ready" >/dev/null || die "The API did not become ready. See its log above."

say "[4/4] Starting web app on port $WEB_PORT"
cat <<READY

  Web app    http://localhost:$WEB_PORT
  API docs   http://localhost:$API_PORT/docs
  Health     http://localhost:$API_PORT/health/ready

  Ctrl+C stops the web app, the API and Postgres.

READY
API_URL="http://localhost:$API_PORT" make -C "$WEB_DIR" run PORT="$WEB_PORT"
