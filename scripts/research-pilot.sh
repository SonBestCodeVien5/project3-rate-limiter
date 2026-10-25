#!/usr/bin/env bash
# Candidate pilot only. Owns a dedicated Compose project and destroys only its own containers.
set -euo pipefail
source "$(dirname "$0")/lab-common.sh"
LAB_PROJECT=project3-research-lab
LAB_COMPOSE_FILE=
LAB_HOST_PORT=${LAB_HOST_PORT:-18080}
REPETITIONS=1
RUN_ANALYSIS=0
MONITORING=0
MIXED_RPS=${MIXED_RPS:-300}
SELECTED=()
LAB_OUTPUT=

usage() {
  cat <<'EOF'
Usage: bash scripts/research-pilot.sh [--output NEW_DIR] [--repetitions 1..3] [--monitoring]
       [--case NAME]... [--analyze] [--host-port 1024..65535]
Cases: normal, burst-fw, burst-tb, concurrent-local, concurrent-redis,
       scale-1, scale-2, scale-4, mixed-none, mixed-local, mixed-redis, custom.
Custom uses bounded CUSTOM_* environment variables; see scripts/README.md.
EOF
}
while (($#)); do
  case "$1" in
    --output|--repetitions|--case|--host-port)
      (($# >= 2)) || { usage >&2; exit 2; }
      case "$1" in
        --output) LAB_OUTPUT=$2 ;;
        --repetitions) REPETITIONS=$2 ;;
        --case) SELECTED+=("$2") ;;
        --host-port) LAB_HOST_PORT=$2 ;;
      esac
      shift 2 ;;
    --analyze) RUN_ANALYSIS=1; shift ;;
    --monitoring) MONITORING=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ "$REPETITIONS" =~ ^[1-3]$ ]] || { echo 'repetitions must be 1..3' >&2; exit 2; }
