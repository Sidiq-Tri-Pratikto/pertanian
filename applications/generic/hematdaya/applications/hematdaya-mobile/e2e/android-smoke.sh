#!/usr/bin/env bash
# One file because android-emulator-runner gives each `script` line its own shell,
# so adb reverse, logcat and Maestro could not share state across lines.
set -euo pipefail

# The workflow reads this marker to tell a boot failure, which retries once, from a flow failure, which never does.
touch "${RUNNER_TEMP:?}/emulator-booted"

evidence_dir="${EVIDENCE_DIR:?}"
apk_path="${APK_PATH:?}"
flow_file="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/smoke.yaml"
mkdir -p "$evidence_dir/maestro-output" "$evidence_dir/maestro-debug"

{
  echo "api_level=$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
  echo "device_model=$(adb shell getprop ro.product.model | tr -d '\r')"
  echo "display_size=$(adb shell wm size | tr -d '\r' | sed -n '1s/.*: //p')"
  echo "display_density=$(adb shell wm density | tr -d '\r' | sed -n '1s/.*: //p')"
} >"$evidence_dir/device.txt"

adb reverse tcp:8081 tcp:8081
adb install -r "$apk_path"

adb logcat -v threadtime >"$evidence_dir/logcat.txt" 2>&1 &
logcat_pid=$!

flow_status=0
maestro test \
  --format junit \
  --output "$evidence_dir/maestro-report.xml" \
  --test-output-dir "$evidence_dir/maestro-output" \
  --debug-output "$evidence_dir/maestro-debug" \
  --flatten-debug-output \
  "$flow_file" || flow_status=$?

kill "$logcat_pid" 2>/dev/null || true
wait "$logcat_pid" 2>/dev/null || true

echo "$flow_status" >"$evidence_dir/flow-exit-code"
exit "$flow_status"
