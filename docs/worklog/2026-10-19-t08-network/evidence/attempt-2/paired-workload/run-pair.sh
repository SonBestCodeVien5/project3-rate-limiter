#!/usr/bin/env bash
set -euo pipefail
root=/tmp/project3-t08-fixed-b
out=/tmp/project3-t08-validation-pair2
project=project3-t08-validation
[[ "$(git -C "$root" rev-parse HEAD)" == b090d2b7391db873a0a2bbe602321ed1f5a55691 ]]
test -z "$(git -C "$root" status --porcelain)"
source "$root/scripts/lab-common.sh"
LAB_PROJECT=$project
LAB_OUTPUT=$out
LAB_OWNED=1
LAB_SAMPLE_PID=
compose() { docker compose --project-directory "$root" -f "$root/compose.yaml" -p "$project" "$@"; }
compose_timeout() { local limit=$1; shift; timeout "$limit" docker compose --project-directory "$root" -f "$root/compose.yaml" -p "$project" "$@"; }
cleanup() { local rc=$?; trap - EXIT; [[ -z "$LAB_SAMPLE_PID" ]] || lab_stop_sample; if [[ "$LAB_OWNED" == 1 ]]; then compose_timeout 30s down --remove-orphans >"$out/compose-down.log" 2>&1 || rc=$?; fi; exit "$rc"; }
trap cleanup EXIT
snapshot() { date -u +%Y-%m-%dT%H:%M:%S.%NZ; compose_timeout 10s exec -T redis redis-cli INFO stats; }
printf '%s\n' 'Sampler off:' '/tmp/project3-t08-loadgen-b -target http://127.0.0.1:8080/work -duration 10s -rps 20 -legitimate-rps 20 -legitimate-clients 5 -max-inflight 100 -timeout 2s -run-id t08-sampler-off -out <OUT>/load-off -mode redis -algorithm fixed-window -fail-policy closed -profile normal' 'Sampler on: same flags with run-id t08-sampler-on and out <OUT>/load-on' > "$out/workload-command.txt"
curl --max-time 5 --fail --silent --show-error http://127.0.0.1:18083/metrics >"$out/backend-before.json"
compose_timeout 10s exec -T api1 wget -q -O - http://127.0.0.1:8080/metrics >"$out/api1-before.txt"
compose_timeout 10s exec -T api2 wget -q -O - http://127.0.0.1:8080/metrics >"$out/api2-before.txt"
snapshot >"$out/off-before.log"
timeout 30s /tmp/project3-t08-loadgen-b -target http://127.0.0.1:8080/work -duration 10s -rps 20 -legitimate-rps 20 -legitimate-clients 5 -max-inflight 100 -timeout 2s -run-id t08-sampler-off -out "$out/load-off" -mode redis -algorithm fixed-window -fail-policy closed -profile normal >"$out/load-off.log" 2>&1
snapshot >"$out/off-after.log"
mkdir -p "$out/sampler-on"
lab_sample "$out/sampler-on"
for i in $(seq 1 600); do
  if rg -q '^total_net_output_bytes:' "$out/sampler-on/redis-resources.log"; then break; fi
  sleep .01
done
kill -0 "$LAB_SAMPLE_PID"
rg -q '^total_net_input_bytes:' "$out/sampler-on/redis-resources.log"
rg -q '^total_net_output_bytes:' "$out/sampler-on/redis-resources.log"
printf '%s\n' "$LAB_SAMPLE_PID" >"$out/sampler-on/pid-before-load.txt"
snapshot >"$out/on-before.log"
kill -0 "$LAB_SAMPLE_PID"
timeout 30s /tmp/project3-t08-loadgen-b -target http://127.0.0.1:8080/work -duration 10s -rps 20 -legitimate-rps 20 -legitimate-clients 5 -max-inflight 100 -timeout 2s -run-id t08-sampler-on -out "$out/load-on" -mode redis -algorithm fixed-window -fail-policy closed -profile normal >"$out/load-on.log" 2>&1
lab_stop_sample
LAB_SAMPLE_PID=
snapshot >"$out/on-after.log"
curl --max-time 5 --fail --silent --show-error http://127.0.0.1:18083/metrics >"$out/backend-after.json"
compose_timeout 10s exec -T api1 wget -q -O - http://127.0.0.1:8080/metrics >"$out/api1-after.txt"
compose_timeout 10s exec -T api2 wget -q -O - http://127.0.0.1:8080/metrics >"$out/api2-after.txt"
compose_timeout 10s images --format json >"$out/images.json"
echo 'matched workload pair completed'
