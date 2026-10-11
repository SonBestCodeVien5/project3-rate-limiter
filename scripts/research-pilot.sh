#!/usr/bin/env bash
# Candidate pilot only. Owns a dedicated Compose project and destroys only its own containers.
set -euo pipefail
source "$(dirname "$0")/lab-common.sh"
LAB_PROJECT=project3-research-lab
LAB_COMPOSE_FILE=
LAB_HOST_PORT=${LAB_HOST_PORT:-18080}
REPETITIONS=1
RUN_ANALYSIS=0
SELECTED=()
LAB_OUTPUT=

usage() {
  cat <<'EOF'
Usage: bash scripts/research-pilot.sh [--output NEW_DIR] [--repetitions 1..3]
       [--case NAME]... [--analyze] [--host-port 1024..65535]
Cases: normal, burst-fw, burst-tb, concurrent-local, concurrent-redis,
       scale-1, scale-2, scale-4, mixed-none, mixed-local, mixed-redis.
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
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ "$REPETITIONS" =~ ^[1-3]$ ]] || { echo 'repetitions must be 1..3' >&2; exit 2; }
[[ "$LAB_HOST_PORT" =~ ^[0-9]+$ ]] && (( LAB_HOST_PORT >= 1024 && LAB_HOST_PORT <= 65535 )) || { echo 'invalid host port' >&2; exit 2; }
ALL_CASES=(normal burst-fw burst-tb concurrent-local concurrent-redis scale-1 scale-2 scale-4 mixed-none mixed-local mixed-redis)
if ((${#SELECTED[@]} == 0)); then SELECTED=("${ALL_CASES[@]}"); fi
for requested in "${SELECTED[@]}"; do
  found=0
  for allowed in "${ALL_CASES[@]}"; do [[ "$requested" == "$allowed" ]] && found=1; done
  ((found)) || { echo "unknown case: $requested" >&2; exit 2; }
done
declare -A seen_cases=()
for requested in "${SELECTED[@]}"; do
  [[ -z "${seen_cases[$requested]:-}" ]] || { echo "duplicate case: $requested" >&2; exit 2; }
  seen_cases[$requested]=1
done
if ((RUN_ANALYSIS)) && [[ ! -f "$LAB_ROOT/scripts/analyze.py" ]]; then
  echo 'analyzer unavailable: scripts/analyze.py' >&2; exit 2
fi

if [[ -z "$LAB_OUTPUT" ]]; then LAB_OUTPUT="$LAB_ROOT/artifacts/research-pilot-$(date -u +%Y%m%dT%H%M%S)-$$"; fi
[[ ! -e "$LAB_OUTPUT" ]] || { echo "output already exists: $LAB_OUTPUT" >&2; exit 2; }
mkdir -p "$LAB_OUTPUT"
LAB_OUTPUT=$(cd "$LAB_OUTPUT" && pwd)

compose() { docker compose --project-directory "$LAB_ROOT" -f "$LAB_COMPOSE_FILE" -p "$LAB_PROJECT" "$@"; }
compose_timeout() { local limit=$1; shift; timeout "$limit" docker compose --project-directory "$LAB_ROOT" -f "$LAB_COMPOSE_FILE" -p "$LAB_PROJECT" "$@"; }
trap lab_cleanup EXIT
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
      mixed-none) MODE=none; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=300; LEGIT_RPS=20 ;;
      mixed-local) MODE=local; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=300; LEGIT_RPS=20 ;;
      mixed-redis) MODE=redis; ALGORITHM=fixed-window; INSTANCES=2; PROFILE=mixed; RPS=300; LEGIT_RPS=20 ;;
    esac
    case_dir="$LAB_OUTPUT/$case_name-repeat-$repeat"
    mkdir "$case_dir"
    export MODE ALGORITHM NAMESPACE="research-$(date -u +%Y%m%dT%H%M%S)-$$-$case_name-$repeat"
    export FAIL_POLICY=closed
    # Compose performs interpolation and default resolution before topology generation.
    timeout 15s docker compose --project-directory "$LAB_ROOT" -f "$LAB_ROOT/compose.yaml" -p "$LAB_PROJECT" config --format json >"$case_dir/base-resolved.json"
    timeout 10s python3 "$LAB_ROOT/scripts/render-topology.py" --base-config "$case_dir/base-resolved.json" --output "$case_dir/topology" --instances "$INSTANCES" --host-port "$LAB_HOST_PORT" --fresh-state
    LAB_COMPOSE_FILE="$case_dir/topology/compose.json"
    cp "$case_dir/topology/policy.json" "$case_dir/policy.json"
    compose_timeout 15s config --format json >"$case_dir/compose-resolved.json"
    LAB_OWNED=1
    compose_timeout 180s up -d --build --force-recreate --wait --wait-timeout 120 >"$case_dir/compose-up.log" 2>&1
    compose_timeout 10s ps >"$case_dir/compose-ps.txt"
    compose_timeout 10s images --format json >"$case_dir/images.json"
    timeout 10s docker image inspect --format '{{json .RepoDigests}} {{.Id}}' redis:7.4.2-alpine nginx:1.28.0-alpine >"$case_dir/base-image-digests.txt"
    curl --max-time 5 --fail --silent --show-error "http://127.0.0.1:$LAB_HOST_PORT/healthz" >"$case_dir/health-before.json"
    compose_timeout 10s exec -T backend wget -q -O - http://127.0.0.1:8080/metrics >"$case_dir/backend-before.json"
    for ((api=1; api<=INSTANCES; api++)); do
      compose_timeout 10s exec -T "api$api" wget -q -O - http://127.0.0.1:8080/metrics >"$case_dir/api$api-before.json"
    done
    sleep 1
    lab_sample "$case_dir"
    args=(-target "http://127.0.0.1:$LAB_HOST_PORT/work" -duration 6s -rps "$RPS" -legitimate-rps "$LEGIT_RPS" -legitimate-clients 5 -max-inflight 200 -timeout 2s -run-id "$case_name-repeat-$repeat" -out "$case_dir/load" -mode "$MODE" -algorithm "$ALGORITHM" -fail-policy "$FAIL_POLICY" -profile "$PROFILE")
    if [[ "$PROFILE" == burst ]]; then args+=(-burst-start 2s -burst-duration 2s -burst-rps 100); fi
    if [[ "$PROFILE" == concurrent ]]; then args+=(-concurrent-at 2s -concurrent-count 100); fi
    timeout 20s "$LAB_OUTPUT/loadgen" "${args[@]}" >"$case_dir/loadgen.log" 2>&1
    lab_stop_sample
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
