# Sổ task P2 — monitoring và demo

P2 là phần mở rộng local do người dùng chọn để học monitoring và cải thiện demo; không đổi yêu cầu hay bằng chứng baseline. Mục tiêu cơ bản là Prometheus, Grafana, Alloy, Loki, một dashboard, truy vấn metrics/logs và demo lặp lại được. Histogram, alerting, tracing, exporters hạ tầng, tự discovery mọi Console run và observability production là tùy chọn/ngoài scope.

**Hiện trạng 24/10/2026:** P2-01–P2-03 đã triển khai/kiểm tra cho metrics và fixed monitoring stack; P2-03 G2 dùng **5/10 request `/work` tuần tự**, không phải Console benchmark, demo load hay outage. Evidence G2/UID-fix giữ nguyên và chỉ chứng minh fixed stack. P2-03A, P2-04–P2-08 chưa bắt đầu; P2-03A là đề xuất trước logs và load. Không có quyền G1/G2/G3/G4 mới. Lịch sử kết quả, source revision và cleanup của P2-03 được ghi dưới đây/checkpoint.

## Cách tiếp tục

Đọc đúng task đang làm trong sổ này, rồi phần liên quan của [DESIGN](DESIGN.md), [RUNBOOK](RUNBOOK.md) hoặc [LEARNING_GUIDE](LEARNING_GUIDE.md). Kiểm tra code/caller thuộc gói trước khi sửa. [AGENTS.md](../../AGENTS.md) quy định nguồn bắt buộc, ownership và commit. [Checkpoint](../context/SESSION_CHECKPOINT.md) ghi kiểm tra/giới hạn từng phiên.

Thứ tự ưu tiên hiện hành: `P2-00 → P2-01 → P2-02 → P2-03 → P2-03A → P2-04 → P2-05 → P2-06 → P2-08`; P2-07 là nhánh có điều kiện sau P2-06. P2-00–P2-03 đã hoàn tất cho fixed stack; evidence giữ nguyên và chỉ chứng minh đúng phạm vi lịch sử đó. P2-03A trở đi là kế hoạch tích hợp/kiểm tra thêm cho run Console opt-in, chưa triển khai/cấp quyền. Không tự giao hoặc khởi chạy task sau điểm dừng được yêu cầu.

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

Người dùng có thể cấp G1, G2 và G3 cùng lúc trong một yêu cầu rõ ràng, kèm phạm vi và ngân sách cần thiết; khi các bước đã nằm trong phạm vi đó, không hỏi lại cho từng thao tác. Hiện P2-03A chưa được cấp gate nào; nội dung kế hoạch không tự cấp quyền runtime.

## Task registry

Trạng thái chỉ đổi khi có bằng chứng; `Xong` kỹ thuật không thay xác nhận học.

| ID | Gói việc | Phụ thuộc/cổng | Trạng thái |
| --- | --- | --- | --- |
| P2-00 | Kế hoạch, design, runbook, learning guide và routing | — | **Xong nền tảng; duy trì bản đồ tác động toàn P2 trong registry** |
| P2-01 | Prometheus exposition, giữ JSON metrics | P2-00; G1 | **Xong**, `0bea7b2`; chi tiết tests/skips ở checkpoint |
| P2-02 | Compose overlay, Prometheus/Grafana và provisioning | P2-01; G1 | **Xong G1**, `d785529`; runtime được kiểm chứng trong P2-03 |
| P2-03 | Dashboard metrics và runtime smoke | P2-02; G2 | **Xong kỹ thuật**; dashboard `bedb095`, evidence và giới hạn ở phần P2-03; học tập chưa xác nhận |
| P2-03A | Scrape các run Chạy benchmark hiện có khi bật monitoring | P2-03; G1/G2/G3 theo phạm vi được cấp | **Đề xuất ưu tiên kế tiếp; chưa bắt đầu, chưa được cấp quyền** |
| P2-04 | Alloy → Loki logs và datasource | P2-02; ưu tiên sau vertical slice P2-03A | **Chưa bắt đầu** |
| P2-05 | Kiểm chứng pipeline logs và vòng đời stack | P2-03/P2-04; G2 | **Chưa bắt đầu** |
| P2-06 | Console normal/mixed: none/local/Redis | P2-03A; G3; cùng runner/topology cho cả ma trận | **Chưa bắt đầu** |
| P2-07 | Demo Redis outage fail-open/fail-closed | P2-06; G4 | **Chờ điều kiện**, tùy chọn |
| P2-08 | Đóng gói, hướng dẫn và diễn tập | P2-06; ghi rõ có/không P2-07 | **Chưa bắt đầu** |

