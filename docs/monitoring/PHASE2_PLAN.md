# Giai đoạn 2 — kế hoạch monitoring và demo trực quan

Ngày lập: **23/10/2026**. Người dùng yêu cầu chuyển sang chuẩn bị giai đoạn 2 để học monitoring, nâng chất lượng demo và tạo nền kiến thức cho đồ án tốt nghiệp. Phiên lập kế hoạch do root tự thực hiện, không gọi worker.

**Điểm dừng ngày 23/10/2026: P2-01 đã xong kỹ thuật trong G1 triển khai và focused checks cục bộ.** Người dùng yêu cầu dừng sau P2-01; không bắt đầu P2-02, Docker/service, demo load, ngắt Redis hoặc chạy lại T09/T10. Việc có kế hoạch không cấp quyền runtime.

## 1. Đọc ít nhưng đủ để tiếp tục

1. Agent đọc [brief](../context/PROJECT_BRIEF.md), [chỉ mục nguồn](../context/SOURCE_INDEX.md), bắt đầu từ Roadmap, theo [AGENTS.md](../../AGENTS.md).
2. Đọc bảng task và gói đang làm trong tài liệu này. Đây là **nơi duy nhất cập nhật trạng thái chi tiết** `P2-*`; [kế hoạch chung](../REMAINING_WORK_PLAN.md) chỉ dẫn tới đây và quản lý T01–T13/H01–H02.
3. Đọc đúng phần liên quan trong [thiết kế](DESIGN.md), [runbook](RUNBOOK.md) hoặc [hướng dẫn học](LEARNING_GUIDE.md), rồi kiểm tra code cần sửa.
4. Chỉ mở [checkpoint](../context/SESSION_CHECKPOINT.md) nếu cần revision, artifact, kiểm tra hoặc điểm dừng phiên trước. Không đọc lại toàn bộ worklog, archive hoặc Drive khi nguồn không thay đổi.

Thứ tự triển khai mặc định: `P2-01 → P2-02 → P2-03 → P2-04 → P2-05 → P2-06 → P2-08`. P2-07 là nhánh outage có điều kiện, cần phạm vi chạy riêng. Không tự giao hoặc bắt đầu gói tiếp theo sau điểm dừng người dùng đã chọn.

## 2. Mục tiêu và ranh giới

Mạch trình bày: traffic flash sale giả định tăng → backend giới hạn năng lực bị ảnh hưởng → cần giới hạn request và quan sát quyết định → limiter local/Redis cùng pipeline monitoring → demo có kiểm soát → đọc xu hướng và giới hạn → kiến thức có thể dùng tiếp ở đồ án tốt nghiệp.

| Loại | Phạm vi |
| --- | --- |
| Yêu cầu baseline Project 3 từ nguồn | Nghiên cứu distributed rate limiter, mixed legitimate/abusive backend protection và outage có giới hạn; dashboard là tùy chọn |
| Mục tiêu giai đoạn 2 do người dùng chọn | Luồng local **Prometheus + Grafana + Alloy + Loki**, một dashboard, truy vấn metrics/logs, demo có thể lặp lại và học cách giải thích số liệu |
| Lựa chọn kỹ thuật cho kế hoạch này | Compose bổ sung; scrape endpoint mới; giữ JSON `/metrics`; monitoring stack cố định, tách runner Console; triển khai metrics trước logs |
| Để sau, chỉ làm nếu có nhu cầu mới | Histogram độ trễ, goodput live theo client class, alerting/Alertmanager, tracing/Tempo/OpenTelemetry, exporter Redis/host/container, tự discovery mọi Console run |
| Ngoài phạm vi hiện tại | Cloud, Kubernetes, HA, Redis Cluster, gateway, auth/RBAC platform, policy editor, hệ thống observability production |

Đủ bốn công cụ là đích của giai đoạn 2; Loki/Alloy không bị bỏ khỏi kế hoạch chỉ vì bản metrics làm trước. Outage live, histogram và alerting không phải điều kiện để bản cơ bản hoàn tất. Đây không phải thay đổi yêu cầu từ Drive hoặc rubric chính thức.

