#!/usr/bin/env bash
set -u
export GOCACHE=/tmp/project3-review-go-cache CUSTOM_DURATION=6 CUSTOM_RPS=120 CUSTOM_LEGIT_RPS=20 CUSTOM_LIMIT=20 CUSTOM_WINDOW_MS=1000 CUSTOM_CAPACITY=20 CUSTOM_RATE=20 CUSTOM_BACKEND_SERVICE_MS=50 CUSTOM_FAIL_POLICY=closed CUSTOM_BURST_START=1 CUSTOM_BURST_DURATION=1 CUSTOM_BURST_RPS=200
run() { local label=$1; bash scripts/research-pilot.sh --case custom --repetitions 2 --analyze --output "artifacts/calibration-20261013/$label" >"artifacts/calibration-20261013/$label-runner.log" 2>&1; local result=$?; echo "$label $result"; }
export CUSTOM_MODE=local CUSTOM_ALGORITHM=token-bucket CUSTOM_INSTANCES=2 CUSTOM_PROFILE=mixed CUSTOM_BACKEND_CAPACITY=10
run tb-mixed2
export CUSTOM_INSTANCES=1 CUSTOM_PROFILE=burst
run tb-burst1
export CUSTOM_MODE=redis CUSTOM_ALGORITHM=fixed-window CUSTOM_INSTANCES=2 CUSTOM_PROFILE=normal CUSTOM_BACKEND_CAPACITY=4 CUSTOM_RPS=20 CUSTOM_LEGIT_RPS=20
run normal-redis
export CUSTOM_PROFILE=mixed CUSTOM_RPS=120
for mode in none local redis; do export CUSTOM_MODE=$mode; run "mixed-$mode"; done
