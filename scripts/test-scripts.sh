#!/usr/bin/env bash
# Exercise fault cleanup without Docker, including failure during pause.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for status in 0 9; do
  set +e
  bash -c '
    source "$1/scripts/lab-common.sh"
    # Override helper with a captured path, avoiding process-global Docker access.
    TEST_LOG=$2
    compose() { printf "%s\n" "$*" >>"$TEST_LOG"; }
    compose_timeout() { shift; compose "$@"; }
    LAB_OWNED=1
    LAB_PAUSED=1
    trap lab_cleanup EXIT
    exit "$3"
  ' _ "$root" "$tmp/cleanup-$status.log" "$status"
  result=$?
  set -e
  [[ "$result" == "$status" ]]
  expected=$'unpause redis\ndown --remove-orphans'
  [[ "$(cat "$tmp/cleanup-$status.log")" == "$expected" ]]
done
mkdir -p "$root/artifacts"
exec 9>"$root/artifacts/.research-pilot.lock"
flock -n 9
if bash "$root/scripts/research-pilot.sh" --case mixed-redis --output "$tmp/should-not-start" >"$tmp/locked.log" 2>&1; then
  echo 'research pilot accepted a second runner' >&2
  exit 1
fi
[[ ! -e "$tmp/should-not-start" ]]
grep -q 'research pilot already running' "$tmp/locked.log"
flock -u 9
echo 'Script cleanup and runner lock tests passed'