T13, rubric/phản hồi giảng viên, định dạng báo cáo và H01/H02 vẫn còn phần chưa hoàn tất; P2 không thay các việc đó. Ngày bảo vệ chính thức chưa được xác nhận; không suy có ngân sách thời gian chắc chắn từ mốc giữa tháng 12/2026 tạm tính.

## 3. Hiện trạng và những gì còn thiếu

Hiện trạng ngày 23/10 sau P2-01; chưa chứng minh runtime stack mới:

| Đã có | Thiếu / hệ quả | Nơi đối chiếu |
| --- | --- | --- |
| Bộ đếm atomic, JSON `GET /metrics` và Prometheus `GET /metrics/prometheus`, API/backend | P2-01 có focused checks; chưa có scrape qua Prometheus, giữ JSON mà Console/runner đang đọc | `internal/server/server.go`, `internal/console/console.go`, `scripts/research-pilot.sh` |
| Hai API, backend, Redis, Nginx trong Compose | Chưa có bốn service monitoring hoặc cấu hình/provisioning | `compose.yaml`, `deploy/nginx.conf` |
| JSON `slog` ra stdout | Log ứng dụng còn ít; cảnh báo Redis có thể phát theo từng request lỗi | `cmd/server/main.go`, `internal/server/server.go` |
| Saved-run Console và fallback T10 | Runner Console tạo project riêng; monitoring của stack cố định không tự quan sát runner | [gói T12](../DEMO_PACKAGE.md), `internal/console/console.go` |
| Summary/trace phía client | Chưa có histogram server, client-class metric hoặc goodput live trong Prometheus | `cmd/loadgen/`, [quy tắc phân tích](../experiments/ANALYSIS.md) |

Điểm dễ hiểu sai: `allowed` bằng 0 ở mode none; backend arrival không phải success; API/backend counters reset khi tiến trình restart; `up` chỉ nói scrape thành công; không có dữ liệu không đồng nghĩa giá trị 0. Hợp đồng đầy đủ ở [DESIGN.md](DESIGN.md).

## 4. Quyền thực hiện và cổng chuyển bước

| Cổng | Phạm vi | Trạng thái quyền hiện tại |
| --- | --- | --- |
| G0 — tài liệu | Khảo sát read-only, viết plan/design/runbook/học, kiểm tra tài liệu và commit | Được người dùng yêu cầu; hoàn tất ở P2-00 |
| G1 — triển khai | Sửa code/config/test theo gói, focused checks; không chạy stack hoặc load generator | Được phép riêng cho P2-01 trong phiên tiếp tục 23/10/2026 |
| G2 — smoke runtime | Build/start đúng project demo, scrape, mở browser, tối đa 10 request `/work` tuần tự; không pause Redis | Chưa được phép trong phiên này |
| G3 — demo tải giới hạn | Chạy cấu hình/thời lượng/RPS/case đã ghi trước theo P2-06; giữ mọi attempt, không chạy ma trận nghiên cứu | Chưa được phép trong phiên này |
| G4 — outage có kiểm soát | Pause/unpause đúng Redis của project demo, có cleanup và healthy reference theo P2-07 | Chưa được phép trong phiên này |

Đầu phiên tiếp tục, ghi lời yêu cầu thực tế của người dùng và các cổng được bao phủ. Nếu yêu cầu đã bao phủ triển khai cùng bounded smoke/demo thì tiếp tục trong giới hạn đó, không hỏi lại ở mỗi lệnh. Nếu chỉ yêu cầu code hoặc tài liệu thì dừng trước cổng runtime tương ứng. Ngưỡng ở đây là ngân sách demo đề xuất, không phải protocol nghiên cứu được khóa.

T09 có 138/138 slot dùng được, T10 đã phân tích xong. Giữ measurement source `0291a80fb404fea0eafee8c3431acc3631bb423e`, dataset/protocol/checksum và các giới hạn nguyên vẹn. Không gọi P2 là chạy lại T09/T10; không ghép telemetry mới vào bảng chính thức. Bất kỳ nghiên cứu/đo overhead mới nào phải có phạm vi và protocol riêng theo [readiness](../experiments/PROTOCOL_READINESS.md).

