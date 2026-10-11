#!/usr/bin/env bash
# Bounded smoke/pilot, not the locked research protocol or a statistical evaluation.
set -euo pipefail
source "$(dirname "$0")/lab-common.sh"
LAB_OUTPUT=${1:-"$LAB_ROOT/artifacts/pilot-$(date -u +%Y%m%dT%H%M%S)-$$"}
mkdir -p "$LAB_OUTPUT"
LAB_OUTPUT=$(cd "$LAB_OUTPUT" && pwd)
lab_prepare
export FAIL_POLICY=closed
for variant in none:fixed-window local:fixed-window local:token-bucket redis:fixed-window redis:token-bucket; do
  IFS=: read -r MODE ALGORITHM <<<"$variant"
  export MODE ALGORITHM
  case_name="$MODE-$ALGORITHM"
  export NAMESPACE="pilot-$$-$case_name"
  case_dir="$LAB_OUTPUT/$case_name"
  lab_start "$case_dir"
  lab_sample "$case_dir"
  "$LAB_OUTPUT/loadgen" -target http://localhost:8080/work -duration 5s -rps 300 -legitimate-rps 20 -legitimate-clients 5 -max-inflight 100 -timeout 2s -run-id "$case_name" -out "$case_dir/load" -mode "$MODE" -algorithm "$ALGORITHM" -fail-policy "$FAIL_POLICY" | tee "$case_dir/loadgen.log"
  lab_stop_sample
  lab_snapshot "$case_dir"
done
echo "Pilot artifacts: $LAB_OUTPUT"
