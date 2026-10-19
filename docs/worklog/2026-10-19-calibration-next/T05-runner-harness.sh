#!/usr/bin/env bash
set -u
trap 'exit 130' INT
trap 'exit 143' TERM
root=/tmp/project3-calibration-26b5dec
out=artifacts/t05-final
mkdir -p "$out"
declare -A failures=()
declare -A already_valid=(
  [none-fw-api1-rps50]=1 [local-fw-api1-rps50]=1 [redis-fw-api1-rps50]=1
  [none-fw-api2-rps50]=1 [local-fw-api2-rps50]=1 [redis-fw-api2-rps50]=1
  [none-fw-api4-rps50]=1 [local-fw-api4-rps50]=1 [redis-fw-api4-rps50]=1
  [none-fw-api1-rps180]=1 [local-fw-api1-rps180]=1 [redis-fw-api1-rps180]=1
  [none-fw-api2-rps180]=1 [local-fw-api2-rps180]=1 [redis-fw-api2-rps180]=1
)
for rps in 50 180 250; do
  for instances in 1 2 4; do
    for mode in none local redis; do
      cell="${mode}-fw-api${instances}-rps${rps}"
      if [[ -n "${already_valid[$cell]:-}" ]]; then echo "KEEP previously validated $cell"; continue; fi
      case_dir="$out/$cell"
      echo "START $cell"
      CUSTOM_MODE=$mode CUSTOM_ALGORITHM=fixed-window CUSTOM_INSTANCES=$instances CUSTOM_PROFILE=normal CUSTOM_RPS=$rps CUSTOM_LEGIT_RPS=$rps CUSTOM_DURATION=10 CUSTOM_LIMIT=1000 CUSTOM_WINDOW_MS=1000 CUSTOM_CAPACITY=1000 CUSTOM_RATE=1000 CUSTOM_BACKEND_CAPACITY=10 CUSTOM_BACKEND_SERVICE_MS=50 CUSTOM_FAIL_POLICY=closed bash scripts/research-pilot.sh --case custom --analyze --output "$case_dir" >"/tmp/t05-$cell-runner.log" 2>&1
      rc=$?
      if ((rc != 0)); then
        printf '{"valid":false,"flags":["runner_exit_%s"]}\n' "$rc" >"$case_dir/runner-failure.json"
        reason="runner_exit_$rc"
      else
        python3 /tmp/project3-t05-check.py "$case_dir/custom-repeat-1"
        check_rc=$?
        if ((check_rc == 0)); then
          echo "PASS $cell"
          continue
        fi
        reason=$(python3 - "$case_dir/custom-repeat-1/t05-quality.json" <<'PY'
import json,sys
print(','.join(json.load(open(sys.argv[1]))['flags']))
PY
)
        [[ -n "$reason" ]] || reason=checker_error
      fi
      echo "INVALID $cell $reason"
      IFS=',' read -r -a reasons <<< "$reason"
      for issue in "${reasons[@]}"; do
        failures[$issue]=$(( ${failures[$issue]:-0} + 1 ))
        if (( failures[$issue] >= 2 )); then
          echo "STOP repeated unresolved blocker: $issue"
          exit 42
        fi
      done
    done
  done
done
echo "T05 initial matrix complete"