## 5. Sổ task giai đoạn 2

Trạng thái dùng: **Xong**, **Chưa bắt đầu**, **Đang làm**, **Chờ điều kiện**, **Bỏ qua có lý do**. Sửa trạng thái trong bảng này sau khi có kết quả, không suy từ việc file đã tồn tại. “Xong kỹ thuật” không thay xác nhận người học đã hiểu.

| ID | Gói việc | Phụ thuộc | Trạng thái / điểm nhận việc |
| --- | --- | --- | --- |
| P2-00 | Tài liệu nền, routing, checkpoint và commit | Không | **Xong** — bộ tài liệu được tạo trong phiên chuẩn bị 23/10/2026; xem checkpoint cho kiểm tra/commit |
| P2-01 | Endpoint Prometheus và hợp đồng metrics | P2-00, G1 | **Xong** — commit `0bea7b2`; focused server tests/vet đạt; chưa xác minh runtime stack |
| P2-02 | Compose bổ sung, Prometheus/Grafana và provisioning | P2-01, G1 | **Chưa bắt đầu** — gói tiếp theo; cần người dùng yêu cầu tiếp tục và mở G1 cho gói này |
| P2-03 | Dashboard metrics và smoke cơ bản | P2-02; G2 cho runtime | **Chưa bắt đầu** |
| P2-04 | Loki/Alloy và datasource logs | P2-02; sau P2-03 theo mặc định | **Chưa bắt đầu** |
| P2-05 | Kiểm chứng pipeline logs và vận hành stack đầy đủ | P2-03, P2-04; G2 | **Chưa bắt đầu** |
| P2-06 | Demo normal/mixed none/local/Redis | P2-05; G3 | **Chưa bắt đầu** |
| P2-07 | Demo Redis outage fail-open/fail-closed | P2-06; G4 | **Chờ điều kiện** — tùy chọn, không bắt buộc để hoàn tất bản cơ bản |
| P2-08 | Đóng gói, tài liệu sử dụng và diễn tập | P2-06; ghi rõ P2-07 có/không | **Chưa bắt đầu** |

### P2-01 — xuất metrics, giữ tương thích

**Kết quả 23/10/2026:** hoàn tất kỹ thuật ở `0bea7b2` với một worker `gpt-6-luna`, effort `low`; root tích hợp và kiểm tra staged diff. Endpoint xuất 10 counter API hoặc 4 counter backend từ atomic counters hiện có; giữ nguyên JSON, limiter, thời điểm tăng counter và bằng chứng nghiên cứu. Dùng thư viện chuẩn, không thêm dependency.

**Kiểm tra:** focused exposition/JSON tests và toàn bộ `go test ./internal/server` đạt với `GOCACHE=/tmp/project3-p2-01-gocache`; `go vet ./internal/server`, gofmt, `git diff --check` và liên kết nội bộ tài liệu đạt. Test bao phủ mapping từng counter bằng giá trị riêng, HELP/TYPE, role/mode, zero values, escaping, content type, JSON schema/giá trị và metrics/health không tăng counters `/work`. Cache mặc định bị sandbox chặn; chuyển cache sang `/tmp`. Suite server ban đầu bị chặn socket loopback của `httptest`, sau đó đạt khi cấp quyền cho fixture test tạm thời. Đây là kiểm tra package/handler, không phải xác minh runtime stack.

**Bỏ qua/giới hạn:** `promtool` không có sẵn; chưa dùng parser Prometheus độc lập, không tải tool/dependency mới. Scrape thực tế với công cụ/image phù hợp còn chờ P2-02/G2. Snapshot nhiều atomic counter không phải transaction. Không Docker/service ứng dụng, demo load, Redis outage, T09/T10 rerun hoặc P2-02; không tạo bằng chứng đo mới. Xác nhận học của người dùng vẫn riêng, chưa được ghi là hoàn tất. **Gói tiếp theo chính xác: P2-02**, cần yêu cầu tiếp tục mới; quyền G1 phiên này kết thúc ở P2-01.

