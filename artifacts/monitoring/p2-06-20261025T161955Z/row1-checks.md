# Case 1 — normal / none

Run ID: `20261025T162327-4e8d83985f96`. Submit được một lần qua Console **Chạy benchmark**, custom, normal, mode none, monitoring bật; Console trả `completed`. Source revision `c623a305731b3d9ec3efd2890d11e0b913f622bf`; trạng thái working tree trong runner ghi `?? .playwright-mcp/` do output Playwright trong phiên. Runtime topology/policy và image identity nằm trong artifact runner.

## Runner và vòng đời

- Cấu hình loadgen: 2 API; Fixed Window, Q20/W1s; backend capacity 4/service 50ms; normal 20 RPS, toàn bộ hợp lệ; 5 legitimate clients; max-inflight 200; timeout 2s; max schedule lag 100ms; 30s; repetition 1.
- Runner summary: 600 scheduled/sent, 0 dropped; 600 HTTP 2xx; 0 HTTP 429/5xx, timeout hoặc transport error; 600 backend-confirmed arrivals. Các con số này lấy từ `load/summary.json`, không suy từ dashboard.
- Load UTC: `2026-10-25T16:23:53.539147045Z` đến `2026-10-25T16:24:23.539Z`; generator drain `16:24:23.544560821Z`; final scrape API1/API2/backend `16:24:24.256Z`; deregistration `16:24:24.259Z`.
- Trước tải: target API1/API2/backend đã UP, baseline scrape `16:23:48.498Z`; lookback `16:23:48.500Z`–`16:23:52.503Z`, post-lookback scrape `16:23:52.502Z`.
- Cleanup: monitoring record hoàn tất, manifest bị gỡ bởi owner; runner dọn research project riêng; sau run không còn research container. Lock được nhả.

## Monitoring sau cleanup

Grafana dashboard hiển thị đúng job `project3-console-run`, rate window `4s`, load range `16:23:53.539Z`–`16:24:23.539Z` (Grafana browser hiển thị Asia/Bangkok). Bảy panel hiện lên, có target scrape API1/API2/backend và chuỗi request API, limiter, backend. Ảnh toàn trang: [dashboard](screenshots/row1-grafana-dashboard.png). Đây là dữ liệu truy vấn sau khi runner đã dọn container research; Prometheus volume giữ series. Độ phân giải hiển thị là các evaluation point Grafana chọn cho panel, không dùng để tính request count.

Loki Explore sau cleanup, query startup trong `2026-10-25T16:23:30Z`–`16:24:30Z`: `{project="project3-research-lab",service=~"api1|api2"} |= "server started"` trả 2 startup JSON lines; query riêng `{project="project3-research-lab",service="backend"} |= "server started"` trả 1 dòng backend. Các labels ổn định `project`, `service`, `service_name`; startup config thể hiện mode none, limit 20, window 1s, backend service 50ms/capacity 4. Query trả HTTP 200, log lines còn truy vấn được sau cleanup. Ảnh: [Loki API startup](screenshots/row1-loki-api-startup.png).

## Verdict case

Case 1 đạt các tiêu chí kỹ thuật riêng của case: runner artifact đầy đủ, target/baseline/final scrape, Grafana metrics theo đúng job/range và retained logs/metrics sau cleanup. Không dùng kết quả này để kết luận quota correctness hay baseline nghiên cứu. Suite P2-06 vẫn pending năm case còn lại.

Nguồn runner raw/ignored được giữ nguyên tại `artifacts/console/20261025T162327-4e8d83985f96/`; chưa chỉnh sửa hay xóa.
