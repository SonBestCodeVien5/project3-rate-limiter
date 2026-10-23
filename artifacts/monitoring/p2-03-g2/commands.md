# Sanitized runtime commands and ordering

Stack config/start (pinned project only):

```sh
docker compose -p project3-monitoring-demo -f compose.yaml -f compose.observability.yaml config -q
docker compose -p project3-monitoring-demo -f compose.yaml -f compose.observability.yaml pull
docker compose -p project3-monitoring-demo -f compose.yaml -f compose.observability.yaml up -d --build --wait
```

Actual `/work` commands were sent sequentially in this order; captured responses and UTC times are in `work-order.json`. Client IDs are preserved.

```sh
curl --fail --silent --show-error --max-time 5 -X POST -H 'X-Client-ID: p203-smoke-1' http://127.0.0.1:18081/work
curl --fail --silent --show-error --max-time 5 -X POST -H 'X-Client-ID: p203-smoke-2' http://127.0.0.1:18081/work
curl --fail --silent --show-error --max-time 5 -X POST -H 'X-Client-ID: p203-smoke-backend' http://127.0.0.1:18083/work
curl --fail --silent --show-error --max-time 5 -X POST -H 'X-Client-ID: p203-smoke-3' http://127.0.0.1:18082/work
curl --fail --silent --show-error --max-time 5 -X POST -H 'X-Client-ID: p203-backend-exact-5' http://127.0.0.1:18083/work
```

Each original attempt had a pre-dispatch ledger write, but the first ledger labels were out of chronological alignment: the entry titled API2 delta preceded an API2 baseline snapshot, then a direct-backend call; the API2 request itself was sent later. The corrected response-time order is above. Total actual `/work` requests is five; restart and UI-only stack starts sent none.

Read-only telemetry commands used `curl http://127.0.0.1:{18081,18082,18083}/metrics`, matching `/metrics/prometheus`, Prometheus `/api/v1/targets`, `/api/v1/query?query=...` for each expression in `promql-results.json`, Grafana `/api/health`, datasource UID and dashboard UID APIs.