- Đọc `internal/server/server.go`, `internal/server/server_test.go`, `internal/server/config.go`; tìm mọi caller `/metrics` trước khi sửa. Đọc phần metrics trong [thiết kế](DESIGN.md).
- Phạm vi file dự kiến: `internal/server/server.go`, `internal/server/metrics_prometheus.go` nếu tách giúp dễ đọc, focused tests trong `internal/server/`; cập nhật hợp đồng nếu cần. Không đổi limiter, runner, JSON schema, thời điểm tăng counter hay backend behavior.
- Xuất `GET /metrics/prometheus` từ đúng atomic counters, Prometheus text format, counter types, escaping đúng. Không thêm metric runtime/histogram hoặc dependency cho nhu cầu vài bộ đếm cố định; nếu cách làm tối thiểu không đủ đúng, ghi lý do trước khi đổi lựa chọn.
- Hoàn thành khi: JSON endpoint và các giá trị giữ nguyên; none/local/redis có ý nghĩa đúng; API/backend chỉ xuất họ metrics phù hợp; scrape/health không tăng bộ đếm `/work`; label escaping, content type, counter mapping được kiểm tra. Snapshot của nhiều atomic counter không phải transaction, không kiểm tra đẳng thức đồng thời thiếu cơ sở.
- Kiểm tra: focused server tests, format/vet cần thiết, parser/`promtool check metrics` nếu công cụ sẵn có; nếu chưa có parser thì ghi giới hạn, xác nhận bằng image được pin ở P2-02/G2. Không tải dependency/tool chỉ để phiên chuẩn bị có kết quả xanh.

### P2-02 — cấu hình stack metrics có thể tái lập

- File dự kiến: `compose.observability.yaml`, `deploy/monitoring/prometheus.yml`, `deploy/monitoring/grafana/provisioning/`; `.gitignore` chỉ sửa nếu thực sự cần bảo vệ state/credential. Không sửa Compose sinh bởi research runner.
- Pin phiên bản cụ thể cho bốn sản phẩm khi chọn image; ghi nguồn/version/config compatibility và image digest thực tế khi runtime cho phép. Không dùng tag `latest`; không ghi phiên bản dự đoán vào tài liệu như đã xác nhận.
- Dùng project riêng `project3-monitoring-demo` với `compose.yaml` + file bổ sung; Prometheus scrape service DNS trên cùng mạng. Kiểm tra cổng hiện có; tên project khác không giải quyết xung đột host port.
- Datasource Prometheus và provider dashboard được provision từ repo, UID ổn định; credential local không commit. Ghi lựa chọn storage/quota/retention, loopback binding, healthcheck không giả định image có shell/curl, log rotation và cleanup theo [runbook](RUNBOOK.md).
- Hoàn thành tĩnh khi Compose resolve được, đường dẫn mount đúng, cấu hình được validator phù hợp với image kiểm tra khi có công cụ. Không đánh dấu runtime pass từ `compose config`.

### P2-03 — dashboard đúng nghĩa và smoke metrics

- File dự kiến: `deploy/monitoring/grafana/dashboards/project3-overview.json`, cập nhật provisioning/runbook và focused query fixtures nếu logic truy vấn cần test.
- Tạo 6–8 panels theo [thiết kế](DESIGN.md), đơn vị rõ; title/description tiếng Việt và nhãn demo. Không tạo p95/goodput giả từ counter; không gộp backend success với client success.
- Với G2: tối đa 10 request tuần tự, lấy baseline sau khi scrape ổn định, đối chiếu delta JSON/exposition, kiểm tra cả hai API và backend; kiểm tra browser/query thực tế, không chỉ dashboard JSON parse.
- Hoàn thành khi targets scrape được, panel có dữ liệu đúng hoặc trạng thái thiếu mẫu rõ, restart/reset được giải thích; JSON Console vẫn hoạt động. Ghi URL/cấu hình/revision/kết quả/giới hạn rồi cleanup đúng project.

