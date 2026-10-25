# Case 5 — mixed / local

Run ID: `20261025T164349-295d3f8931d4`; một submit từ Console UI; trạng thái `completed`. Revision `c623a305731b3d9ec3efd2890d11e0b913f622bf`; dirty state do runner ghi `?? .playwright-mcp/`.

## Runner và vòng đời

- Cấu hình gửi: 2 API, Fixed Window Q20/W1s, local state, fail-closed, backend capacity 4/service 50ms; mixed 120 RPS tổng, 20 legitimate + 100 abusive; duration 30s, monitoring bật, một lần lặp. Loadgen: 5 legitimate client keys, max-inflight 200, timeout 2s, max schedule lag 100ms.
- Summary runner: 3.600 scheduled; 3.599 sent; 1 generator drop do `schedule_backlog`; 1.223 HTTP 2xx, 1.759 HTTP 429, 617 HTTP 5xx; 0 timeout/transport error; 1.840 backend-confirmed arrivals; 600 legitimate sent, 472 legitimate 2xx. Không retry hoặc thay run.
- Load `16:44:15.568711567Z`–`16:44:45.568Z`; drain `16:44:45.572869054Z`; final scrape API1/API2/backend `16:44:45.985Z`; deregister `16:44:45.989Z`.
- Baseline `16:44:10.494Z`; lookback `16:44:10.496Z`–`16:44:14.501Z`; post-lookback scrape `16:44:14.499Z` cho đủ ba target.
- Owner gỡ manifest; research stack được runner cleanup; lock nhả.

## Monitoring sau cleanup

Grafana URL do runner tạo dùng job `project3-console-run`, rate `4s`, bounds `16:44:15.569Z`–`16:44:45.568Z`. Bấm End để render panel thứ bảy; DOM có đủ 7 panel, bao gồm `API backend errors (/s)` với api1/api2, không alert/query error. Ảnh: [Grafana đủ bảy panel](supplemental/row5-grafana-seven-panels.png).

Loki query allowlist API + `server started` trong query load-covering ban đầu (`16:44:10Z`–`16:45:10Z`) trả 0 dòng (HTTP 200, không error). Giữ nguyên kết quả đầu tiên. Query chẩn đoán read-only thực tế có bounds `16:37:05Z`–`16:45:10Z` (Grafana UI hiển thị Bangkok `23:37:05`–`23:45:10`); dùng runner `started_at=16:43:49.051886569Z` tới target registration `16:44:09.374Z` làm cửa sổ case-owned startup/setup. Trong response rộng, API1 `16:44:01.329644533Z`, API2 `16:44:01.301416003Z`, backend `16:43:58.340153565Z` đều thuộc cửa sổ setup của row5. Backend row `16:38:51.076884396Z` thuộc lượt trước, được loại khỏi số liệu row5; đây là Loki indexed `tsNs`, embedded event time là `16:38:51.076195341Z`, đều trước run. Các dòng thuộc row5 là JSON startup, labels project/service/service_name khớp; status 200, không error. Query ban đầu 0 vẫn được báo rõ, không thay thế bằng số startup lines. Bảng timestamp/labels đã sanitize ở `loki-startup-ownership.json`; response thô ở `browser-raw/row5-*-response.json`; ảnh query backend broad (gồm cả row cũ bị loại): [Loki](supplemental/row5-loki-backend-query.png).

## Giới hạn thời gian

Bound Grafana `from` là `+0.288433 ms` so với load start độ phân giải ns; `to` là `−0.711567 ms` so với start + 30s. Đây là bounds do runner serialize ở ms; không chỉnh tay. Dashboard evaluation points không phải số raw scrape samples. Kết quả request/latency/goodput chỉ lấy từ runner artifacts.

Raw runner evidence: `artifacts/console/20261025T164349-295d3f8931d4/`.
