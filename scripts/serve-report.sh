#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
report_dir="$project_dir/reports"
port="${1:-8000}"

if [[ ! "$port" =~ ^[0-9]{1,5}$ ]] || (( 10#$port < 1 || 10#$port > 65535 )); then
    echo "Usage: $0 [port: 1-65535]" >&2
    exit 1
fi
port="$((10#$port))"

if [[ ! -f "$report_dir/index.html" ]]; then
    echo "Report missing: $report_dir/index.html" >&2
    echo "Generate it with scripts/build-comparison-report.py first." >&2
    exit 1
fi

echo "Serving $report_dir on 0.0.0.0:$port"
echo "Local URL: http://localhost:$port/"
if command -v ip >/dev/null 2>&1; then
    while read -r address; do
        echo "LAN URL:   http://$address:$port/"
    done < <(ip -4 -o addr show scope global | awk '{split($4, address, "/"); print address[1]}')
fi
echo "Leave this terminal open. Press Ctrl+C to stop."
echo

if command -v basic-http-server >/dev/null 2>&1; then
    exec basic-http-server -a "0.0.0.0:$port" "$report_dir"
elif command -v python >/dev/null 2>&1; then
    exec python -m http.server "$port" --bind 0.0.0.0 --directory "$report_dir"
else
    echo "Install Python or basic-http-server to serve the report." >&2
    exit 1
fi
