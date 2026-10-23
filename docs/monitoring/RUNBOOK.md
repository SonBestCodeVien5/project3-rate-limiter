# Runbook dự kiến cho demo monitoring

**Chưa phải hướng dẫn đã chạy thành công.** Ngày 23/10/2026 mới chuẩn bị tài liệu; file Compose/config P2 chưa được tạo. Chỉ dùng các bước runtime sau khi task và quyền tương ứng trong [kế hoạch P2](PHASE2_PLAN.md) được tiếp tục. [Thiết kế](DESIGN.md) quy định metrics/labels; [kế hoạch chung](../REMAINING_WORK_PLAN.md) quản lý việc baseline, [readiness](../experiments/PROTOCOL_READINESS.md) vẫn quản lý phép đo nghiên cứu.

## 1. Trước khi sửa hoặc chạy

1. Xác nhận task đang làm, phạm vi người dùng đã yêu cầu và điểm dừng. Không tự chạy Docker/load vì thấy command trong tài liệu.
2. Kiểm tra working tree; giữ file người dùng, template HUST, ignored artifacts, T12 bundle và measurement evidence. Không prune Docker hoặc xóa thư mục chưa xác minh ownership.
3. Khi cần runtime, kiểm tra Docker/Compose, Go, browser, port và tài nguyên máy; ghi version thực tế. Không cài tool hoặc pull image trong phiên chỉ làm tài liệu.
4. Project demo dự kiến `project3-monitoring-demo`; research project `project3-research-lab` và project mặc định `project3-rate-limiter` không được điều khiển nhầm. Khác project vẫn xung đột cổng app `8080`, `18081`, `18082`, `18083`, `16379`.
5. Không chạy load/observer nghiên cứu khác cùng lúc; chỉ dừng process thuộc phiên hoặc được người dùng cho phép. Không sửa clock/NTP, protocol hoặc dataset để phục vụ demo.

## 2. Kiểm tra trước runtime

Lệnh dưới đây dành cho **sau khi file P2 được triển khai**, từ repo root; chưa chạy ở phiên lập kế hoạch:

```bash
# Xem trạng thái nguồn trước khi sửa hoặc chụp evidence.
git status --short
git rev-parse HEAD

# Chỉ resolve cấu hình, không khởi động service.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml config
```

Compose config không thay validator Prometheus/Loki/Alloy hoặc browser check. Dùng validator sẵn có/đi kèm image đã pin theo đúng version; không ghi pass nếu validator chưa chạy. Kiểm tra JSON dashboard parse và UID/datasource bằng cấu hình, rồi xác nhận runtime ở bước sau.

Focused checks cho P2-01 phải kiểm tra escaping, counter semantics, JSON endpoint và scrape không tính như `/work`. Khi đổi code mới chạy checks phù hợp; tài liệu-only không cần code suite/live run. Không chạy cả research matrix để kiểm tra một endpoint.

## 3. Start và smoke có giới hạn — G2

Trước start, tạo output mới theo mục 7, ghi env/config đã resolve và image tags được chọn; không ghi mật khẩu vào evidence. Kiểm tra chưa có stack khác chiếm cổng. Những lệnh dưới đây là mẫu cho cấu hình mặc định; khi thử case khác phải truyền cùng env cho các lệnh Compose liên quan và lưu config thực tế.

```bash
# Chỉ dùng khi đã được tiếp tục runtime; image/config phải được pin trước.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml up -d --build --wait

docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml ps
```

Không coi `--wait` là kiểm chứng toàn pipeline; healthcheck phải tồn tại và phù hợp image. Start thất bại thì giữ log lỗi, xác định container thuộc project, không lặp up/rebuild vô hạn.

Checklist smoke:

- API/backend JSON `/metrics` vẫn trả cùng schema; exposition endpoint có format/labels đúng.
- Prometheus targets `api1`, `api2`, `backend` scrape được; datasource Grafana đúng URL nội bộ và UID. Nếu các host port debug không publish thì kiểm tra từ đúng network, không mở toàn interface để tiện curl.
- Lấy baseline sau khi scrape ổn định; tối đa **10 request `/work` tuần tự** tổng cộng cho một gói smoke, dùng ID hợp lệ, ghi count/status và delta. Scrape probes không tính vào ngân sách `/work` và không làm tăng counters app.
- Ví dụ một request, không phải lệnh tạo loop/load:

