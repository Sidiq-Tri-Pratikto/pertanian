#!/usr/bin/env bash
# Real core-only API through adb reverse, with an embedded app bundle and a separate 003 smoke job.
set -euo pipefail

touch "${RUNNER_TEMP:?}/offline-emulator-booted"
evidence="${EVIDENCE_DIR:?}"
apk="${APK_PATH:?}"
scenario_file="${OFFLINE_SCENARIO_FILE:?}"
postgres="${OFFLINE_POSTGRES_ID:?}"
flow="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/offline.yaml"
app=id.hematdaya.app
mkdir -p "$evidence"

{
  echo "candidate=$(git rev-parse HEAD)"
  echo "api_level=$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
  echo "device_model=$(adb shell getprop ro.product.model | tr -d '\r')"
  echo "display=$(adb shell wm size | tr -d '\r')"
  echo "density=$(adb shell wm density | tr -d '\r')"
  echo "composition=core-only"
  echo "apk_sha256=$(sha256sum "$apk" | cut -d ' ' -f1)"
  echo "apk_bytes=$(stat -c %s "$apk")"
  maestro --version
} > "$evidence/runtime.txt"

radio_online() {
  adb shell cmd connectivity airplane-mode disable
  adb shell svc wifi enable
  adb shell svc data enable
  adb reverse tcp:8034 tcp:8034
  for _ in $(seq 1 30); do
    if adb shell dumpsys connectivity | grep -E 'Active default network: [0-9]+' >/dev/null; then return 0; fi
    sleep 1
  done
  echo 'Android did not recover its default network' >&2
  return 1
}

radio_offline() {
  adb shell cmd connectivity airplane-mode enable
  adb shell svc wifi disable
  adb shell svc data disable
  adb reverse --remove tcp:8034
  [[ "$(adb shell settings get global airplane_mode_on | tr -d '\r')" = 1 ]]
  for _ in $(seq 1 20); do
    if ! adb shell dumpsys connectivity | grep -E 'Active default network: [0-9]+' >/dev/null; then break; fi
    sleep 1
  done
  if adb shell dumpsys connectivity | grep -E 'Active default network: [0-9]+' >/dev/null; then
    echo 'Android still has an active default network' >&2
    return 1
  fi
  if adb reverse --list | grep -q 'tcp:8034'; then
    echo 'ADB API route still present' >&2
    return 1
  fi
}

cleanup() {
  local code=$?
  trap - EXIT
  adb logcat -d -v brief AndroidRuntime:E ReactNativeJS:E '*:S' |     sed -E 's/hdd_[[:alnum:]_-]+/[redacted]/g; s/(Authorization: Bearer )[[:alnum:]_.-]+/\1[redacted]/gi'     > "$evidence/device-errors.txt" 2>/dev/null || true
  adb shell cmd connectivity airplane-mode disable >/dev/null 2>&1 || true
  adb reverse --remove tcp:8034 >/dev/null 2>&1 || true
  printf '%s\n' "$code" > "$evidence/flow-exit-code"
  exit "$code"
}
trap cleanup EXIT

flow_number=0
run() {
  local phase="$1" output
  flow_number=$((flow_number + 1))
  printf -v output '%s/%02d-%s' "$evidence" "$flow_number" "$phase"
  mkdir -p "$output"
  timeout 180s maestro test -e "CASE=$phase" --format junit     --output "$output/junit.xml" --test-output-dir "$output"     --debug-output "$output" --flatten-debug-output "$flow"
  printf '%s passed\n' "$phase" >> "$evidence/assertions.txt"
}

writes() {
  awk '/^(POST|PATCH|DELETE) / { n++ } END { print n+0 }' "$evidence/requests.txt"
}

read_saved_timestamp() {
  adb shell uiautomator dump /sdcard/spec034.xml >/dev/null
  adb exec-out cat /sdcard/spec034.xml | python3 -c '
import sys
import xml.etree.ElementTree as ET
root = ET.fromstring(sys.stdin.buffer.read())
times = {value for node in root.iter("node") for value in (node.get("text", ""), node.get("content-desc", ""))
         if value.startswith("Terakhir dimuat:")}
if len(times) != 1:
    raise SystemExit("Expected one visible saved-fetch timestamp")
print(times.pop())
'
  adb shell rm /sdcard/spec034.xml
}

choose() {
  printf '%s\n' "$1" > "$scenario_file"
}

expire_owner() {
  # Only isolated synthetic demo owners exist in this CI database. The app observes a real 401.
  docker exec "$postgres" psql -U app -d app -v ON_ERROR_STOP=1 -q     -c "UPDATE demo_sessions SET expires_at = now() - interval '1 second' WHERE expires_at > now()"
  run revoke
}

adb shell settings put global hide_error_dialogs 1
adb logcat -c
adb install -r "$apk"
radio_online

choose h-stale-offline
run stale-online
baseline="$(writes)"
radio_offline
run stale-warm
read_saved_timestamp > "$evidence/fetch-stale-warm.txt"
run draft-warm
adb shell am force-stop "$app"
run stale-cold
read_saved_timestamp > "$evidence/fetch-stale-cold.txt"
cmp "$evidence/fetch-stale-warm.txt" "$evidence/fetch-stale-cold.txt"
run draft-cold
[[ "$(writes)" = "$baseline" ]]
radio_online
run draft-reconnect
[[ "$(writes)" = "$baseline" ]]
run draft-save
[[ "$(writes)" = "$((baseline + 1))" ]]
printf '%s\n' 'No writes during offline, cold launch, or reconnect; exactly one after explicit save.' >> "$evidence/assertions.txt"

expire_owner
choose i-base
run other-owner
expire_owner
choose h-learning-partial
run learning
expire_owner
choose h-zero
run zero
expire_owner
choose h-scope
run scope
expire_owner
choose empty
run historical-online
baseline="$(writes)"
radio_offline
run historical-warm
read_saved_timestamp > "$evidence/fetch-historical-warm.txt"
adb shell am force-stop "$app"
run historical-cold
read_saved_timestamp > "$evidence/fetch-historical-cold.txt"
cmp "$evidence/fetch-historical-warm.txt" "$evidence/fetch-historical-cold.txt"
radio_online
run historical-reconnect
[[ "$(writes)" = "$baseline" ]]
printf '%s\n' 'Historical CSV preserved original fetch time; no reconnect write.' >> "$evidence/assertions.txt"