### P2-04 — pipeline logs Alloy → Loki

- File dự kiến: `deploy/monitoring/alloy/config.alloy`, `deploy/monitoring/loki.yml`, datasource Loki trong provisioning và service/volume liên quan trong Compose bổ sung.
- Loki một tiến trình local; Alloy lọc **đúng Compose project và allowlist service ứng dụng** trước khi đọc log. Không thu logs của mọi container hoặc chính pipeline theo mặc định.
- Chọn phương án Docker API/socket sau khi xác minh môi trường; ghi quyền truy cập rộng của socket, `:ro` không biến Docker API thành read-only. Không expose daemon TCP, không thêm `privileged`; nếu không thể dùng socket thì ghi blocker hoặc thiết kế file input riêng, không mount rộng thư mục host để lách.
- Labels nhỏ, JSON message giữ để truy vấn; không thêm success/reject access log cho mọi request. Không cần sửa app logs chỉ để có nhiều dữ liệu.
- Hoàn thành tĩnh khi cấu hình đúng cú pháp theo phiên bản đã pin, project/service filter rõ, state/retention/credentials có phương án; chưa có runtime thì chỉ ghi phần tĩnh đã đạt.

### P2-05 — kiểm chứng logs và vòng đời đầy đủ

- Với G2: khởi động stack đủ bốn công cụ, tìm `server started` thật từ API/backend trên Grafana Explore; không cần outage để kiểm tra log đầu tiên.
- Chứng minh filter bằng labels/source container thực tế; không thu service ngoài allowlist. Kiểm tra ingestion delay, timezone, parse errors, Alloy positions và hành vi restart, ghi rõ chưa có bảo đảm exactly-once.
- Kiểm tra datasource/UID, volume permissions, container health, log rotation và disk usage. Phân biệt `up`, healthz, Redis errors và pipeline logs bị gián đoạn.
- Hoàn thành khi từ source log tới Loki/Grafana có bằng chứng; cả metrics/logs chạy cùng nhau, dừng/start lại có hành vi được ghi; cleanup giữ đúng dữ liệu và project khác.

### P2-06 — demo traffic có giới hạn

- Trước load, ghi cấu hình và ngân sách trong `scenario-plan.md` mới; sử dụng loadgen hiện có trên stack cố định, không gọi research runner/Console Start để tạo stack khác.
- Điểm xuất phát đề xuất từ calibration lịch sử: FW `Q=20,W=1s`, hai API, backend capacity `4`, service time `50ms`; normal `20 RPS`, mixed tổng `120 RPS`/hợp lệ `20 RPS`. Phải kiểm tra lại key distribution và flags của loadgen trước khi chốt.
- Ngân sách đề xuất: tối đa **6 case**, normal/mixed × none/local/redis, **30 giây/case**, offered load tối đa **120 RPS**, một attempt/case; chưa cấp quyền chạy. Nếu cần retry hoặc đổi cấu hình, ghi lý do và phạm vi bổ sung, giữ attempt cũ. Không chạy liên tục vô hạn.
- Cố định thuật toán/policy/workload/key/backend/topology, chỉ đổi mode cho đối chứng. Chờ đủ mẫu và chọn time range từng case; tránh data cũ sau restart làm người xem nhầm. Backend overload hoặc local/Redis khác nhau là giả thuyết cần quan sát, không là kết quả bảo đảm.
- Ghi sent/drops/errors từ loadgen, config thực tế, UTC start/end, screenshots/query và diễn giải. Bộ đếm sampled/rate không thay exact request trace; không gọi nominal RPS là achieved RPS nếu chưa kiểm tra. Demo không có gate benchmark chính thức.

### P2-07 — nhánh outage có điều kiện

