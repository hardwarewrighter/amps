#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo build --offline --release --locked
mkdir -p dist
cp target/release/tone-control dist/tone-control
