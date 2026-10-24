# P2-03A — kiểm tra acceptance Console → Grafana

Ngày: 2026-10-24. Đây là một pilot runtime trên source sạch
`1687a61672b54a258afa78c52c93fc4cfcaf013b`; không thay evidence T09/T10.

## Kết quả

- Run `20261024T152427-65c5e2bc4341` được tạo bởi đúng một lần submit trên nút
  **Chạy benchmark** hiện có; attempt trước `20261024T145701-272e462e6502` giữ
  nguyên và không retry.
- Cấu hình: custom, normal/all legitimate, Redis shared state, Fixed Window,
  fail-closed, 2 API, quota 20/1s, backend capacity 4/service 50ms, 20 RPS,
  30 giây, 1 repeat; monitoring bật. UI request và resolved config khớp.
- Loadgen ghi 600 scheduled/sent, 600 HTTP 2xx, 600 legitimate successes,
  600 backend-confirmed arrivals và 0 drops. Đây là pilot; không suy quota
  correctness từ các bộ đếm.
- Metadata ghi load UTC start/end với nanosecond precision:
  `2026-10-24T15:24:53.378456510Z`–`2026-10-24T15:25:23.378000000Z`.
  Prometheus/Grafana range dùng epoch milliseconds, làm tròn start xuống
  `15:24:53.378Z` (khoảng 0.456510 ms trước metadata start) và end là
  `15:25:23.378Z`; đây là precision của range đã request, không phải metadata start ở
  nanosecond precision. Generator drain lúc `15:25:23.383030760Z`; final scrape cả ba
  target lúc `15:25:24.493Z`, sau drain và trước deregistration.
- Prometheus range `project3-console-run` có 31 evaluation points cho từng
  `api1`, `api2`, `backend` trong range ms-floor đã request; các chuỗi `up` đều
  là 1. Đây là evaluation points của `query_range` với step 1s, không khẳng định
  31 raw scrape samples riêng biệt. Counter cuối API1/API2 lần lượt 300/300
  request và backend 600 arrivals/600 successes; tổng khớp load summary.
- Console link chọn job `project3-console-run`, rate window `4s`, và đúng range
  tải. Grafana dashboard identity khớp; browser record thấy đủ 7/7 panel, 14
  query responses HTTP 200, không có query error hay No data.
- Sau cleanup theo evidence đã lưu: không còn research target/container; fixed
  targets vẫn UP tại lần post-cleanup check. Không đọc runtime hiện tại từ kết
  quả lịch sử này.

## Kiểm tra đã thực hiện khi closeout

- Đối chiếu JSON đã lưu: config, ID/revision, summary, UTC bounds, scrape
  points, counter snapshots, Grafana link/browser và cleanup record.
- Xác minh manifest checksum gốc từ thư mục evidence:
  `sha256sum -c <(sed 's#artifacts/monitoring/p2-03a-console-recheck/##' SHA256SUMS)`
  — 38/38 entries passed. Đây là full local capture manifest, được giữ nguyên
  riêng với selected commit manifest `SELECTED_SHA256SUMS` (repository-root-relative paths, gồm checks.md và
  các artifact JSON/ảnh được chọn). SHA256 manifest gốc:
  `fcd0c780d944e8ce2a30a5d5e59690cda40518a6a5768833b8ac95e827b5002b`.
- Không chọn `*.cjs`, browser/UI submit captures, form screenshot hay auth state.
  Không chạy benchmark, POST, `/work`, script browser/UI, code suite hay live
  health query trong closeout. Chỉ chọn artifact cần thiết; không đưa script,
  request capture, ảnh form hoặc dữ liệu xác thực vào commit evidence.

## Giới hạn và trạng thái hiện tại

Kết quả chỉ xác nhận đường telemetry cho một run 30 giây; 1s scrape / 4s rate
window chưa được khái quát cho workload ngắn hơn. Không đánh giá latency,
correctness, overhead, resource utilization, P2-06 coverage hoặc T09/T10.
Learning confirmation chưa có. Grafana credential tool-echo incident trước đó
chưa được xử lý bằng rotation; không có credential trong các artifact được chọn.

Lần kiểm tra trạng thái hiện tại riêng của root cho thấy 7 container
`project3-monitoring-demo` đang `Exited (0)`, không có container
`project3-research-lab`, thư mục target JSON rỗng. Vì vậy monitoring stack không
đang chạy ở thời điểm kiểm tra; listeners/Console chưa được xác định. Không có
restart hay mutation. Dừng tại P2-03A; P2-04 và tải thêm cần scope mới.