### Bản đồ tác động toàn P2

| Gói | Giữ lại | Điều chỉnh/kế hoạch tương lai |
| --- | --- | --- |
| P2-00 | Registry là chủ sở hữu trạng thái; design/runbook/learning guide là mô tả kỹ thuật và reader route | Đồng bộ các tài liệu hiện hành với luồng Console runner opt-in; không coi đề xuất là tính năng đã chạy. |
| P2-01 | Prometheus exposition và JSON `/metrics` nguyên trạng, dùng được cho fixed và research targets | Không sửa counter semantics/schema để tích hợp dashboard. |
| P2-02 | Stack, image pins, volumes, secrets, datasource UID `project3-prometheus`, loopback ownership | Đề xuất gắn Prometheus vào shared scrape network và mount allowlisted file_sd directory; giữ fixed service discovery/job. Chưa sửa cấu hình. |
| P2-03 | Bảy panels, dashboard UID `project3-monitoring-demo`, folder UID `project3-monitoring-folder`, datasource, fixed-job query và toàn bộ evidence/UID-fix | Thêm chọn job/topology và UTC context cho research; regression cả fixed panels, target list, Grafana list/folder/dashboard. Evidence cũ chỉ hợp lệ cho fixed stack, không chứng minh Console integration. |
| P2-03A | Nút, model, runner, generator, topology, lock/cancel/scoped cleanup hiện có | Opt-in file_sd/API-backend allowlist; là prerequisite metrics vertical slice trước P2-04/05, chưa bắt đầu. |
| P2-04/05 | App JSON logs, Alloy/Loki local pipeline và fixed demo teaching path | Filter rõ fixed project + opted-in research services; P2-05 kiểm tra registration/log discovery/lifecycle/cancel/kill/stale manifest và dừng từng project đúng owner. Chỉ sau logs G2 mới hoàn tất full monitoring. |
| P2-06 | Mức tải, số case và giới hạn đã nêu dưới đây | Toàn bộ suite cùng Console runner/topology/instrumentation; không trộn fixed demo, không lấy CLI/redis-outage.sh thay tương tác Console. |
| P2-07 | G4 optional và ngân sách outage được khóa bên dưới | Chưa có đường fault hook an toàn cho Redis trong run research; không pause Redis fixed project khi load chạy ở research project. Chỉ thiết kế lại P2-07 để target/lifecycle hiện hữu nếu được cấp riêng; nếu không khớp, giữ blocked, không dùng workflow tải thứ hai. |
| P2-08 | T12 bundle/T10 offline artifacts và learning checklist | Đóng gói hướng dẫn source hiện tại, opt-in path, exact UTC links, offline dashboard/log screenshots hoặc dữ liệu mẫu, recovery/cleanup; không tái sinh hay thay artifacts baseline. |

## Tiêu chí theo gói

### P2-01 — endpoint metrics (hoàn tất)

`GET /metrics/prometheus` xuất 10 API counters hoặc 4 backend counters từ atomic counters hiện có; JSON schema, limiter và nghiên cứu không đổi. Focused/full server tests, vet, formatting đạt. `promtool` không có sẵn; chưa có parser độc lập hoặc runtime scrape. Xem commit/test/skips ở [checkpoint](../context/SESSION_CHECKPOINT.md); snapshot nhiều counter không phải transaction.

### P2-02 — Prometheus/Grafana (hoàn tất G1; research extension chưa làm)

- Tệp hiện tại: `compose.observability.yaml`, `deploy/monitoring/prometheus.yml`, `deploy/monitoring/grafana/provisioning/`. Đây là fixed-stack implementation đã kiểm tra; không mô tả như đã có research discovery.
- Dùng project `project3-monitoring-demo`; pin image versions (không dùng `latest`), provision datasource/provider với UID ổn định, không commit credentials; kiểm tra host-port conflicts.
- Compose mount, scrape service DNS, retention/storage, loopback ports, healthcheck và cleanup theo [design](DESIGN.md)/[runbook](RUNBOOK.md). Static config pass không phải runtime pass.
- Tiêu chí tĩnh: Compose resolve được, mounts/ports đúng và config được validator phù hợp kiểm tra khi có công cụ; không đánh dấu runtime đạt chỉ từ `compose config`.

