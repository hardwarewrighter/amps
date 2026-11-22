#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$repo_root/tools/tone-control/dist/tone-control" \
  --port "${PORT:-/dev/ttyACM1}" "$@"