```bash
curl --max-time 5 -i -X POST -H 'X-Client-ID: demo-buyer-1' \
  http://127.0.0.1:8080/work
```

- Counter delta ở trạng thái đã drain phù hợp từng nguồn; không bắt rate/increase của Prometheus bằng exact count. Chưa đủ sample thì ghi chờ/thiếu mẫu, không báo hỏng hoặc ép 0.
- Browser mở được dashboard đúng panels/units; saved Console JSON caller vẫn tương thích. Không bấm Start benchmark của Console để kiểm tra stack này.
- Khi P2-04 đã triển khai: thấy log startup thật từ service allowlist trong Loki/Grafana; ghi source timestamp, ingestion delay và labels. Không gây outage ở G2 chỉ để có warning.
- Ghi kiểm tra reset/restart/positions đã làm và chưa làm. Nếu restart cần thêm request vượt ngân sách thì ghi phạm vi mới trước khi tiếp tục.

## 4. Diễn tập tải — G3

Không chạy các script pilot/research/outage lịch sử như shortcut để tạo dashboard. Loadgen hiện có được dùng trực tiếp trên ingress stack P2 sau khi kiểm tra flags, identity/key distribution và timeout.

Trước mỗi batch, ghi `scenario-plan.md` gồm: câu hỏi demo; mode/algorithm/policy; API count; backend capacity/service time; workload/keys; RPS/duration/request bound; cách drain/reset; time range và attempt budget. Ngân sách khởi đầu đề xuất ở P2-06, không phải quyền chạy hiện tại.

Trình tự một case:

1. Xác minh env/Compose resolved và image identities thực tế. Tách namespace Redis cho demo; không FLUSHDB.
2. Start/recreate đúng case, chờ healthy và đủ sample nền, ghi UTC start; không đổi cấu hình trong case.
3. Chạy load có thời hạn; lưu command, summary/trace và sent/drops/errors. Dừng khi quá ngân sách, process lỗi hoặc máy có vấn đề; không nới tải/thời gian để tạo hình đẹp.
4. Drain request, ghi UTC end, chọn khoảng dashboard không cắt qua mode transition; lưu query/time range/screenshot.
5. Đọc request API, reject, backend arrivals/success/overload; nói rõ dữ liệu client-class/goodput nằm ở summary nếu đã lấy đúng, không suy từ backend.
6. Giữ attempt dù kết quả khác kỳ vọng; ghi chưa thấy khác biệt hoặc chưa đủ mẫu. Chỉ retry khi phạm vi thực tế cho phép, không tự chọn lượt đẹp.

## 5. Redis outage — chỉ G4

Không có lệnh pause thực thi sẵn ở đây vì cần xác minh ownership và cleanup của gói P2-07 trước. Trước khi thao tác phải có:

- Case/healthy reference cùng workload/policy/backend/topology được ghi trước, thời điểm pause và budget cụ thể.
- Redis container ID thuộc **đúng** `project3-monitoring-demo`; không nhầm Redis host hoặc research stack.
- Cleanup trap/watchdog unpause đã kiểm tra, kể cả khi loadgen hoặc terminal lỗi; giới hạn pause đề xuất 2s/case chưa phải thao tác đã được phép.
- Sau sự cố: xác nhận unpaused, requests đã drain, trạng thái cuối và process còn lại; ghi trường hợp không khôi phục được, không âm thầm rời phiên.

Đọc metrics/logs cùng nhau: `up=1` vẫn có thể đi với limiter errors; fail-open có thể tăng backend traffic; fail-closed 503 khác quota 429. Không gọi thời điểm request đầu tiên thành công là stable recovery theo protocol cũ.

## 6. Dừng và giữ dữ liệu

