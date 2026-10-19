#!/usr/bin/env bash
# Source-only helpers. Destructive lifecycle operations are scoped to a new lab project.
set -euo pipefail
LAB_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LAB_PROJECT=project3-lab
LAB_OWNED=0
LAB_PAUSED=0
LAB_LOAD_PID=
LAB_SAMPLE_PID=

compose() { docker compose --project-directory "$LAB_ROOT" -f "$LAB_ROOT/compose.yaml" -p "$LAB_PROJECT" "$@"; }
compose_timeout() { local limit=$1; shift; timeout "$limit" docker compose --project-directory "$LAB_ROOT" -f "$LAB_ROOT/compose.yaml" -p "$LAB_PROJECT" "$@"; }
lab_cleanup() {
  local result=$?
  trap - EXIT INT TERM
  if [[ -n "$LAB_SAMPLE_PID" ]]; then kill "$LAB_SAMPLE_PID" 2>/dev/null || true; wait "$LAB_SAMPLE_PID" 2>/dev/null || true; fi
  if [[ "$LAB_PAUSED" == 1 ]]; then compose_timeout 10s unpause redis >/dev/null 2>&1 || true; fi
  if [[ -n "$LAB_LOAD_PID" ]]; then kill -TERM "$LAB_LOAD_PID" 2>/dev/null || true; wait "$LAB_LOAD_PID" 2>/dev/null || true; fi
  if [[ "$LAB_OWNED" == 1 ]]; then compose_timeout 30s down --remove-orphans >/dev/null 2>&1 || true; fi
  exit "$result"
}
lab_prepare() {
  command -v docker >/dev/null
  command -v curl >/dev/null
  command -v timeout >/dev/null
  docker compose version >/dev/null
  docker info >/dev/null
  if [[ -n "$(compose ps -aq)" ]]; then
    echo "Refusing to modify existing $LAB_PROJECT containers. Stop that project explicitly before this pilot." >&2
    return 1
  fi
  trap lab_cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  LAB_OWNED=1
  mkdir -p "$LAB_OUTPUT"
  (cd "$LAB_ROOT" && go build -o "$LAB_OUTPUT/loadgen" ./cmd/loadgen)
  docker version >"$LAB_OUTPUT/docker-version.txt"
  docker compose version >"$LAB_OUTPUT/compose-version.txt"
}
lab_start() {
  local case_dir=$1
  mkdir -p "$case_dir"
  compose config >"$case_dir/compose-resolved.yaml"
  compose up -d --build --force-recreate --wait --wait-timeout 120 >"$case_dir/compose-up.log" 2>&1
  compose ps >"$case_dir/compose-ps.txt"
  curl --max-time 5 --fail --silent --show-error http://localhost:18083/metrics >"$case_dir/backend-before.json"
}
lab_snapshot() {
  local case_dir=$1
  curl --max-time 5 --fail --silent --show-error http://localhost:18083/metrics >"$case_dir/backend-after.json"
  curl --max-time 5 --fail --silent --show-error http://localhost:18081/metrics >"$case_dir/api1-after.json"
  curl --max-time 5 --fail --silent --show-error http://localhost:18082/metrics >"$case_dir/api2-after.json"
  compose_timeout 10s logs --no-color >"$case_dir/compose.log"
}
lab_sample() {
  local case_dir=$1
  # No Redis INFO during pause: a blocked redis-cli would obscure outage timing.
  (
    local stop=0
    trap 'stop=1' TERM
    while [[ "$stop" == 0 ]]; do
      date -u +%Y-%m-%dT%H:%M:%S.%NZ
      compose_timeout 5s exec -T redis redis-cli INFO cpu
      compose_timeout 5s exec -T redis redis-cli INFO memory
      compose_timeout 5s exec -T redis redis-cli INFO stats
      [[ "$stop" == 1 ]] || sleep 1
    done
  ) >"$case_dir/redis-resources.log" 2>&1 &
  LAB_SAMPLE_PID=$!
}
lab_stop_sample() {
  if [[ -n "$LAB_SAMPLE_PID" ]]; then kill "$LAB_SAMPLE_PID" 2>/dev/null || true; wait "$LAB_SAMPLE_PID" 2>/dev/null || true; LAB_SAMPLE_PID=; fi
}
