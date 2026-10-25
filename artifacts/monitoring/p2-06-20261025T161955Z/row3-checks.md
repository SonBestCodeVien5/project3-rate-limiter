# Case 3 — normal / Redis

Run ID: `20261025T163206-aabcac391d9b`. Một lần submit qua Console UI, `completed`. Source revision `c623a305731b3d9ec3efd2890d11e0b913f622bf`; runner ghi dirty status `?? .playwright-mcp/` (capture browser của phiên).

## Runner và vòng đời

- Cấu hình hiệu lực: 2 API; Redis shared state; Fixed Window Q20/W1s; fail-closed; backend capacity 4/service 50ms; normal 20 RPS, toàn legitimate; 5 legitimate clients; max-inflight 200; timeout 2s; max schedule lag 100ms; 30s; repeat 1.
- Runner summary: 600 scheduled/sent, 0 dropped; 600 HTTP 2xx; 0 HTTP 429/5xx, timeout hoặc transport errors; 600 backend-confirmed arrivals.
- Load start `2026-10-25T16:32:31.419556862Z`; end theo duration `16:33:01.419Z`; drain `16:33:01.424911262Z`; final scrape API1/API2/backend `16:33:02.248Z`; deregistration `16:33:02.250Z`.
- Baseline scrape `16:32:26.367Z`, lookback `16:32:26.368Z`–`16:32:30.372Z`, post-lookback `16:32:30.370Z`.
- Owner gỡ registration, runner cleanup xong; lock rảnh, không còn research containers.

## Metrics/logs sau cleanup

Grafana retained data có job `project3-console-run`, rate `4s`, load range `16:32:31.420Z`–`16:33:01.419Z`. Ảnh overview riêng row3 cho thấy 6 panel: [ảnh row3 sáu panel](supplemental/row3-grafana-six-panels.png). Ảnh từng được gán tên `supplemental/row3-grafana-panel7.png` thực ra trùng byte với panel7 row2 và không dùng làm bằng chứng row3; xem [hiệu chỉnh provenance](panel7-correction.md).

Sau đó, trong phiên read-only được root cho phép, mở đúng runner URL trên hai container Prometheus/Grafana hiện hữu và bấm End. DOM có panel `API backend errors (/s)` với series api1/api2. Query panel7 HTTP 200, 2 series × 3 evaluation points, mọi giá trị là 0; screenshot đúng range/panel được lưu [tại đây](supplemental/row3-grafana-panel7-corrected.png), response raw và bảng sanitized ở `browser-raw/row3-panel7-response.json` và `row3-panel7-verification.json`. Không có workload, registration mới hay thay đổi config.

Loki Explore sau cleanup, `{project="project3-research-lab",service=~"api1|api2|backend"} |= "server started"`, range `16:32:15Z`–`16:33:10Z`, trả 3 dòng startup JSON; labels `project`, `service`, `service_name`; log backend cho thấy capacity 4/service 50ms. [Ảnh query](supplemental/row3-loki-startup.png).

Case đạt tiêu chí runtime và bảy panel sau lần xác minh retained-data này; không kết luận quota correctness. Raw runner artifacts giữ tại `artifacts/console/20261025T163206-aabcac391d9b/`.