[[ "$LAB_HOST_PORT" =~ ^[0-9]+$ ]] && (( LAB_HOST_PORT >= 1024 && LAB_HOST_PORT <= 65535 )) || { echo 'invalid host port' >&2; exit 2; }
ALL_CASES=(normal burst-fw burst-tb concurrent-local concurrent-redis scale-1 scale-2 scale-4 mixed-none mixed-local mixed-redis)
ALLOWED_CASES=("${ALL_CASES[@]}" custom)
if ((${#SELECTED[@]} == 0)); then SELECTED=("${ALL_CASES[@]}"); fi
for requested in "${SELECTED[@]}"; do
  found=0
  for allowed in "${ALLOWED_CASES[@]}"; do [[ "$requested" == "$allowed" ]] && found=1; done
  ((found)) || { echo "unknown case: $requested" >&2; exit 2; }
done
if [[ "${SELECTED[*]}" == *custom* ]] && ((${#SELECTED[@]} != 1)); then
  echo 'custom must run alone' >&2; exit 2
fi
if [[ "${SELECTED[0]}" != custom ]]; then
  [[ "$MIXED_RPS" =~ ^[1-9][0-9]{0,5}$ ]] && (( MIXED_RPS > 20 && MIXED_RPS <= 100000 )) || { echo 'MIXED_RPS must be an integer in 21..100000' >&2; exit 2; }
fi
if [[ "${SELECTED[0]}" == custom ]]; then
  CUSTOM_MODE=${CUSTOM_MODE:-redis}
  CUSTOM_ALGORITHM=${CUSTOM_ALGORITHM:-fixed-window}
  CUSTOM_INSTANCES=${CUSTOM_INSTANCES:-2}
  CUSTOM_PROFILE=${CUSTOM_PROFILE:-mixed}
  CUSTOM_RPS=${CUSTOM_RPS:-120}
  CUSTOM_LEGIT_RPS=${CUSTOM_LEGIT_RPS-20}
  CUSTOM_DURATION=${CUSTOM_DURATION:-6}
  CUSTOM_LIMIT=${CUSTOM_LIMIT:-20}
  CUSTOM_WINDOW_MS=${CUSTOM_WINDOW_MS:-1000}
  CUSTOM_CAPACITY=${CUSTOM_CAPACITY:-20}
  CUSTOM_RATE=${CUSTOM_RATE:-20}
  CUSTOM_BACKEND_CAPACITY=${CUSTOM_BACKEND_CAPACITY:-10}
  CUSTOM_BACKEND_SERVICE_MS=${CUSTOM_BACKEND_SERVICE_MS-50}
  CUSTOM_FAIL_POLICY=${CUSTOM_FAIL_POLICY:-closed}
  CUSTOM_BURST_START=${CUSTOM_BURST_START:-2}
  CUSTOM_BURST_DURATION=${CUSTOM_BURST_DURATION:-2}
  CUSTOM_BURST_RPS=${CUSTOM_BURST_RPS:-200}
  CUSTOM_CONCURRENT_AT=${CUSTOM_CONCURRENT_AT-2}
  CUSTOM_CONCURRENT_COUNT=${CUSTOM_CONCURRENT_COUNT:-100}
  valid_int() { [[ "$1" =~ ^(0|[1-9][0-9]{0,3})$ ]] && (( $1 >= $2 && $1 <= $3 )); }
  [[ "$CUSTOM_MODE" == none || "$CUSTOM_MODE" == local || "$CUSTOM_MODE" == redis ]] || { echo 'invalid CUSTOM_MODE' >&2; exit 2; }
  [[ "$CUSTOM_ALGORITHM" == fixed-window || "$CUSTOM_ALGORITHM" == token-bucket ]] || { echo 'invalid CUSTOM_ALGORITHM' >&2; exit 2; }
  [[ "$CUSTOM_INSTANCES" == 1 || "$CUSTOM_INSTANCES" == 2 || "$CUSTOM_INSTANCES" == 4 ]] || { echo 'invalid CUSTOM_INSTANCES' >&2; exit 2; }
  [[ "$CUSTOM_PROFILE" == normal || "$CUSTOM_PROFILE" == mixed || "$CUSTOM_PROFILE" == burst || "$CUSTOM_PROFILE" == concurrent ]] || { echo 'invalid CUSTOM_PROFILE' >&2; exit 2; }
  [[ "$CUSTOM_FAIL_POLICY" == open || "$CUSTOM_FAIL_POLICY" == closed ]] || { echo 'invalid CUSTOM_FAIL_POLICY' >&2; exit 2; }
  for spec in "CUSTOM_RPS 1 1000" "CUSTOM_LEGIT_RPS 0 1000" "CUSTOM_DURATION 3 30" "CUSTOM_LIMIT 1 1000" "CUSTOM_WINDOW_MS 100 9999" "CUSTOM_CAPACITY 1 1000" "CUSTOM_RATE 1 1000" "CUSTOM_BACKEND_CAPACITY 1 100" "CUSTOM_BACKEND_SERVICE_MS 0 1000" "CUSTOM_BURST_START 1 29" "CUSTOM_BURST_DURATION 1 29" "CUSTOM_BURST_RPS 1 1000" "CUSTOM_CONCURRENT_AT 0 29" "CUSTOM_CONCURRENT_COUNT 1 1000"; do
    read -r name low high <<<"$spec"
    valid_int "${!name}" "$low" "$high" || { echo "invalid $name ($low..$high)" >&2; exit 2; }
  done
  (( CUSTOM_LEGIT_RPS <= CUSTOM_RPS )) || { echo 'legitimate RPS exceeds total RPS' >&2; exit 2; }
  [[ "$CUSTOM_MODE" != none || "$CUSTOM_ALGORITHM" == fixed-window ]] || { echo 'algorithm is unused in none mode' >&2; exit 2; }
  [[ "$CUSTOM_FAIL_POLICY" == closed || "$CUSTOM_MODE" == redis ]] || { echo 'fail-open requires Redis mode' >&2; exit 2; }
  if [[ "$CUSTOM_PROFILE" == normal ]]; then
    (( CUSTOM_LEGIT_RPS == CUSTOM_RPS )) || { echo 'normal profile requires all traffic legitimate' >&2; exit 2; }
  elif [[ "$CUSTOM_PROFILE" == burst ]]; then
    (( CUSTOM_BURST_START + CUSTOM_BURST_DURATION <= CUSTOM_DURATION && CUSTOM_BURST_RPS > CUSTOM_RPS - CUSTOM_LEGIT_RPS )) || { echo 'invalid burst interval or RPS' >&2; exit 2; }
  elif [[ "$CUSTOM_PROFILE" == concurrent ]]; then
    (( CUSTOM_CONCURRENT_AT < CUSTOM_DURATION && CUSTOM_LEGIT_RPS == 0 )) || { echo 'concurrent profile requires a batch within duration and zero legitimate RPS' >&2; exit 2; }
  fi
fi
declare -A seen_cases=()
for requested in "${SELECTED[@]}"; do
  [[ -z "${seen_cases[$requested]:-}" ]] || { echo "duplicate case: $requested" >&2; exit 2; }
  seen_cases[$requested]=1
done
if ((RUN_ANALYSIS)) && [[ ! -f "$LAB_ROOT/scripts/analyze.py" ]]; then
  echo 'analyzer unavailable: scripts/analyze.py' >&2; exit 2
fi
command -v flock >/dev/null
mkdir -p "$LAB_ROOT/artifacts"
exec 9>"$LAB_ROOT/artifacts/.research-pilot.lock"
flock -n 9 || { echo 'research pilot already running' >&2; exit 1; }

if [[ -z "$LAB_OUTPUT" ]]; then LAB_OUTPUT="$LAB_ROOT/artifacts/research-pilot-$(date -u +%Y%m%dT%H%M%S)-$$"; fi
[[ ! -e "$LAB_OUTPUT" ]] || { echo "output already exists: $LAB_OUTPUT" >&2; exit 2; }
monitoring_path="$LAB_ROOT/artifacts/monitoring/console-targets/active.json"
if ((MONITORING)); then
  monitoring_dir=$(dirname "$monitoring_path")
  if ! mkdir -p "$monitoring_dir" || [[ ! -O "$monitoring_dir" || ! -r "$monitoring_dir" || ! -w "$monitoring_dir" || ! -x "$monitoring_dir" ]]; then
    echo "monitoring target directory must be owned by this user and readable/writable; see docs/monitoring/RUNBOOK.md#file_sd-directory-permissions" >&2
    exit 1
  fi
fi
mkdir -p "$LAB_OUTPUT"
LAB_OUTPUT=$(cd "$LAB_OUTPUT" && pwd)

compose() { docker compose --project-directory "$LAB_ROOT" -f "$LAB_COMPOSE_FILE" -p "$LAB_PROJECT" "$@"; }
compose_timeout() { local limit=$1; shift; timeout "$limit" docker compose --project-directory "$LAB_ROOT" -f "$LAB_COMPOSE_FILE" -p "$LAB_PROJECT" "$@"; }
monitoring_record=
monitoring_owner=
research_cleanup() {
  local result=$?
  if ((MONITORING)) && [[ -n "$monitoring_record" ]]; then
    python3 "$LAB_ROOT/scripts/console-monitoring.py" remove --path "$monitoring_path" --record "$monitoring_record" --owner "$monitoring_owner" || true
  fi
  lab_cleanup "$result"
}
trap research_cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
command -v docker >/dev/null
command -v curl >/dev/null
command -v timeout >/dev/null
command -v python3 >/dev/null
timeout 10s docker compose version >/dev/null
timeout 10s docker info >/dev/null
existing_containers=$(timeout 10s docker ps -aq --filter "label=com.docker.compose.project=$LAB_PROJECT")
if [[ -n "$existing_containers" ]]; then
  echo "Refusing to modify existing $LAB_PROJECT containers" >&2; exit 1
fi
cd "$LAB_ROOT"
timeout 90s go build -o "$LAB_OUTPUT/loadgen" ./cmd/loadgen
git -C "$LAB_ROOT" rev-parse HEAD >"$LAB_OUTPUT/git-revision.txt"
git -C "$LAB_ROOT" status --porcelain >"$LAB_OUTPUT/git-status.txt"
timeout 10s docker version >"$LAB_OUTPUT/docker-version.txt"
timeout 10s docker compose version >"$LAB_OUTPUT/compose-version.txt"

for case_name in "${SELECTED[@]}"; do
  for ((repeat=1; repeat<=REPETITIONS; repeat++)); do
    case "$case_name" in
      normal) MODE=redis; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=normal; RPS=10; LEGIT_RPS=10 ;;
      burst-fw) MODE=redis; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=burst; RPS=20; LEGIT_RPS=10 ;;
      burst-tb) MODE=redis; ALGORITHM=token-bucket; INSTANCES=2; PROFILE=burst; RPS=20; LEGIT_RPS=10 ;;
      concurrent-local) MODE=local; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=concurrent; RPS=20; LEGIT_RPS=10 ;;
      concurrent-redis) MODE=redis; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=concurrent; RPS=20; LEGIT_RPS=10 ;;
      scale-1) MODE=redis; ALGORITHM=fixed-window; INSTANCES=1; PROFILE=mixed; RPS=100; LEGIT_RPS=20 ;;
      scale-2) MODE=redis; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=100; LEGIT_RPS=20 ;;
      scale-4) MODE=redis; ALGORITHM=fixed-window; INSTANCES=4; PROFILE=mixed; RPS=100; LEGIT_RPS=20 ;;
      mixed-none) MODE=none; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=$MIXED_RPS; LEGIT_RPS=20 ;;
      mixed-local) MODE=local; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=$MIXED_RPS; LEGIT_RPS=20 ;;
      mixed-redis) MODE=redis; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=$MIXED_RPS; LEGIT_RPS=20 ;;
      custom) MODE=$CUSTOM_MODE; ALGORITHM=$CUSTOM_ALGORITHM; INSTANCES=$CUSTOM_INSTANCES; PROFILE=$CUSTOM_PROFILE; RPS=$CUSTOM_RPS; LEGIT_RPS=$CUSTOM_LEGIT_RPS ;;
    esac
    case_dir="$LAB_OUTPUT/$case_name-repeat-$repeat"
    mkdir "$case_dir"
    export MODE ALGORITHM NAMESPACE="research-$(date -u +%Y%m%dT%H%M%S)-$$-$case_name-$repeat"
    FAIL_POLICY=closed
    DURATION=6
    BURST_START=2; BURST_DURATION=2; BURST_RPS=100
    CONCURRENT_AT=2; CONCURRENT_COUNT=100
    if [[ "$case_name" == custom ]]; then
      FAIL_POLICY=$CUSTOM_FAIL_POLICY
      DURATION=$CUSTOM_DURATION
      LIMIT=$CUSTOM_LIMIT WINDOW="${CUSTOM_WINDOW_MS}ms" CAPACITY=$CUSTOM_CAPACITY RATE=$CUSTOM_RATE
      BACKEND_CAPACITY=$CUSTOM_BACKEND_CAPACITY BACKEND_SERVICE_TIME="${CUSTOM_BACKEND_SERVICE_MS}ms"
      BURST_START=$CUSTOM_BURST_START BURST_DURATION=$CUSTOM_BURST_DURATION BURST_RPS=$CUSTOM_BURST_RPS
      CONCURRENT_AT=$CUSTOM_CONCURRENT_AT CONCURRENT_COUNT=$CUSTOM_CONCURRENT_COUNT
      export LIMIT WINDOW CAPACITY RATE BACKEND_CAPACITY BACKEND_SERVICE_TIME
    fi
    export FAIL_POLICY
    # Compose performs interpolation and default resolution before topology generation.
    timeout 15s docker compose --project-directory "$LAB_ROOT" -f "$LAB_ROOT/compose.yaml" -p "$LAB_PROJECT" config --format json >"$case_dir/base-resolved.json"
    topology_args=(--base-config "$case_dir/base-resolved.json" --output "$case_dir/topology" --instances "$INSTANCES" --host-port "$LAB_HOST_PORT" --fresh-state)
    if ((MONITORING)); then topology_args+=(--monitoring); fi
    timeout 10s python3 "$LAB_ROOT/scripts/render-topology.py" "${topology_args[@]}"
    LAB_COMPOSE_FILE="$case_dir/topology/compose.json"
    cp "$case_dir/topology/policy.json" "$case_dir/policy.json"
    compose_timeout 15s config --format json >"$case_dir/compose-resolved.json"
    LAB_OWNED=1
    compose_timeout 180s up -d --build --force-recreate --wait --wait-timeout 120 >"$case_dir/compose-up.log" 2>&1
    compose_timeout 10s ps >"$case_dir/compose-ps.txt"
    compose_timeout 10s images --format json >"$case_dir/images.json"
    python3 - "$case_dir/images.json" "$case_dir/image-inspect.json" <<'PY'
