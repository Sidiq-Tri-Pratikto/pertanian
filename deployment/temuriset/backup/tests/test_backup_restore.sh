#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here/../../../.."
"${PYTHON_BIN:-python3}" -B -m unittest discover -s "$here" -p 'test_backup_tools.py'
