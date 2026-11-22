#!/usr/bin/env bash
# Play the opening Imperial March melody. PORT is forwarded to tone-control.sh.
set -euo pipefail
usage() { echo "Usage: $0 [speed multiplier]  (default: 1.5; higher is faster)"; }
if [[ ${1:-} == --help || ${1:-} == -h ]]; then
  usage
  exit 0
fi
speed="${1:-1.5}"
if (( $# > 1 )) || [[ ! $speed =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)$ ]] ||
   ! awk -v speed="$speed" 'BEGIN { exit !(speed > 0 && speed <= 100) }'; then
  usage >&2
  echo "Speed must be a number greater than 0 and at most 100." >&2
  exit 1
fi
# Calculate each distinct delay once, avoiding a subprocess for every note.
declare -A delays
while read -r duration scaled; do
  delays["$duration"]="$scaled"
done < <(awk -v speed="$speed" 'BEGIN {
  n = split("0.45 0.30 0.12 0.85 0.20 0.25 0.060", durations, " ")
  for (i = 1; i <= n; i++) printf "%s %.6f\n", durations[i], durations[i] / speed
}')
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
control="$script_dir/tone-control.sh"

cleanup() { "$control" stop >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Each note has a short silent gap; rests and durations are in seconds.
note() {
  "$control" frequency "$1" >/dev/null
  "$control" start >/dev/null
  sleep "${delays[$2]}"
  "$control" stop >/dev/null
  sleep "${delays[0.060]}"
}
rest() { sleep "${delays[$1]}"; }

"$control" stop >/dev/null

# G4 G4 G4 Eb4 Bb4 G4 Eb4 Bb4 G4
note 392 0.45
note 392 0.45
note 392 0.45
note 311 0.30
note 466 0.12
note 392 0.45
note 311 0.30
note 466 0.12
note 392 0.85
rest 0.20

# D5 D5 D5 Eb5 Bb4 Gb4 Eb4 Bb4 G4
note 587 0.45
note 587 0.45
note 587 0.45
note 622 0.30
note 466 0.12
note 370 0.45
note 311 0.30
note 466 0.12
note 392 0.85
rest 0.20

# G5 G4 G4 G5 Gb5 F5 E5 Eb5 E5
note 784 0.45
note 392 0.30
note 392 0.12
note 784 0.45
note 740 0.30
note 698 0.12
note 659 0.12
note 622 0.12
note 659 0.25
rest 0.20

# Ab4 Db5 C5 B4 Bb4 A4 Bb4
note 415 0.25
note 554 0.45
note 523 0.30
note 494 0.12
note 466 0.12
note 440 0.12
note 466 0.25
rest 0.20

# Eb4 Gb4 Eb4 Gb4 Bb4 G4 Bb4 D5
note 311 0.25
note 370 0.45
note 311 0.30
note 370 0.12
note 466 0.45
note 392 0.30
note 466 0.12
note 587 0.85
rest 0.20

# Repeat the high phrase, then resolve to G.
note 784 0.45
note 392 0.30
note 392 0.12
note 784 0.45
note 740 0.30
note 698 0.12
note 659 0.12
note 622 0.12
note 659 0.25
rest 0.20
note 415 0.25
note 554 0.45
note 523 0.30
note 494 0.12
note 466 0.12
note 440 0.12
note 466 0.25
rest 0.20
note 311 0.25
note 370 0.45
note 311 0.30
note 466 0.12
note 392 0.45
note 311 0.30
note 466 0.12
note 392 0.85
