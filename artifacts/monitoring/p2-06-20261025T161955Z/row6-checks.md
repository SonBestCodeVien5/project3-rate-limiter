# Case 6 — mixed / Redis

Run ID: `20261025T164831-642d9b71ee0d`; một submit từ Console UI; trạng thái `completed`. Revision `31bc3389bc3d4a3f21978dde9fb070723ccf56b0`; dirty state do runner ghi `?? .playwright-mcp/`. So với case 5, revision đổi bởi commit tài liệu `docs(context): record root-only final proposal review`; diff chỉ chạm `SESSION_CHECKPOINT.md` và `SOURCE_INDEX.md`, không đổi code/runtime.

## Runner và vòng đời

- Cấu hình gửi: 2 API, Fixed Window Q20/W1s, Redis shared state, fail-closed, backend capacity 4/service 50ms; mixed 120 RPS tổng, 20 legitimate + 100 abusive; duration 30s, monitoring bật, một lần lặp. Loadgen: 5 legitimate client keys, max-inflight 200, timeout 2s, max schedule lag 100ms.
- Summary runner: 3.600 scheduled/sent, 0 generator drops; 905 HTTP 2xx, 2.393 HTTP 429, 302 HTTP 5xx; 0 timeout/transport error; 1.207 backend-confirmed arrivals; 600 legitimate sent, 534 legitimate 2xx. Không retry hoặc thay run.
- Load `16:48:55.074244320Z`–`16:49:25.074Z`; drain `16:49:25.118360485Z`; final scrape API1/API2/backend `16:49:25.937Z`; deregister `16:49:25.939Z`.
- Baseline `16:48:50.033Z`; lookback `16:48:50.034Z`–`16:48:54.037Z`; post-lookback scrape `16:48:54.036Z` cho đủ ba target.
- Owner gỡ manifest; research stack được runner cleanup; lock nhả.

## Monitoring sau cleanup

Grafana URL do runner tạo dùng job `project3-console-run`, rate `4s`, bounds `16:48:55.074Z`–`16:49:25.074Z`. Bấm End để render panel thứ bảy; DOM có đủ 7 panel, bao gồm `API backend errors (/s)` với api1/api2, không alert/query error. Ảnh: [Grafana đủ bảy panel](supplemental/row6-grafana-seven-panels.png).

Loki query allowlist API + `server started` trong load-covering window `16:48:45Z`–`16:49:35Z` trả 0 dòng (HTTP 200, không error). Giữ nguyên kết quả đầu tiên. Query diagnostic chỉ đọc mở rộng `16:48:25Z`–`16:49:40Z`; run `started_at=16:48:31.904475545Z` tới registration `16:48:48.919Z` là cửa sổ case-owned startup/setup. Loki indexed timestamps (`tsNs`) là backend `16:48:38.489722665Z`, API1 `16:48:41.482954829Z`, API2 `16:48:41.509566186Z`; labels project/service/service_name khớp case. Cả required và backend response HTTP 200, không error. Các response được lưu ở `browser-raw/row6-*-response.json`. Ảnh: [Loki backend query](supplemental/row6-loki-backend-query.png). Startup logs thuộc giai đoạn setup trước load; query load-window ban đầu 0 được giữ nguyên.

## Giới hạn thời gian

Bound Grafana `from` và `to` đều `−0.244320 ms` so với load start độ phân giải ns và start + 30s tương ứng. Đây là bounds do runner serialize ở ms; không chỉnh tay. Dashboard evaluation points không phải số raw scrape samples. Kết quả request/latency/goodput chỉ lấy từ runner artifacts.

Raw runner evidence: `artifacts/console/20261025T164831-642d9b71ee0d/`.