- Chỉ làm khi người dùng yêu cầu phạm vi G4. Lập plan trước; đề xuất tối đa **4 case**: healthy/outage × fail-open/fail-closed, **30 giây/case** ở normal **20 RPS**, một attempt/case. Mỗi case outage pause Redis **một lần 2 giây**, dự kiến tại giây 10; ghi thời điểm thực tế. Hai healthy references phải cùng cấu hình tương ứng và nằm trong ngân sách riêng này, không tự cộng vào P2-06.
- Chuẩn bị cleanup unpause trong trap/watchdog được kiểm chứng trước thao tác; xác minh project/container sở hữu. Không restart host Redis, FLUSHDB, thay clock hoặc thay cấu hình hệ thống.
- Đối chiếu cảnh báo `limiter unavailable`, `limiter_errors`, `fail_open`/`fail_closed`, backend traffic và kết quả client. API vẫn có thể `up=1` khi Redis lỗi.
- Hoàn thành khi ghi đúng thời điểm yêu cầu/thực hiện pause/unpause và cleanup; không diễn giải thành HA, quota correctness pass hoặc stable recovery theo protocol T07/T09. Nếu chưa làm, ghi “chưa thực hiện” hoặc bỏ qua có lý do.

### P2-08 — đóng gói và bàn giao

- Cập nhật [runbook](RUNBOOK.md) từ dự kiến thành lệnh đã thử; cập nhật [demo hiện tại](../DEMO_SCRIPT.md), reader index và source revision P2. Không ghi đè bundle T12 hoặc đổi original pilot IDs.
- Tạo ảnh/video fallback có tên case, mode/config/time range, nhãn demo, revision và giới hạn; không sinh lại hình T10. Kiểm tra fresh start, dừng đúng project và khả năng trình bày offline.
- Đối chiếu checklist học với người dùng; ghi phần chưa tự giải thích được, không tự đánh dấu đã hiểu. Liên kết nội dung nào hữu ích cho đồ án tốt nghiệp, phần nào vẫn chưa triển khai.
- Hoàn thành bản cơ bản khi P2-01–P2-06 và P2-08 có bằng chứng/checks, bốn công cụ hoạt động, có đường phục hồi và fallback; P2-07 ghi trạng thái rõ. Nếu chỉ xong metrics thì báo milestone metrics, không tuyên bố xong giai đoạn 2.

## 6. Bàn giao giữa các phiên và commit

- Mỗi lần chỉ nhận một gói hoặc tập gói độc lập được yêu cầu; kiểm tra `git status` và giữ nguyên file người dùng/ignored artifacts.
- Commit feature/fix cùng focused tests trực tiếp liên quan; logs/screenshots/evidence riêng; cập nhật tiến độ/checkpoint riêng. Stage tệp/hunk cụ thể và đọc staged diff trước mỗi commit. Không push nếu chưa được yêu cầu.
- Artifact theo [runbook](RUNBOOK.md); worklog chỉ ghi tóm tắt và liên kết, không đổ raw log vào chat. Không commit credentials, TSDB/chunks hoặc dữ liệu volume.
- Cuối phiên: cập nhật sổ task ở đây, checkpoint cho revision/checks/artifacts/process, brief chỉ giữ trạng thái ngắn và link. Không nhân bản toàn bộ task list vào nhiều file.

**Khối tiếp tục dành cho agent — English; người học có thể bỏ qua:**

```text
Phase 2 resumption: read AGENTS.md and mandatory project sources, then the P2 task
registry in docs/monitoring/PHASE2_PLAN.md. Take only the requested ready package.
P2-01 is technically complete. Next package: P2-02, only after the user resumes
that scope and authorizes its G1 work. Inspect its exact code and callers, read only the relevant DESIGN/RUNBOOK sections, and record the user's
authorized gates. Planning is not permission for runtime, load or Redis outage.
Preserve JSON /metrics, Console compatibility and all T09/T10 evidence. Use a named
fixed demo stack; do not automatically integrate the Console research runner.
Honor any root-only/no-delegation request. Otherwise follow the current AGENTS.md
delegation policy; do not infer authorization to start the next package at a stop.
Report task IDs, files, checks and skips, remaining limits, next prerequisite,
commits, owned processes and artifact paths. For runtime also record revision,
resolved config, image identities, UTC times, request budget and artifact hashes.
```