import json, pathlib, subprocess, sys
images = json.loads(pathlib.Path(sys.argv[1]).read_text())
ids = sorted({image['ID'] for image in images})
assert ids, 'no running image identities recorded'
data = subprocess.check_output(['docker', 'image', 'inspect', *ids], timeout=10)
assert {image['Id'] for image in json.loads(data)} == set(ids), 'image inspection identity mismatch'
pathlib.Path(sys.argv[2]).write_bytes(data)
PY
    timeout 10s docker image inspect --format '{{json .RepoDigests}} {{.Id}}' redis:7.4.2-alpine nginx:1.28.0-alpine >"$case_dir/base-image-digests.txt"
    curl --max-time 5 --fail --silent --show-error "http://127.0.0.1:$LAB_HOST_PORT/healthz" >"$case_dir/health-before.json"
    compose_timeout 10s exec -T backend wget -q -O - http://127.0.0.1:8080/metrics >"$case_dir/backend-before.json"
    for ((api=1; api<=INSTANCES; api++)); do
      compose_timeout 10s exec -T "api$api" wget -q -O - http://127.0.0.1:8080/metrics >"$case_dir/api$api-before.json"
    done
    if ((MONITORING)); then
      monitoring_record="$case_dir/monitoring.json"
      monitoring_owner="$(basename "$LAB_OUTPUT")-$case_name-$repeat"
      python3 "$LAB_ROOT/scripts/console-monitoring.py" register --path "$monitoring_path" --record "$monitoring_record" --owner "$monitoring_owner" --instances "$INSTANCES"
      python3 "$LAB_ROOT/scripts/console-monitoring.py" wait --path "$monitoring_path" --record "$monitoring_record" --owner "$monitoring_owner"
    fi
    sleep 1
    lab_sample "$case_dir"
    args=(-target "http://127.0.0.1:$LAB_HOST_PORT/work" -duration "${DURATION}s" -rps "$RPS" -legitimate-rps "$LEGIT_RPS" -legitimate-clients 5 -max-inflight 200 -timeout 2s -run-id "$case_name-repeat-$repeat" -out "$case_dir/load" -mode "$MODE" -algorithm "$ALGORITHM" -fail-policy "$FAIL_POLICY" -profile "$PROFILE")
    if [[ "$PROFILE" == burst ]]; then args+=(-burst-start "${BURST_START}s" -burst-duration "${BURST_DURATION}s" -burst-rps "$BURST_RPS"); fi
    if [[ "$PROFILE" == concurrent ]]; then args+=(-concurrent-at "${CONCURRENT_AT}s" -concurrent-count "$CONCURRENT_COUNT"); fi
    # Console cancels the runner process group; keep timeout and loadgen in that group.
    timeout --foreground "$((DURATION + 15))s" "$LAB_OUTPUT/loadgen" "${args[@]}" >"$case_dir/loadgen.log" 2>&1
    lab_stop_sample
    if ((MONITORING)); then
      read -r load_start load_end drain_end < <(python3 - "$case_dir/load/summary.json" "$case_dir/load/metadata.json" <<'PY'
from datetime import datetime, timedelta
import json, sys
s=json.load(open(sys.argv[1]))
m=json.load(open(sys.argv[2]))
start=datetime.fromisoformat(s['started_at'].replace('Z','+00:00'))
duration=m['config']['duration_ns']
load_end=(start+timedelta(microseconds=duration//1000)).isoformat(timespec='milliseconds').replace('+00:00','Z')
print(s['started_at'], load_end, s['ended_at'])
PY
)
      python3 "$LAB_ROOT/scripts/console-monitoring.py" finish --path "$monitoring_path" --record "$monitoring_record" --owner "$monitoring_owner" --load-start "$load_start" --load-end "$load_end" --drain-end "$drain_end"
      monitoring_record=
      monitoring_owner=
    fi
    compose_timeout 10s exec -T backend wget -q -O - http://127.0.0.1:8080/metrics >"$case_dir/backend-after.json"
    for ((api=1; api<=INSTANCES; api++)); do
      compose_timeout 10s exec -T "api$api" wget -q -O - http://127.0.0.1:8080/metrics >"$case_dir/api$api-after.json"
    done
    compose_timeout 10s logs --no-color >"$case_dir/compose.log"
    if ((RUN_ANALYSIS)); then timeout 20s python3 "$LAB_ROOT/scripts/analyze.py" "$case_dir" >"$case_dir/analyzer.log" 2>&1; fi
    compose_timeout 30s down --remove-orphans >"$case_dir/compose-down.log" 2>&1
    LAB_OWNED=0
    echo "Completed $case_name repeat $repeat"
  done
done
echo "Research pilot artifacts: $LAB_OUTPUT"
