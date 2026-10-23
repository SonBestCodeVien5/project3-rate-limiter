# Sổ task P2 — monitoring và demo

P2 là phần mở rộng local do người dùng chọn để học monitoring và cải thiện demo; không đổi yêu cầu hay bằng chứng baseline. Mục tiêu cơ bản là Prometheus, Grafana, Alloy, Loki, một dashboard, truy vấn metrics/logs và demo lặp lại được. Histogram, alerting, tracing, exporters hạ tầng, tự discovery mọi Console run và observability production là tùy chọn/ngoài scope.

**Hiện trạng 23/10/2026:** P2-01 hoàn tất G1 ở commit `0bea7b2`; P2-02 hoàn tất triển khai G1 ở commit `d785529`; P2-03 đã kiểm chứng dashboard và runtime G2 trên stack cố định. Dashboard 7 panel ở commit `bedb095`; JSON `GET /metrics` giữ nguyên. Smoke dùng **5/10 request `/work` tuần tự**, không có demo load hay outage, khép gói bằng cleanup giữ named volumes. Sửa lỗi trang danh sách Grafana sau đó ở `9cecd15`, chi tiết bên dưới. Dừng triển khai sau P2-03; gói kế tiếp cần yêu cầu mới.

## Cách tiếp tục

Đọc đúng task đang làm trong sổ này, rồi phần liên quan của [DESIGN](DESIGN.md), [RUNBOOK](RUNBOOK.md) hoặc [LEARNING_GUIDE](LEARNING_GUIDE.md). Kiểm tra code/caller thuộc gói trước khi sửa. [AGENTS.md](../../AGENTS.md) quy định nguồn bắt buộc, ownership và commit. [Checkpoint](../context/SESSION_CHECKPOINT.md) ghi kiểm tra/giới hạn từng phiên.

Chuỗi mặc định: `P2-01 → P2-02 → P2-03 → P2-04 → P2-05 → P2-06 → P2-08`; P2-07 là nhánh có điều kiện. Không tự giao hoặc khởi chạy task sau điểm dừng được yêu cầu.

## Phạm vi và bảo toàn evidence

| Phần | Quy tắc |
| --- | --- |
| Project 3 baseline | Rate limiter, mixed legitimate/abusive backend protection và bounded Redis outage; dashboard là tùy chọn ở baseline. |
| P2 cơ bản | Đủ bốn Prometheus/Grafana/Alloy/Loki và demo/học; không tuyên bố hoàn tất nếu mới có metrics. |
| Giữ riêng | Không ghép P2 telemetry vào T09/T10. Measurement source vẫn `0291a80fb404fea0eafee8c3431acc3631bb423e`; không rerun, diễn giải lại hoặc đo overhead baseline dưới nhãn P2. Xem [readiness](../experiments/PROTOCOL_READINESS.md). |
| Học tập | Technical completion không xác nhận người học đã hiểu; learning check cần người dùng tự làm/xác nhận. |

## Cổng quyền

| Cổng | Giới hạn | Trạng thái hiện tại |
| --- | --- | --- |
| G0 — tài liệu | Đọc, viết và kiểm tra tài liệu | P2-00 hoàn tất |
| G1 — triển khai | Sửa code/config/test và focused checks; không start stack, loadgen hoặc outage | P2-01/P2-02 và dashboard P2-03 hoàn tất trong phạm vi được cấp riêng |
| G2 — runtime smoke | Stack demo đúng project; scrape/browser; tối đa **10 request `/work` tuần tự**; không pause Redis | Đã được cấp và dùng **chỉ cho P2-03**: 5/10 request; kết thúc tại điểm dừng P2-03, không chuyển quyền sang gói sau |
| G3 — demo load | Chỉ scenario đã ghi theo P2-06; không chạy research matrix | Chưa được cấp |
| G4 — Redis outage | Pause/unpause đúng Redis demo, cleanup và healthy reference theo P2-07 | Chưa được cấp |

Đọc yêu cầu hiện hành để xác định các cổng đã được bao phủ. Nếu người dùng đã cho phép một hành động trong giới hạn cụ thể, không hỏi lại cho từng lệnh trong phạm vi đó. Nếu yêu cầu chỉ bao phủ tài liệu hoặc code, dừng trước runtime tương ứng. Kế hoạch không tự cấp quyền.

## Task registry

Trạng thái chỉ đổi khi có bằng chứng; `Xong` kỹ thuật không thay xác nhận học.

