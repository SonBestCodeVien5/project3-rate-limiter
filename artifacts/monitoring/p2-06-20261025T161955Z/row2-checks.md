# Case 2 — normal / local

Run ID: `20261025T162826-777671c4739c`. Submit một lần qua Console UI, trạng thái cuối `completed`. Source revision `c623a305731b3d9ec3efd2890d11e0b913f622bf`; working tree trong runner ghi `?? .playwright-mcp/` (output browser của phiên).

## Runner và vòng đời

- Cấu hình hiệu lực: 2 API; Fixed Window Q20/W1s; backend capacity 4/service 50ms; normal 20 RPS, 20 RPS legitimate; 5 legitimate client keys; loadgen max-inflight 200, timeout 2s, max schedule lag 100ms; 30s; repeat 1; mode local/fail-closed.
- Runner summary: 600 scheduled/sent, 0 dropped; 600 HTTP 2xx; 0 HTTP 429/5xx, timeout hoặc transport error; 600 backend-confirmed arrivals.
- Load UTC `2026-10-25T16:28:51.425343854Z`–`16:29:21.425Z`; drain `16:29:21.430002140Z`; final scrape API1/API2/backend `16:29:21.741Z`; deregistration `16:29:21.744Z`.
- Target baseline `16:28:46.362Z`; lookback `16:28:46.363Z`–`16:28:50.368Z`; post-lookback target scrape `16:28:50.366Z`.
- Runner completed owner-scoped manifest removal and cleanup; no research container remained.

## Monitoring sau cleanup

Grafana mở job `project3-console-run`, rate `4s`, load bounds `16:28:51.425Z`–`16:29:21.425Z` (browser timezone Asia/Bangkok); bảy panel render, API1/API2/backend target series và workload metric series thấy được, không có alert/query error. Ảnh: [dashboard](screenshots/row2-grafana-dashboard.png). Dữ liệu xem được sau cleanup; panel resolution là evaluation points của query, không phải raw scrape count.

Loki Explore query `{project="project3-research-lab",service=~"api1|api2|backend"} |= "server started"` trong `16:28:30Z`–`16:29:30Z` trả 3 dòng startup JSON, labels project/service/service_name ổn định; retained sau cleanup. Config backend JSON xác nhận capacity 4/service 50ms. Ảnh: [Loki startup](screenshots/row2-loki-startup.png).

## Verdict case

Case 2 đạt tiêu chí kỹ thuật riêng: runner artifacts, targets/baseline/final scrape, Grafana job/range, Loki startup JSON và dữ liệu retained sau cleanup. Chưa suy quota correctness. Suite vẫn pending bốn case.

Runner artifacts raw được giữ nguyên tại `artifacts/console/20261025T162826-777671c4739c/`.