Kết quả G1 (`d785529`): overlay project cố định; scrape ba service qua `/metrics/prometheus`; datasource UID `project3-prometheus`, provider/folder ổn định; named volumes, loopback, healthchecks, memory/retention budget và log rotation đã cấu hình. Image Prometheus `v3.15.0`/Grafana `12.4.11` được đối chiếu nguồn chính thức; digest và image thực tế chưa kiểm chứng.

Kiểm tra tại điểm dừng P2-02: base Compose độc lập và base+overlay resolve; YAML/PyYAML và assertions cho targets/labels, mount paths, ports, provisioning, healthchecks, logging, secret không lộ nội dung; `git diff --check`. Bảy host ports không có listener tại lúc kiểm tra. Khi đó `promtool` không sẵn có; chưa chạy validator Prometheus, image, scrape hay UI. Chi tiết lệnh và file tạm ở [checkpoint](../context/SESSION_CHECKPOINT.md). Kết quả runtime/dashboard sau đó thuộc P2-03 bên dưới; Loki/Alloy và xác nhận học tập vẫn chưa hoàn tất.

### P2-03 — dashboard và smoke

Tệp dashboard: `deploy/monitoring/grafana/dashboards/project3-overview.json`. Làm **6–8 panels** theo design, đơn vị/nhãn demo rõ; không giả lập p95/goodput từ counters hoặc gộp backend arrivals với successes. G2 smoke đối chiếu scrape với JSON/exposition trên cả hai API và backend; kiểm tra query/browser thật, thiếu mẫu phải hiện rõ. Hoàn tất khi targets, panels, restart semantics và JSON Console compatibility được kiểm tra runtime; ghi kết quả/cleanup.

**Kết quả 23/10/2026:** 7 panel, dashboard UID `project3-monitoring-demo`, datasource UID `project3-prometheus`; giải thích tiếng Việt, đơn vị request/s và nhãn dữ liệu demo. Giữ gaps khi thiếu dữ liệu, `rate` trước `sum`; tách backend arrivals/success/overload. Cả ba target `api1`/`api2`/`backend` UP; 11 biểu thức PromQL trả kết quả thành công; Grafana API xác nhận provisioning và Chromium hiển thị đủ 7 panel qua các vị trí cuộn. JSON/exposition đã đối chiếu trên cả ba service; restart riêng `api1` reset counters. Không chạy Console research run.

Smoke có 5 request tuần tự, đều HTTP 200; API deltas +1, backend kiểm tra riêng +1 arrival/+1 success/0 overload. Khoảng backend ban đầu có delta +2 vì chứa hai request, không phải phép kiểm tra một request. Snapshot nhiều counters không phải transaction; `rate`/`increase` không thay exact count. Không suy latency, legitimate goodput, correctness hoặc kết quả T09/T10 từ dashboard. Technical completion không xác nhận người dùng đã hiểu monitoring.

Bằng chứng và lệnh đã loại secrets: [checks](../../artifacts/monitoring/p2-03-g2/checks.md), [request ledger](../../artifacts/monitoring/p2-03-g2/work-ledger.txt), [commands](../../artifacts/monitoring/p2-03-g2/commands.md), [ảnh UI và mô tả](../../artifacts/monitoring/p2-03-g2/browser-ui.md), [checksums](../../artifacts/monitoring/p2-03-g2/SHA256SUMS). Source chạy là `bedb095`; evidence hoàn chỉnh ở `6b0f2ed`, cập nhật design/runbook ở `e8201a5`. `promtool check config` đạt khi chạy từ pinned Prometheus image; bản host không có sẵn. UTC, image IDs/digests, lỗi ban đầu và cleanup được ghi trong evidence. Stack `project3-monitoring-demo` đã dừng/xóa containers và network, giữ hai named volumes; không còn service thuộc project chạy hoặc paused. **Điều kiện tiếp theo:** người dùng yêu cầu mới cho P2-03A và nêu rõ G1 implementation. Sau G1, G2 smoke và G3 vertical slice cần được cho phép rõ; không dùng lại G2 của P2-03. G4 chưa được cấp.

