# Kế hoạch scenario P2-06 — bản ghi trước tải

Thời điểm lập: `2026-10-25T16:19:55Z` (UTC). Batch: `p2-06-20261025T161955Z`.

## Phạm vi và ma trận

Chạy đúng sáu lần submit qua form Console **Chạy benchmark** hiện có, mỗi lần một case, `repetitions=1`, bật monitoring. Tất cả theo Console → `research-pilot.sh` → topology renderer/loadgen hiện tại. Mỗi load tối đa 30 giây, offered load tối đa 120 RPS. Không retry, thay run, thêm case thứ bảy, kéo dài duration, chạy `/work` ngoài sáu load, hoặc thao tác outage.

| # | Profile | Offered load | Mode | Attempts | Run ID / kết quả |
|---|---|---:|---|---:|---|
| 1 | normal | 20 RPS, toàn bộ hợp lệ | none | 1 | pending |
| 2 | normal | 20 RPS, toàn bộ hợp lệ | local | 1 | pending |
| 3 | normal | 20 RPS, toàn bộ hợp lệ | Redis | 1 | pending |
| 4 | mixed | 120 RPS tổng, gồm 20 RPS hợp lệ | none | 1 | pending |
| 5 | mixed | 120 RPS tổng, gồm 20 RPS hợp lệ | local | 1 | pending |
| 6 | mixed | 120 RPS tổng, gồm 20 RPS hợp lệ | Redis | 1 | pending |

## Cấu hình gửi từ UI

Giữ chung 2 API instances; Fixed Window, `limit=20`, `window_ms=1000`; backend `capacity=4`, `service_time=50ms`; `fail_policy=closed` cả ba mode, dù chỉ Redis có đường lỗi Redis; `duration_seconds=30`; monitoring opt-in. Normal: `rps=20`, `legitimate_rps=20`. Mixed: `rps=120`, `legitimate_rps=20`. Loadgen hiện dùng 5 legitimate clients, khóa `legitimate-0001`…`legitimate-0005` theo vòng tròn; abusive traffic dùng một khóa `abusive-0001`.

Để hồ sơ custom đầy đủ, các field không hoạt động với Fixed Window được gửi rõ: `capacity=20`, `refill_rate=20`; burst start `2s`, duration `2s`, peak `200 RPS`; concurrent offset `2s`, count `100`. Profile normal/mixed không sử dụng các field burst/concurrent. Loadgen dùng tối đa in-flight `200`, request timeout `2s`, max schedule lag `100ms`, 5 khóa hợp lệ; các giá trị này theo lệnh runner hiện hành. Chỉ mode thay đổi giữa các lượt tương ứng.

## Ngưỡng hoàn tất và ghi nhận

Case hoàn tất kỹ thuật khi runner tạo artifact config/policy/topology/revision/image IDs và summary/trace; nguồn runner ghi offered/scheduled/sent/dropped cùng response outcomes; target đăng ký đúng owner và UP có baseline trước load; có load start/end, drain và final scrape sau drain; Grafana dùng job `project3-console-run`, rate window `4s`, exact load range và có API/backend samples; Loki có startup JSON phù hợp; dữ liệu vẫn query được sau cleanup; manifest được gỡ đúng owner. Dashboard không thay artifact runner, không được dùng suy goodput, latency hoặc correctness. Thiếu sample/query/file/coverage là incomplete, không pass. Ghi rõ độ chính xác timestamp/flooring quan sát được; không dời query bounds hoặc tăng duration.

Giữ riêng snapshot `scenario-plan.md` này làm cấu hình dự kiến. `attempt-ledger.md` sẽ ghi trạng thái thực tế từng attempt, không sửa kế hoạch sau khi bắt đầu.

## Cleanup và bảo toàn trạng thái

Trước phiên, chín container `project3-monitoring-demo` đều ở trạng thái stopped; giữ nguyên identity của cả chín. Chỉ start chúng để chạy suite, sau đó stop đúng các container phiên đã start, không xóa/recreate. Giữ bốn volume hiện có và hai network dự án (`project3-monitoring-demo_default`, `project3-monitoring-scrape`) nguyên vẹn. Không chạm tài nguyên project khác.

Sau mỗi run, dùng cleanup/owner trong runner để xóa manifest chỉ khi record còn khớp owner; xác nhận lock đã nhả. Runner tự scoped `down --remove-orphans` với project research do run vừa tạo. Cuối phiên chỉ đóng Console/browser do phiên này mở; stop monitoring container đã start lúc đầu; khôi phục trạng thái ban đầu (chín container stopped). Giữ raw ignored artifacts, cả lượt lỗi/canceled; không prune/xóa artifacts/volume/network. Nếu Console/browser đã tồn tại từ trước thì không đóng.

## Preflight trước tải

Đã xem UI/model/validation, lệnh runner, topology renderer và cách loadgen tạo key. Worktree tại lần đọc đầu sạch, HEAD `c623a305731b3d9ec3efd2890d11e0b913f622bf`; HEAD/dirty state sẽ ghi lại cho từng attempt vì root có thể đang commit thay đổi song song. Compose image tags ghim: Redis `7.4.2-alpine`, Nginx `1.28.0-alpine`, Prometheus `v3.15.0`, Grafana `12.4.11`, Loki `3.7.0`, Alloy `v1.21.2`; ghi image IDs thực tế trước load.

Ban đầu Docker socket bị sandbox từ chối, chưa chạy load. Được phép đọc tài nguyên Docker hiện có và start đúng chín container đã dừng. Cả chín identity còn nguyên và sau start healthy (Loki/Alloy đang chạy); Prometheus `/−/ready` và Grafana `/api/health` đáp ứng. Loki chưa có host port (được query trong Docker network từ Grafana). Đường target `artifacts/monitoring/console-targets/` tồn tại rỗng; lock `artifacts/.research-pilot.lock` tồn tại, kích thước 0; không thấy tiến trình research-pilot/loadgen/Console. Cổng cố định 8080/18081–18083, Grafana 13000, Prometheus 19090 đang listen sau khi stack start; cần xác minh Console trên 8090 và không có research container trước mỗi attempt. Credentials không được đọc/ghi vào evidence hoặc output.
