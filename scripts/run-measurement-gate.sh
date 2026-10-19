#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
timeout_seconds=240
output_root=
runner="$root/scripts/research-pilot.sh"
while (($#)); do
  case "$1" in
    --output-root) output_root=${2:?}; shift 2 ;;
    --timeout-seconds) timeout_seconds=${2:?}; shift 2 ;;
    --runner) runner=${2:?}; shift 2 ;;
    *) echo "usage: $0 --output-root NEW_DIR [--timeout-seconds N] [--runner PATH]" >&2; exit 2 ;;
  esac
done
[[ -n "$output_root" && "$timeout_seconds" =~ ^[1-9][0-9]*$ ]] || { echo 'output root and positive timeout are required' >&2; exit 2; }
[[ ! -e "$output_root" ]] || { echo "output already exists: $output_root" >&2; exit 2; }
if [[ "$runner" == "$root/scripts/research-pilot.sh" ]]; then
  [[ -z "$(git -C "$root" status --porcelain)" ]] || { echo 'measurement checkout must be clean' >&2; exit 2; }
fi
mkdir -p "$output_root"
output_root=$(cd "$output_root" && pwd)
invalid=0
completed=0
for profile in normal mixed; do
  for repeat in 1 2 3; do
    label="$profile-$repeat"
    run_root="$output_root/$label"
    mkdir "$run_root"
    export CUSTOM_PROFILE=$profile CUSTOM_MODE=redis CUSTOM_ALGORITHM=fixed-window CUSTOM_INSTANCES=2
    export CUSTOM_RPS=20 CUSTOM_LEGIT_RPS=20 CUSTOM_DURATION=30 CUSTOM_LIMIT=20 CUSTOM_WINDOW_MS=1000
    export CUSTOM_CAPACITY=20 CUSTOM_RATE=20 CUSTOM_BACKEND_CAPACITY=4 CUSTOM_BACKEND_SERVICE_MS=50 CUSTOM_FAIL_POLICY=closed
    if [[ "$profile" == mixed ]]; then export CUSTOM_RPS=120; fi
    set +e
    timeout "${timeout_seconds}s" bash "$runner" --case custom --repetitions 1 --analyze --output "$run_root/output" >"$run_root/runner.log" 2>&1
    runner_status=$?
    set -e
    if ((runner_status)); then
      printf '{"profile":"%s","repeat":%s,"runner_status":%s}\n' "$profile" "$repeat" "$runner_status" >"$run_root/runner-failure.json"
      echo "$label runner failed ($runner_status); retained $run_root" >&2
      exit 1
    fi
    case_dir="$run_root/output/custom-repeat-1"
    mkdir -p "$case_dir"
    set +e
    python3 "$root/scripts/check-gate-quality.py" "$case_dir" >"$run_root/quality-check.log" 2>&1
    quality_status=$?
    set -e
    ((completed+=1))
    ((quality_status == 0)) || invalid=1
    set +e
    python3 - "$case_dir/quality.json" "$output_root/stop.json" <<'PY'
import json,pathlib,sys
quality=json.load(open(sys.argv[1]))
state_path=pathlib.Path(sys.argv[2])
state=json.loads(state_path.read_text()) if state_path.exists() else {}
for flag in quality.get('flags',[]): state[flag]=state.get(flag,0)+1
state_path.write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps({'flags':quality.get('flags',[]),'repeated':[k for k,v in state.items() if v>=2]}))
sys.exit(2 if any(v>=2 for v in state.values()) else 0)
PY
    stop_status=$?
    set -e
    if ((stop_status)); then
      echo "$label repeated a blocker; stopping after $completed run(s)" >&2
      exit 2
    fi
  done
done
if ((completed != 6 || invalid)); then echo 'gate incomplete or has invalid runs' >&2; exit 1; fi
echo 'six normal/mixed runs completed and passed quality checks'