**Sửa lỗi vận hành sau P2-03 (23/10/2026):** người dùng mở lại stack để học và gặp `RangeError: Maximum call stack size exceeded` ở trang danh sách Grafana. UID folder trùng UID dashboard làm cây danh sách lặp đệ quy; kiểm tra UI trực tiếp ban đầu chưa bao phủ trang này. Commit `9cecd15` đổi folder sang **Project 3 Monitoring** / `project3-monitoring-folder`, giữ dashboard UID/URL. Reload provisioning đạt; browser kiểm tra list, mở folder và dashboard đạt; người dùng xác nhận hết lỗi sau refresh. Evidence riêng ở `dde34ad`: [checks](../../artifacts/monitoring/grafana-uid-collision-fix/checks.md). Không sửa evidence G2 gốc, không gửi `/work`, restart hay dừng service; stack phiên học được để chạy. Việc này không mở P2-04 hoặc G3/G4.

### P2-03A — scrape run Chạy benchmark hiện có (đề xuất, chưa được cấp)

**Hiện trạng:** Console `POST /api/runs` gọi `scripts/research-pilot.sh`; runner render topology 1/2/4 API, dựng case trong project `project3-research-lab`, lấy before/after JSON `/metrics`, rồi cleanup project. `GET /api/runs/{id}/metrics` đã poll counters đang chạy qua Docker Compose exec. Prometheus hiện chỉ scrape tĩnh `api1`, `api2`, `backend` của `project3-monitoring-demo` trong network riêng; vì vậy thiếu đường scrape cho case research. Nút `Gửi một request mẫu` là luồng khác, gửi một request vào stack cố định và không thay được benchmark.

**Khuyến nghị kỹ thuật:** giữ nút, request model, generator, topology, lock, cancel và cleanup hiện có; thêm checkbox/flag opt-in cho run Console mới, mặc định tắt. Khi bật, runner hiện tại chỉ đăng ký API/backend của đúng case qua external network `project3-monitoring-scrape`, do monitoring Compose sở hữu vòng đời; research runner không tạo/xóa network. Mount thư mục ignored `artifacts/monitoring/console-targets/` chỉ đọc vào Prometheus, còn runner ghi đúng một active allowlist manifest theo runner lock. Renderer gắn `api1`…`api4` và `backend` bằng aliases ổn định; runner ghi target file `file_sd` sau khi Compose healthy, chờ các target `UP` và baseline scrape rồi thực hiện một khoảng quan sát trước tải theo rate/lookback đã cấu hình. Khoảng này không gửi `/work`, không thuộc thời lượng benchmark và được ghi riêng; sau đó loadgen chạy đúng duration yêu cầu, không tự kéo dài hay trì hoãn để bù sample. Không gắn Redis/Nginx; không dùng Docker socket, Docker discovery rộng, port publish mới hay reroute request. Target file chỉ chứa aliases/labels, không env/secret. Opt-out giữ nguyên đường runner hiện tại.

Dùng job riêng, ổn định `project3-console-run`; giữ job `project3-demo` cho stack cố định. Labels giới hạn ở `service`, topology và project cố định; không thêm Run ID/case/revision/time vào metric labels. Runner ghi UTC ngay sau baseline scrape và sau drain/final scrape, giữ target đăng ký đến khi final scrape xong rồi gỡ trước cleanup. Prometheus TSDB volume giữ samples sau khi case container bị dọn. Nếu target không lên, mất scrape, hoặc runner bị hủy/lỗi thì ghi rõ trạng thái thiếu/incomplete, không coi absent là 0 và không retry ẩn. Một global `flock` hiện đã tuần tự hóa runner; giữ nguyên ownership `project3-research-lab` và scoped cleanup.

