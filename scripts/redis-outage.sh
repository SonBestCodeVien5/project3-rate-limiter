#!/usr/bin/env bash
# Bounded Redis pause pilot with a matched healthy calibration per fail policy.
set -euo pipefail
LAB_ROOT=$(cd "$(dirname "$0")/.." && pwd)
PROJECT=project3-outage-$$
PORT=${OUTAGE_HOST_PORT:-18080}
OUT=${1:-"$LAB_ROOT/artifacts/outage-$(date -u +%Y%m%dT%H%M%S)-$$"}
[[ ! -e "$OUT" ]] || { echo "Output already exists: $OUT" >&2; exit 2; }
mkdir -p "$(dirname "$OUT")"
mkdir "$OUT"
OUT=$(cd "$OUT" && pwd)
OWNED=0 PAUSED=0 LOAD_PID=
compose() { timeout "${1:-10s}" docker compose --project-directory "$LAB_ROOT" -f "$CASE_DIR/topology/compose.json" -p "$PROJECT" "${@:2}"; }
cleanup() {
  local rc=$?; trap - EXIT INT TERM
  [[ -z "$LOAD_PID" ]] || { kill -TERM "$LOAD_PID" 2>/dev/null || true; wait "$LOAD_PID" 2>/dev/null || true; }
  if ((PAUSED)); then compose 10s unpause redis >/dev/null 2>&1 || true; fi
  if ((OWNED)); then compose 30s down --remove-orphans >/dev/null 2>&1 || true; fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
command -v docker >/dev/null; command -v curl >/dev/null; command -v timeout >/dev/null; command -v python3 >/dev/null
docker compose version >/dev/null
docker info >/dev/null
[[ -z "$(docker ps -aq --filter "label=com.docker.compose.project=$PROJECT")" ]] || { echo "Project collision: $PROJECT" >&2; exit 1; }
git -C "$LAB_ROOT" rev-parse HEAD >"$OUT/git-revision.txt"
git -C "$LAB_ROOT" status --porcelain >"$OUT/git-status.txt"
go -C "$LAB_ROOT" build -o "$OUT/loadgen" ./cmd/loadgen
duration=${OUTAGE_DURATION:-25}; rps=${OUTAGE_RPS:-100}; legit=${OUTAGE_LEGIT_RPS:-20}; pause_at=${OUTAGE_PAUSE_AT:-4}; pause_for=${OUTAGE_PAUSE_FOR:-2}
[[ $duration =~ ^[0-9]+$ && $rps =~ ^[0-9]+$ && $legit =~ ^[0-9]+$ && $pause_at =~ ^[0-9]+$ && $pause_for =~ ^[0-9]+$ ]] || { echo 'duration/rates/pause values must be integers' >&2; exit 2; }
(( duration >= pause_at + pause_for + 5 && legit >= 5 && rps >= legit )) || { echo 'Need >=5s post-outage, >=5 legitimate RPS, and total RPS >= legitimate RPS' >&2; exit 2; }
algo=${ALGORITHM:-fixed-window}; limit=${LIMIT:-20}; window=${WINDOW:-1s}; capacity=${CAPACITY:-20}; rate=${RATE:-20}; backend=${BACKEND_CAPACITY:-10}; service=${BACKEND_SERVICE_TIME:-50ms}

for policy in open closed; do
  for phase in healthy outage; do
    CASE_DIR="$OUT/$policy/$phase"; mkdir -p "$CASE_DIR"
    export MODE=redis ALGORITHM="$algo" FAIL_POLICY="$policy" NAMESPACE="outage-$$-$policy-$phase" LIMIT="$limit" WINDOW="$window" CAPACITY="$capacity" RATE="$rate" BACKEND_CAPACITY="$backend" BACKEND_SERVICE_TIME="$service"
    cp "$OUT/git-revision.txt" "$OUT/git-status.txt" "$OUT/$policy/"
    timeout 15s docker compose --project-directory "$LAB_ROOT" -f "$LAB_ROOT/compose.yaml" -p "$PROJECT" config --format json >"$CASE_DIR/base-resolved.json"
    python3 "$LAB_ROOT/scripts/render-topology.py" --base-config "$CASE_DIR/base-resolved.json" --output "$CASE_DIR/topology" --instances 2 --host-port "$PORT" --fresh-state
    cp "$CASE_DIR/topology/policy.json" "$CASE_DIR/policy.json"
    compose 15s config --format json >"$CASE_DIR/compose-resolved.json"
    OWNED=1
    compose 180s up -d --build --force-recreate --wait --wait-timeout 120 >"$CASE_DIR/compose-up.log" 2>&1
    compose 10s ps >"$CASE_DIR/compose-ps.txt"
    compose 10s images --format json >"$CASE_DIR/images.json"
    python3 - "$CASE_DIR/images.json" "$CASE_DIR/image-inspect.json" <<'PY'
import json, pathlib, subprocess, sys
ids = sorted({x['ID'] for x in json.loads(pathlib.Path(sys.argv[1]).read_text())})
assert ids, 'no image identities recorded'
data = subprocess.check_output(['docker', 'image', 'inspect', *ids], timeout=10)
assert {x['Id'] for x in json.loads(data)} == set(ids)
pathlib.Path(sys.argv[2]).write_bytes(data)
PY
    timeout 10s docker image inspect --format '{{json .RepoDigests}} {{.Id}}' redis:7.4.2-alpine nginx:1.28.0-alpine >"$CASE_DIR/base-image-digests.txt"
    for service_name in backend api1 api2; do compose 10s exec -T "$service_name" wget -q -O - http://127.0.0.1:8080/metrics >"$CASE_DIR/$service_name-before.json"; done
    if [[ $phase == healthy ]]; then load_duration=$duration; else load_duration=$duration; fi
    run_id="t07-$(date -u +%Y%m%dT%H%M%S)-$$-$policy-$phase"
    args=(-target "http://127.0.0.1:$PORT/work" -duration "${load_duration}s" -rps "$rps" -legitimate-rps "$legit" -legitimate-clients 5 -max-inflight 200 -timeout 2s -run-id "$run_id" -out "$CASE_DIR/load" -mode redis -algorithm "$algo" -fail-policy "$policy")
    timeout "$((duration + 20))s" "$OUT/loadgen" "${args[@]}" >"$CASE_DIR/loadgen.log" 2>&1 & LOAD_PID=$!
    for attempt in {1..200}; do [[ -f "$CASE_DIR/load/metadata.json" ]] && break; kill -0 "$LOAD_PID" 2>/dev/null || { wait "$LOAD_PID"; LOAD_PID=; exit 1; }; sleep .05; done
    [[ -f "$CASE_DIR/load/metadata.json" ]] || { echo 'Loadgen did not start' >&2; exit 1; }
    if [[ $phase == outage ]]; then
      sleep "$pause_at"
      printf '%s pause_requested\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$CASE_DIR/outage-events.txt"
      PAUSED=1; compose 10s pause redis >>"$CASE_DIR/outage-events.txt" 2>&1
      printf '%s pause_completed\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$CASE_DIR/outage-events.txt"
      sleep "$pause_for"
      printf '%s unpause_requested\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$CASE_DIR/outage-events.txt"
      compose 10s unpause redis >>"$CASE_DIR/outage-events.txt" 2>&1; PAUSED=0
      printf '%s unpause_completed\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)" >>"$CASE_DIR/outage-events.txt"
    fi
    if ! wait "$LOAD_PID"; then echo "Load generator failed in $CASE_DIR" >&2; LOAD_PID=; exit 1; fi
    LOAD_PID=
    for service_name in backend api1 api2; do compose 10s exec -T "$service_name" wget -q -O - http://127.0.0.1:8080/metrics >"$CASE_DIR/$service_name-after.json"; done
    compose 10s logs --no-color >"$CASE_DIR/compose.log"
    compose 30s down --remove-orphans >"$CASE_DIR/compose-down.log"; OWNED=0
    if [[ $phase == healthy ]]; then
      python3 - "$CASE_DIR" <<'PY'
import json, sys
from pathlib import Path
case=Path(sys.argv[1])
summary=json.loads((case/'load/summary.json').read_text())
rows=[json.loads(line) for line in (case/'load/requests.jsonl').read_text().splitlines() if line]
legit=[r for r in rows if r.get('client_class')=='legitimate' and r.get('sent_at')]
legit_ok=[r for r in legit if not r.get('error') and not r.get('timeout') and 200 <= (r.get('status') or 0) < 300]
transport=sum(bool(r.get('error')) or bool(r.get('timeout')) for r in rows if r.get('sent_at'))
limiter=sum(bool(r.get('limiter_error')) for r in rows if r.get('sent_at'))
backend=json.loads((case/'backend-before.json').read_text())
after=json.loads((case/'backend-after.json').read_text())
api=[]
for name in ('api1','api2'):
    before=json.loads((case/f'{name}-before.json').read_text())
    end=json.loads((case/f'{name}-after.json').read_text())
    api.append(end['limiter_errors']-before['limiter_errors'])
overload=after['overload']-backend['overload']
if len(legit) != len(legit_ok) or summary.get('generator_dropped') != 0 or transport or limiter or any(api) or overload:
    raise SystemExit('healthy baseline gate failed: require all legitimate successes and zero generator drops, transport/limiter errors, and backend overload')
PY
      threshold=$(python3 - "$CASE_DIR/load/requests.jsonl" <<'PY'
import json, math, pathlib, sys
v=[x['latency_ms'] for x in map(json.loads,pathlib.Path(sys.argv[1]).open()) if x.get('client_class')=='legitimate' and x.get('sent_at') and 200 <= (x.get('status') or 0) < 300]
if len(v)<5: raise SystemExit('healthy calibration has fewer than five successful legitimate samples')
v.sort(); p95=v[math.ceil(.95*len(v))-1]; print(max(1,1.5*p95))
PY
      )
      printf '%s\n' "$threshold" >"$OUT/$policy/recovery-p95-threshold-ms.txt"
    fi
  done
  threshold=$(cat "$OUT/$policy/recovery-p95-threshold-ms.txt")
  timeout 20s python3 "$LAB_ROOT/scripts/analyze.py" "$OUT/$policy/outage" --recovery-p95-ms "$threshold" --recovery-window-ms 1000 --recovery-min-samples 5 --recovery-consecutive 3 >"$OUT/$policy/outage/analyzer.log" 2>&1
done
echo "Outage artifacts: $OUT"