Sau khi ghi artifact, chỉ dừng project của phiên bằng đúng bộ file/env:

```bash
# Dừng stack demo; giữ named volumes để xem lại dữ liệu.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml down
```

Không dùng `down -v`, `docker system prune`, `volume prune` hoặc xóa artifact làm cleanup mặc định. Nếu cần reset dữ liệu demo, xác định chính xác volume/project, lưu phần cần giữ và áp dụng quyền xóa đã có; không suy dữ liệu ignored là có thể bỏ.

Ghi trước/sau: containers/process nào do phiên tạo, paused state nếu có, host ports còn bind, volumes giữ lại, vị trí credentials. Nếu để stack chạy theo yêu cầu người dùng, ghi cách dừng và chi phí tài nguyên; không để background vô thời hạn mà không bàn giao.

## 7. Bằng chứng và mẫu bàn giao

Output mới, không ghi đè, dự kiến:

```text
artifacts/monitoring/<batch-id>/
  scenario-plan.md       # Cấu hình, mục đích và ngân sách đã ghi trước
  source.txt            # Revision và trạng thái working tree thực tế
  compose.resolved.yaml # Bản đã loại bỏ credential trước khi lưu/chia sẻ
  images.json           # Tag, image ID/digest thực tế; thiếu thì ghi thiếu
  checks.md             # Kiểm tra, kết quả, lỗi/bỏ qua, cleanup
  cases/<case-id>/      # Command, UTC times, JSON snapshots, loadgen output
  screenshots/          # Dashboard/Explore kèm query/time range
  SHA256SUMS            # Hash artifact đã chốt, không gồm chính manifest hash
```

Batch/case ID là metadata artifact, không thành indexed label. File chưa tạo không được dẫn như bằng chứng đã có. Không lưu token/mật khẩu, Docker inspect env chưa lọc, Loki chunks hoặc Prometheus TSDB vào Git.

Sau khi artifact chốt, hash một lần; nếu sửa thì tạo bản mới hoặc ghi manifest mới có lý do. Worklog ngày thực hiện trong `docs/worklog/` chỉ chứa tóm tắt đã loại secrets và link/path/checksum cần thiết. Ghi rõ dirty source nếu có; không giả định HEAD mô tả patch chưa commit.

Cuối mỗi phiên cập nhật [sổ task](PHASE2_PLAN.md) và [checkpoint](../context/SESSION_CHECKPOINT.md): task/substep, quyền đã dùng, files/commits, checks pass/fail/skip, revision/config/artifacts/hashes, process/volumes, giới hạn và việc tiếp theo. Không ghi root đã xác nhận runtime khi chỉ đọc báo cáo hoặc cấu hình.

## 8. Tra lỗi theo lớp

| Hiện tượng | Kiểm tra đầu tiên | Điều không được kết luận vội |
| --- | --- | --- |
| Target DOWN | Service DNS/network, port/path, content type, timeout và response thật | Không tự gọi là Redis outage |
| Target UP nhưng panel trống | Tên metric/labels, đúng role, đủ sample, datasource/time range | Không đổi null thành 0 để che lỗi |
| none có allowed=0 | Semantics limiter và panel backend attempts | Không sửa counter cũ chỉ để đồ thị tăng |
| Backend success khác API responses | Transport, overload, drain, từng nguồn counter | Không xem server success là client goodput |
| Không có log Loki | Project/service filter, socket permissions, positions, Loki readiness và time range | Không tăng log mọi request trước khi tìm nguyên nhân |
| Log lặp/sai thứ tự sau restart | Source timestamps, positions/storage và ingestion delay | Không cam kết exactly-once hoặc sửa raw timestamp |
| Máy chậm/đĩa tăng | Containers/log rate/storage/retention và tải đang chạy | Không công bố overhead định lượng từ cảm nhận |

Nếu live demo chưa ổn, dùng [gói T12](../DEMO_PACKAGE.md) và [kịch bản hiện có](../DEMO_SCRIPT.md); ảnh/video P2 chỉ được dùng sau khi tạo và kiểm tra thật.