Thêm dashboard job selector để xem **một nguồn tại một thời điểm**: `project3-demo` hoặc `project3-console-run`; các PromQL không gộp fixed-stack traffic vào research run. Link Console dùng UTC load start/end chính xác của case, không dịch `from` để che phần đầu workload. Trước load, opt-in runner có thể quan sát targets trong khoảng lookback cấu hình (ứng viên 4s), không phát `/work`, để tách query window khỏi case liền trước; ghi khoảng này riêng khỏi load duration. Giữ final scrape sau drain riêng. Fixed stack giữ scrape 2s/rate 20s; research scrape 1s, `file_sd` refresh 1s và rate window 4s chỉ là ứng viên cần kiểm chứng khi được phép, không phải yêu cầu hay bảo đảm đủ phân giải. Case 3s có thể thiếu mẫu; không sửa duration/protocol để lấp dữ liệu. G3 acceptance dùng case P2-06 tối đa 30s và xác minh timing thực tế. Không dùng dashboard để kết luận quota correctness, legitimate goodput, latency, Redis resources hay kết quả T09/T10.

Mỗi run được bật monitoring là telemetry demo mới, không phân loại lại pilot/formal run cũ và không tham gia T09/T10. Giữ artifact runner hiện có: request/policy/Compose đã resolve, revision + dirty state, images/image IDs, summary/trace/before-after counters; bổ sung cờ opt-in, target/health record, scrape/window UTC và Grafana link. Ghi rõ network scrape/instrumentation thay đổi runtime so với run opt-out; không suy overhead hay so sánh telemetry run với T09/T10. UID dashboard `project3-monitoring-demo`, folder `project3-monitoring-folder`, datasource `project3-prometheus` giữ nguyên và khác nhau.

**Touchpoints G1 dự kiến:** `internal/console/console.go`, `internal/console/index.html`, checks Console; `scripts/research-pilot.sh`, `scripts/render-topology.py` và checks runner; `compose.observability.yaml`, `deploy/monitoring/prometheus.yml`, `deploy/monitoring/grafana/dashboards/project3-overview.json`. Dashboard thêm selector job, research query window và Console link có job + UTC range; giữ nguyên dashboard/folder/datasource UIDs. Không sửa JSON `/metrics` hoặc đường chạy opt-out. G1 chỉ implementation/focused checks; G2 kiểm tra stack/scrape config runtime theo đúng phạm vi; G3 bắt buộc bấm **Chạy benchmark** hiện có với opt-in và thấy API/backend samples của run đó trong dashboard, đúng job/time range. Chỉ sau G3 mới đạt end-to-end; một request mẫu hoặc static config không đủ.

**Gate/budget:** G1/G2/G3 có thể được cho phép chung trong một yêu cầu rõ ràng, với ngân sách cụ thể; hiện chưa gate nào được cấp. Đề xuất điều chỉnh P2-06 để cả normal/mixed × none/local/Redis chạy qua cùng Console runner/topology khi monitoring bật; ma trận này thay đề xuất fixed-stack chưa chạy, không cộng thêm lượt. G3 acceptance là một trong sáu case đó, không phải case thứ bảy; tổng tối đa **6 case**, **30 giây/case**, **120 RPS**, **1 attempt/case**. Case G3 chỉ được tính vào sáu case nếu source/config/workload/topology và monitoring setup khớp suite đã khai báo; nếu khác, đánh dấu không so sánh được và phần coverage còn chờ, không tự thêm run. Cùng scenario-plan giữ thuật toán, quota, backend, key/workload và topology cố định, chỉ đổi mode cho từng so sánh. Đây là ma trận demo P2 mới, không phải bằng chứng nghiên cứu baseline. Không thêm lượt/retry hoặc dùng lại ngân sách P2-03; không mở P2-04, G4 outage hay T09/T10.

### P2-04 — Alloy/Loki

Tệp dự kiến: `deploy/monitoring/alloy/config.alloy`, `deploy/monitoring/loki.yml`, provisioning và Compose. Loki chạy một tiến trình local. Alloy giữ fixed-demo allowlist hiện có và thêm đúng project/service allowlist `project3-research-lab` `api1`…`api4`/`backend` cho run opt-in; không quét mọi project/container, Redis, Nginx hoặc access log từng request. Dùng labels ổn định `project`, `service`; không gắn Run ID. Xác minh Docker socket/API; `:ro` không làm Docker API read-only. Nếu không dùng được, ghi blocker hoặc chọn file input hẹp, không mount host rộng. Prometheus/Grafana không được mount Docker socket. Chỉ P2-04/05 đạt khi log pipeline đã kiểm chứng cho các nguồn được hỗ trợ; fixed-only evidence không chứng minh research logs.

