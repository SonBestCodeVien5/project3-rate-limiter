#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
unformatted=$(gofmt -l cmd internal)
if [[ -n "$unformatted" ]]; then printf 'Go files need gofmt:\n%s\n' "$unformatted" >&2; exit 1; fi
go vet ./...
go test -race ./...
go build ./...
for script in scripts/*.sh; do bash -n "$script"; done
bash scripts/test-scripts.sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_topology.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_redis_outage.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_analyze.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_report_study.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_plot_calibration.py
if command -v node >/dev/null; then node internal/console/index_test.js; fi
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
  docker compose -f compose.yaml -p project3-lab config --quiet
fi
