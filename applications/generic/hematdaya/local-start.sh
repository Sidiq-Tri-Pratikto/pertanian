#!/usr/bin/env bash
# Start the whole local stack: Postgres, API and the mobile app. Ctrl+C stops everything.
#
#   ./local-start.sh           web app on http://localhost:8081
#   ./local-start.sh phone     QR code for Expo Go, on a phone on the same Wi-Fi
#
# Change ports when something else holds them:
#   API_PORT=8010 WEB_PORT=8082 ./local-start.sh
set -euo pipefail

cd "$(dirname "$0")"

API_DIR=applications/hematdaya-api
MOBILE_DIR=applications/hematdaya-mobile
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-8081}"
MODE="${1:-web}"

say() { printf '\n==> %s\n' "$1"; }
die() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }
port_in_use() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

lan_address() {
  hostname -I 2>/dev/null | awk '{print $1}' | grep . || ipconfig getifaddr en0 2>/dev/null
}

use_project_node() {
  local wanted
  wanted="$(cat "$MOBILE_DIR/.nvmrc")"
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
  [ "$MODE" = web ] || [ "$MODE" = phone ] || die "Unknown mode '$MODE'. Use: ./local-start.sh [phone]"
  command -v uv >/dev/null || die "uv is required: https://docs.astral.sh/uv/getting-started/installation/"
  command -v docker >/dev/null || die "Docker is required: https://docs.docker.com/get-started/get-docker/"
  docker info >/dev/null 2>&1 || die "Docker is not running. Start Docker, then run this again."
  use_project_node
  port_in_use "$API_PORT" && die "Port $API_PORT is in use. Try: API_PORT=8010 ./local-start.sh"
  port_in_use "$WEB_PORT" && die "Port $WEB_PORT is in use. Try: WEB_PORT=8082 ./local-start.sh"
  return 0
}

cleanup() {
  trap - EXIT INT TERM
  say "Stopping"
  if [ -n "${API_PID:-}" ]; then kill -- "-$API_PID" 2>/dev/null || true; fi
  make -C "$API_DIR" stop-dependencies >/dev/null 2>&1 || true
}

check_requirements

say "Installing dependencies"
make -C "$API_DIR" install >/dev/null
# npm ci deletes node_modules, so run it only when the lockfile changed.
[ "$MOBILE_DIR/node_modules/.package-lock.json" -nt "$MOBILE_DIR/package-lock.json" ] || make -C "$MOBILE_DIR" install

trap cleanup EXIT
trap 'cleanup; exit 0' INT TERM

say "Starting Postgres"
make -C "$API_DIR" run-dependencies >/dev/null 2>&1 || die "Postgres did not start. Is port 5432 already in use?"
make -C "$API_DIR" migrate >/dev/null

say "Starting API on port $API_PORT"
set -m # Own process group, so cleanup also stops uvicorn's reloader.
CORS_ALLOWED_ORIGINS="[\"http://localhost:$WEB_PORT\"]" make -C "$API_DIR" run PORT="$API_PORT" &
API_PID=$!
set +m

for _ in $(seq 1 30); do
  curl -sf "http://127.0.0.1:$API_PORT/health/ready" >/dev/null && break
  sleep 1
done
curl -sf "http://127.0.0.1:$API_PORT/health/ready" >/dev/null || die "The API did not become ready. See its log above."

if [ "$MODE" = phone ]; then
  ADDRESS="${LAN_IP:-$(lan_address || true)}"
  [ -n "$ADDRESS" ] || die "Could not find this computer's Wi-Fi address. Set it: LAN_IP=192.168.1.20 ./local-start.sh phone"
  export EXPO_PUBLIC_API_URL="http://$ADDRESS:$API_PORT"
  say "Scan the QR code with Expo Go. The app will call $EXPO_PUBLIC_API_URL. Ctrl+C stops everything."
  make -C "$MOBILE_DIR" run PORT="$WEB_PORT"
else
  export EXPO_PUBLIC_API_URL="http://localhost:$API_PORT"
  say "App http://localhost:$WEB_PORT | API docs http://localhost:$API_PORT/docs | Ctrl+C stops everything."
  make -C "$MOBILE_DIR" web PORT="$WEB_PORT"
fi
