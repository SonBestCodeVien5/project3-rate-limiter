# Lệnh và thao tác — P2-03A

## Kiểm tra ban đầu

```bash
git status --short
git rev-parse HEAD
docker ps -a --filter label=com.docker.compose.project=project3-monitoring-demo --format '{{.ID}} {{.Names}} {{.Status}}'
docker ps -a --filter label=com.docker.compose.project=project3-research-lab --format '{{.ID}} {{.Names}} {{.Status}}'
docker volume inspect project3-monitoring-demo_grafana-data project3-monitoring-demo_prometheus-data --format '{{.Name}} {{json .Labels}}'
docker version --format '{{.Client.Version}} {{.Server.Version}}'
docker compose version
ss -ltnp
stat -c '%a %n' .secrets .secrets/grafana_admin_password
```

Docker và `ss` không truy cập được trong sandbox ban đầu; kiểm tra read-only qua escalation đã thành công. Không có container thuộc hai project hoặc Console/loadgen đang chạy. Các cổng cần dùng trống. Hai named volumes monitoring đã tồn tại; credential local đã tồn tại và không đọc ra chat/evidence. Không sửa/xóa tài nguyên ở bước này.

G1/G2/G3 và các lỗi/kiểm tra tiếp theo được bổ sung trong evidence sau khi thực hiện; phần này không chứng minh runtime acceptance.

## G1 và sửa lỗi do Luna kiểm tra

Các lệnh focused đã được worker thực hiện theo các revision trong `checks.md`: `python3 scripts/test_topology.py`, `python3 scripts/test_console_monitoring.py`, `bash -n scripts/research-pilot.sh scripts/lab-common.sh`, `GOCACHE=/tmp/p2-03a-go-cache go test ./internal/console`, `node internal/console/index_test.js`, `bash scripts/test-scripts.sh`, Python compile, YAML/JSON/UID/local-link checks, Compose resolve và `git diff --check`. Root không lặp lại suite.

## G2/G3 runtime

- Worker dựng monitoring bằng base+overlay đúng project; reuse `.secrets/grafana_admin_password`, không in secret. MCP browser login echo credential trong tool output; MCP sau đó stalled, root chuyển local browser.
- Local scripts được lưu cùng evidence. Chạy `timeout 75s node /tmp/p2-03a-browser-check.cjs` để login kín/list/folder/Console form; `timeout 55s node /tmp/p2-03a-render.cjs` kiểm tra panels/query. Hai lần đầu timeout selector trước submit; lần sau pass.
- `docker compose -p project3-monitoring-demo -f compose.yaml -f compose.observability.yaml up -d --no-build --wait api1 api2 backend prometheus`; `exec -T prometheus promtool check config /etc/prometheus/prometheus.yml`; `kill -s HUP prometheus` để reload config.
- **Một lần duy nhất** `timeout 330s node /tmp/p2-03a-g3.cjs`: script điền form, validate POST thực, lưu attempt trước click, bấm `#run`, rồi chỉ GET trạng thái/targets/queries. HTTP201, sau đó registration failure trước loadgen. Không chạy lại script này.
- `stat` xác minh target dir owner65534, runner1000. Sửa đúng thư mục bằng helper container tự xóa: `docker run --rm --user 0 --label project3.task=p2-03a-permission-repair --mount "type=bind,src=$PWD/artifacts/monitoring/console-targets,dst=/targets" --entrypoint /bin/sh prom/prometheus:v3.15.0 -c 'chown 1000:1000 /targets && chmod 755 /targets'`. Không mount/xóa volume.
- G2 gọi helper register/remove với query mock, tên `.permission-check` ngoài glob `*.json`; `docker exec project3-monitoring-demo-prometheus-1 test -r /etc/prometheus/console-targets/.permission-check` pass. Không đăng ký target hoặc chạy load.
- Nginx reload trung gian lỗi DNS; sau sửa network dùng `up -d --no-build --force-recreate --wait --wait-timeout 60 api1 api2 backend nginx`. Final all healthy.
- Chỉ GET `/healthz`, `/metrics`, `/metrics/prometheus`, Console APIs và Prometheus/Grafana queries. Docker inspect evidence chỉ chọn IDs/digests/network/status, bỏ Env/credentials. Commands/config actual ở các JSON/log đã chọn.