| ID | Gói việc | Phụ thuộc/cổng | Trạng thái |
| --- | --- | --- | --- |
| P2-00 | Kế hoạch, design, runbook, learning guide và routing | — | **Xong**; xem checkpoint |
| P2-01 | Prometheus exposition, giữ JSON metrics | P2-00; G1 | **Xong**, `0bea7b2`; chi tiết tests/skips ở checkpoint |
| P2-02 | Compose overlay, Prometheus/Grafana và provisioning | P2-01; G1 | **Xong G1**, `d785529`; runtime được kiểm chứng trong P2-03 |
| P2-03 | Dashboard metrics và runtime smoke | P2-02; G2 | **Xong kỹ thuật**; dashboard `bedb095`, evidence và giới hạn ở phần P2-03; học tập chưa xác nhận |
| P2-04 | Alloy → Loki logs và datasource | P2-02; sau P2-03 theo mặc định | **Chưa bắt đầu** |
| P2-05 | Kiểm chứng pipeline logs và vòng đời stack | P2-03/P2-04; G2 | **Chưa bắt đầu** |
| P2-06 | Demo normal/mixed: none/local/Redis | P2-05; G3 | **Chưa bắt đầu** |
| P2-07 | Demo Redis outage fail-open/fail-closed | P2-06; G4 | **Chờ điều kiện**, tùy chọn |
| P2-08 | Đóng gói, hướng dẫn và diễn tập | P2-06; ghi rõ có/không P2-07 | **Chưa bắt đầu** |

## Tiêu chí theo gói

### P2-01 — endpoint metrics (hoàn tất)

`GET /metrics/prometheus` xuất 10 API counters hoặc 4 backend counters từ atomic counters hiện có; JSON schema, limiter và nghiên cứu không đổi. Focused/full server tests, vet, formatting đạt. `promtool` không có sẵn; chưa có parser độc lập hoặc runtime scrape. Xem commit/test/skips ở [checkpoint](../context/SESSION_CHECKPOINT.md); snapshot nhiều counter không phải transaction.

### P2-02 — Prometheus/Grafana (hoàn tất G1)

- Tệp triển khai: `compose.observability.yaml`, `deploy/monitoring/prometheus.yml`, `deploy/monitoring/grafana/provisioning/`. Giữ research runner Compose nguyên trạng.
- Dùng project `project3-monitoring-demo`; pin image versions (không dùng `latest`), provision datasource/provider với UID ổn định, không commit credentials; kiểm tra host-port conflicts.
- Compose mount, scrape service DNS, retention/storage, loopback ports, healthcheck và cleanup theo [design](DESIGN.md)/[runbook](RUNBOOK.md). Static config pass không phải runtime pass.
- Tiêu chí tĩnh: Compose resolve được, mounts/ports đúng và config được validator phù hợp kiểm tra khi có công cụ; không đánh dấu runtime đạt chỉ từ `compose config`.

Kết quả G1 (`d785529`): overlay project cố định; scrape ba service qua `/metrics/prometheus`; datasource UID `project3-prometheus`, provider/folder ổn định; named volumes, loopback, healthchecks, memory/retention budget và log rotation đã cấu hình. Image Prometheus `v3.15.0`/Grafana `12.4.11` được đối chiếu nguồn chính thức; digest và image thực tế chưa kiểm chứng.

Kiểm tra tại điểm dừng P2-02: base Compose độc lập và base+overlay resolve; YAML/PyYAML và assertions cho targets/labels, mount paths, ports, provisioning, healthchecks, logging, secret không lộ nội dung; `git diff --check`. Bảy host ports không có listener tại lúc kiểm tra. Khi đó `promtool` không sẵn có; chưa chạy validator Prometheus, image, scrape hay UI. Chi tiết lệnh và file tạm ở [checkpoint](../context/SESSION_CHECKPOINT.md). Kết quả runtime/dashboard sau đó thuộc P2-03 bên dưới; Loki/Alloy và xác nhận học tập vẫn chưa hoàn tất.

### P2-03 — dashboard và smoke

Tệp dashboard: `deploy/monitoring/grafana/dashboards/project3-overview.json`. Làm **6–8 panels** theo design, đơn vị/nhãn demo rõ; không giả lập p95/goodput từ counters hoặc gộp backend arrivals với successes. G2 smoke đối chiếu scrape với JSON/exposition trên cả hai API và backend; kiểm tra query/browser thật, thiếu mẫu phải hiện rõ. Hoàn tất khi targets, panels, restart semantics và JSON Console compatibility được kiểm tra runtime; ghi kết quả/cleanup.

**Kết quả 23/10/2026:** 7 panel, dashboard UID `project3-monitoring-demo`, datasource UID `project3-prometheus`; giải thích tiếng Việt, đơn vị request/s và nhãn dữ liệu demo. Giữ gaps khi thiếu dữ liệu, `rate` trước `sum`; tách backend arrivals/success/overload. Cả ba target `api1`/`api2`/`backend` UP; 11 biểu thức PromQL trả kết quả thành công; Grafana API xác nhận provisioning và Chromium hiển thị đủ 7 panel qua các vị trí cuộn. JSON/exposition đã đối chiếu trên cả ba service; restart riêng `api1` reset counters. Không chạy Console research run.

Smoke có 5 request tuần tự, đều HTTP 200; API deltas +1, backend kiểm tra riêng +1 arrival/+1 success/0 overload. Khoảng backend ban đầu có delta +2 vì chứa hai request, không phải phép kiểm tra một request. Snapshot nhiều counters không phải transaction; `rate`/`increase` không thay exact count. Không suy latency, legitimate goodput, correctness hoặc kết quả T09/T10 từ dashboard. Technical completion không xác nhận người dùng đã hiểu monitoring.