### P2-05 — kiểm chứng logs/lifecycle

Trong G2, kiểm tra log thật từ cả fixed allowlist và run Console opt-in từ source tới Loki/Grafana, filter labels/container, delay/timezone/parse errors/positions/restart, datasource, permissions, health và disk. Kiểm tra runner đăng ký target/file, scrape/log startup trước/sau workload, cancel/SIGTERM cleanup và stale registration sau sự cố; không sửa ownership của stack fixed khi research runner dừng case riêng. Ghi rõ không có exactly-once guarantee. Hoàn tất khi metrics và logs hoạt động cùng nhau trên luồng đã chọn, restart/cleanup không ảnh hưởng project khác. G2 P2-03 fixed-only không được tính lại làm bằng chứng này.

### P2-06 — bounded demo load

Trước load, ghi đủ cấu hình/ngân sách vào `scenario-plan.md`; sau P2-03A dùng nút **Chạy benchmark** hiện có với monitoring opt-in, cùng `research-pilot.sh`/loadgen/topology cho tất cả case. P2-06 không dùng fixed-stack request mẫu hay một lệnh loadgen thay Console interaction acceptance. Ma trận **đề xuất** gồm tối đa **6 case**, normal/mixed × none/local/Redis; **30 giây/case**, tối đa **120 RPS**, một attempt/case. Case G3 đầu tiên là một trong sáu case; đây không phải comparison cell trên fixed stack. Để giữ so sánh, dùng cùng 2 API, FW `Q=20,W=1s`, backend capacity 4/service 50ms; normal 20 RPS, mixed tổng 120 RPS/hợp lệ 20 RPS; chỉ mode thay đổi. Mọi case đều bật cùng instrumentation và topology; P2-03A opt-in chỉ đổi cách thu telemetry, không đổi loadgen/đường request. Ghi sai khác runtime/instrumentation so với T09/T10 và không dùng làm formal baseline. Không đủ budget cho case thứ bảy, retry hay config change; cần yêu cầu/phạm vi mới. P2-06 vẫn cần G3 rõ; G2 không tự cấp tải.

### P2-07 — outage có điều kiện

Chỉ chạy khi yêu cầu bao phủ G4. Ngân sách riêng giữ nguyên: tối đa **4 case** healthy/outage × fail-open/fail-closed; **30 giây/case**, **20 RPS**, một attempt/case. Mỗi outage case pause Redis target của chính run đã khai báo **một lần 2 giây**, dự kiến tại giây 10; ghi thời điểm thực. Healthy references cùng config, không cộng ngầm vào P2-06. Hiện `scripts/redis-outage.sh` dựng project `project3-outage-$$` và tự chạy load; không dùng làm G4 Console hoặc pause Redis thuộc `project3-monitoring-demo` khi request đi qua `project3-research-lab`. Trước bất kỳ G4 nào cần một fault hook/lifecycle owner hẹp trong run hiện tại, trap/watchdog unpause, target identity verification và evidence/cleanup; nếu không thể làm trong một load path duy nhất thì giữ P2-07 chưa khả thi/blocked ở thiết kế, không thêm workflow tải. Không restart host Redis, FLUSHDB hay sửa clock/system config. Báo kết quả như demo fault injection, không phải HA/correctness/recovery protocol pass.

### P2-08 — đóng gói

Cập nhật runbook từ dự kiến thành đã thử, demo script, index và P2 source revision; giữ T12 bundle/IDs. Tạo offline fallback ghi riêng fixed P2-03 evidence và research opt-in case đã kiểm chứng: case/config/topology/revision, exact UTC load bounds, Grafana job/link, log query nếu P2-04/05 hoàn tất, limitations, recovery/cleanup. Kiểm tra fresh start/recovery bằng quyền tương ứng; người dùng tự xác nhận learning checklist. P2 cơ bản chỉ hoàn tất khi P2-01–P2-06 và P2-08 có evidence, đủ bốn công cụ, Console-run metrics/Grafana slice và offline fallback/recovery; logs pipeline phải hoàn tất để tuyên bố full monitoring. Ghi rõ trạng thái P2-07; G4 optional không phải điều kiện P2 cơ bản.
