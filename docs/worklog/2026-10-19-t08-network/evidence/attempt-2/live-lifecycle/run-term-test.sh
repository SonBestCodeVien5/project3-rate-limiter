#!/usr/bin/env bash
set -euo pipefail
root=/tmp/project3-t08-fixed-b
out=/tmp/project3-t08-validation-b
bash -c '
  set -euo pipefail
  source "$1/scripts/lab-common.sh"
  LAB_PROJECT=project3-t08-validation
  DIR=$2/term-cycle
  mkdir -p "$DIR"
  LAB_SAMPLE_CALL=0
  compose_timeout() {
    local limit=$1; shift
    if [[ "$*" == *"INFO cpu"* ]]; then
      LAB_SAMPLE_CALL=$((LAB_SAMPLE_CALL + 1))
      touch "$DIR/cpu-start-$LAB_SAMPLE_CALL"
      sleep .5
    fi
    timeout "$limit" docker compose --project-directory "$LAB_ROOT" -f "$LAB_ROOT/compose.yaml" -p "$LAB_PROJECT" "$@"
  }
  lab_sample "$DIR"
  for i in $(seq 1 1500); do [[ -e "$DIR/cpu-start-2" ]] && break; sleep .01; done
  [[ -e "$DIR/cpu-start-2" ]]
  kill -TERM "$LAB_SAMPLE_PID"
  lab_stop_sample
  python3 - "$1/scripts/analyze.py" "$DIR/redis-resources.log" >"$DIR/analyzer-live.json" <<'PY'
import importlib.util,json,pathlib,sys
spec=importlib.util.spec_from_file_location("analyze",sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(json.dumps(m.redis_resources(pathlib.Path(sys.argv[2])),indent=2))
PY
  rg -c "^total_net_input_bytes:" "$DIR/redis-resources.log" >"$DIR/input-sample-count.txt"
  rg -c "^total_net_output_bytes:" "$DIR/redis-resources.log" >"$DIR/output-sample-count.txt"
' _ "$root" "$out"