Bằng chứng và lệnh đã loại secrets: [checks](../../artifacts/monitoring/p2-03-g2/checks.md), [request ledger](../../artifacts/monitoring/p2-03-g2/work-ledger.txt), [commands](../../artifacts/monitoring/p2-03-g2/commands.md), [ảnh UI và mô tả](../../artifacts/monitoring/p2-03-g2/browser-ui.md), [checksums](../../artifacts/monitoring/p2-03-g2/SHA256SUMS). Source chạy là `bedb095`; evidence hoàn chỉnh ở `6b0f2ed`, cập nhật design/runbook ở `e8201a5`. `promtool check config` đạt khi chạy từ pinned Prometheus image; bản host không có sẵn. UTC, image IDs/digests, lỗi ban đầu và cleanup được ghi trong evidence. Stack `project3-monitoring-demo` đã dừng/xóa containers và network, giữ hai named volumes; không còn service thuộc project chạy hoặc paused. **Điều kiện tiếp theo:** người dùng yêu cầu mới cho P2-04 (Alloy → Loki logs và datasource), nêu rõ gate được cấp; không tự dùng lại G2 của P2-03. G3/G4 chưa được cấp.

**Sửa lỗi vận hành sau P2-03 (23/10/2026):** người dùng mở lại stack để học và gặp `RangeError: Maximum call stack size exceeded` ở trang danh sách Grafana. UID folder trùng UID dashboard làm cây danh sách lặp đệ quy; kiểm tra UI trực tiếp ban đầu chưa bao phủ trang này. Commit `9cecd15` đổi folder sang **Project 3 Monitoring** / `project3-monitoring-folder`, giữ dashboard UID/URL. Reload provisioning đạt; browser kiểm tra list, mở folder và dashboard đạt; người dùng xác nhận hết lỗi sau refresh. Evidence riêng ở `dde34ad`: [checks](../../artifacts/monitoring/grafana-uid-collision-fix/checks.md). Không sửa evidence G2 gốc, không gửi `/work`, restart hay dừng service; stack phiên học được để chạy. Việc này không mở P2-04 hoặc G3/G4.

### P2-04 — Alloy/Loki

Tệp dự kiến: `deploy/monitoring/alloy/config.alloy`, `deploy/monitoring/loki.yml`, provisioning và Compose. Loki chạy một tiến trình local; Alloy chỉ đọc đúng project và allowlist service app. Không thu mọi container, thêm access log từng request, expose Docker daemon TCP hoặc dùng `privileged`. Xác minh Docker socket/API; `:ro` không làm Docker API read-only. Nếu không dùng được, ghi blocker hoặc thiết kế file input riêng, không mount host rộng.

### P2-05 — kiểm chứng logs/lifecycle

Trong G2, kiểm tra log thật từ source tới Loki/Grafana, filter labels/container, delay/timezone/parse errors/positions/restart, datasource, permissions, health và disk. Ghi rõ không có exactly-once guarantee. Hoàn tất khi metrics và logs hoạt động cùng nhau, restart/cleanup không ảnh hưởng project khác.

### P2-06 — bounded demo load

Trước load, ghi config/ngân sách vào `scenario-plan.md`; dùng loadgen hiện có trên stack cố định, không dùng research runner/Console Start. Ngân sách: tối đa **6 case**, normal/mixed × none/local/Redis; **30 giây/case**, tối đa **120 RPS**, một attempt/case. Điểm khởi đầu đề xuất: FW `Q=20,W=1s`, 2 API, backend capacity 4/service 50ms; normal 20 RPS, mixed tổng 120 RPS/hợp lệ 20 RPS. So sánh phải giữ algorithm/policy/workload/key/backend/topology cố định và chỉ đổi mode. Kiểm tra key distribution/flags trước khi khóa scenario. Retry hoặc config change cần scope/ngân sách mới; demo không phải benchmark.

### P2-07 — outage có điều kiện

Chỉ chạy khi yêu cầu bao phủ G4. Ngân sách riêng: tối đa **4 case** healthy/outage × fail-open/fail-closed; **30 giây/case**, **20 RPS**, một attempt/case. Mỗi outage case pause đúng Redis demo **một lần 2 giây**, dự kiến tại giây 10; ghi thời điểm thực. Healthy references cùng config, không cộng ngầm vào P2-06. Trước đó kiểm chứng trap/watchdog unpause và resource ownership. Không restart host Redis, FLUSHDB hay sửa clock/system config. Báo kết quả như demo fault injection, không phải HA/correctness/recovery protocol pass.

### P2-08 — đóng gói

Cập nhật runbook từ dự kiến thành đã thử, demo script, index và P2 source revision; giữ T12 bundle/IDs. Tạo offline fallback gắn case/config/time range/revision/giới hạn; kiểm tra fresh start, recovery và cleanup. Người dùng tự xác nhận learning checklist. P2 cơ bản chỉ hoàn tất khi P2-01–P2-06 và P2-08 có evidence, đủ bốn công cụ và fallback/recovery; ghi rõ trạng thái P2-07.
