#!/usr/bin/env bash
# Only pause the Redis service of the newly created, dedicated Compose lab.
# Each workload is 10s; nominal pause is 2s. Docker operations can add bounded
# control-plane delay; actual requested/completed timestamps are recorded.
set -euo pipefail
source "$(dirname "$0")/lab-common.sh"
LAB_OUTPUT=${1:-"$LAB_ROOT/artifacts/outage-$(date -u +%Y%m%dT%H%M%S)-$$"}
mkdir -p "$LAB_OUTPUT"
LAB_OUTPUT=$(cd "$LAB_OUTPUT" && pwd)
lab_prepare
export MODE=redis
export ALGORITHM=${ALGORITHM:-fixed-window}
for FAIL_POLICY in open closed; do
  export FAIL_POLICY NAMESPACE="outage-$$-$FAIL_POLICY"
  case_dir="$LAB_OUTPUT/$FAIL_POLICY"
  lab_start "$case_dir"
  date -u +%Y-%m-%dT%H:%M:%S.%NZ >"$case_dir/redis-before.txt"
  compose_timeout 5s exec -T redis redis-cli INFO cpu >>"$case_dir/redis-before.txt"
  compose_timeout 5s exec -T redis redis-cli INFO memory >>"$case_dir/redis-before.txt"
  "$LAB_OUTPUT/loadgen" -target http://localhost:8080/work -duration 10s -rps 100 -legitimate-rps 20 -legitimate-clients 5 -max-inflight 100 -timeout 2s -run-id "outage-$FAIL_POLICY" -out "$case_dir/load" -mode "$MODE" -algorithm "$ALGORITHM" -fail-policy "$FAIL_POLICY" >"$case_dir/loadgen.log" 2>&1 &
  LAB_LOAD_PID=$!
  # Startup is a compiled binary; metadata is written immediately before scheduling.
  for attempt in {1..100}; do
    [[ -f "$case_dir/load/metadata.json" ]] && break
    kill -0 "$LAB_LOAD_PID" 2>/dev/null || { wait "$LAB_LOAD_PID"; exit 1; }
    sleep .05
  done
  [[ -f "$case_dir/load/metadata.json" ]] || { echo "Loadgen did not start" >&2; exit 1; }
  sleep 3
  printf '%s pause_requested\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$case_dir/outage-events.txt"
  LAB_PAUSED=1
  compose_timeout 10s pause redis >>"$case_dir/outage-events.txt" 2>&1
  printf '%s pause_completed\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$case_dir/outage-events.txt"
  sleep 2
  printf '%s unpause_requested\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$case_dir/outage-events.txt"
  compose_timeout 10s unpause redis >>"$case_dir/outage-events.txt" 2>&1
  LAB_PAUSED=0
  printf '%s unpause_completed\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$case_dir/outage-events.txt"
  wait "$LAB_LOAD_PID"
  LAB_LOAD_PID=
  compose_timeout 5s exec -T redis redis-cli INFO cpu >"$case_dir/redis-after.txt"
  compose_timeout 5s exec -T redis redis-cli INFO memory >>"$case_dir/redis-after.txt"
  lab_snapshot "$case_dir"
done
echo "Outage pilot artifacts: $LAB_OUTPUT"
