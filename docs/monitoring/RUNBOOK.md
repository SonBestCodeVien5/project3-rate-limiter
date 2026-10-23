# Runbook dự kiến cho demo monitoring

**Trạng thái runtime:** P2-01/P2-02 hoàn tất; G2 của P2-03 đang được kiểm chứng theo yêu cầu cho phép. Dashboard đã được provision từ `deploy/monitoring/grafana/dashboards/project3-overview.json`; kết quả thật của lượt kiểm chứng được ghi trong [sổ task P2](PHASE2_PLAN.md) và [checkpoint](../context/SESSION_CHECKPOINT.md). Chỉ các target, query và thao tác có bằng chứng runtime mới được coi là đã kiểm tra. [Thiết kế](DESIGN.md) quy định metrics/labels, [kế hoạch chung](../REMAINING_WORK_PLAN.md) quản lý baseline, [readiness](../experiments/PROTOCOL_READINESS.md) quản lý phép đo nghiên cứu.

## 1. Trước khi chạy

1. Xác nhận task/gate được người dùng tiếp tục trong [kế hoạch P2](PHASE2_PLAN.md). Commands dưới đây không tự cấp quyền runtime, tải hay outage.
2. Kiểm tra working tree và giữ file người dùng, template HUST, ignored artifacts, T12 bundle, evidence và volumes. Không prune Docker hoặc xóa dữ liệu chưa xác minh ownership.
3. Trước runtime, ghi version Docker/Compose, Go, browser, ports và tài nguyên máy. Image dùng tag đã pin trong overlay; ghi image ID/digest thực tế khi đã tải.
4. Demo dùng project riêng `project3-monitoring-demo`; không điều khiển nhầm `project3-research-lab` hay `project3-rate-limiter`. Kiểm tra đủ host ports base `8080`, `18081`, `18082`, `18083`, `16379` và ports monitoring `13000` (Grafana), `19090` (Prometheus).
5. Không chạy đồng thời research load/observer; không sửa clock/NTP, protocol hoặc dataset để phục vụ demo.

Tạo password local cho Grafana trong thư mục bị ignore, chỉ khi file chưa tồn tại. Thư mục `0700` giới hạn truy cập trên host; file mới được mount trực tiếp nên đặt ở chế độ đọc được trong container. Nếu đã có file, giữ và dùng lại credential đó: thay file không tự đổi mật khẩu trong Grafana database đang lưu trên volume. Không ghi secret hoặc password file vào evidence.

```bash
umask 077
mkdir -p .secrets
chmod 700 .secrets
if [ ! -e .secrets/grafana_admin_password ] && [ ! -L .secrets/grafana_admin_password ]; then
  openssl rand -base64 32 > .secrets/grafana_admin_password
  chmod 444 .secrets/grafana_admin_password
fi
export GRAFANA_ADMIN_PASSWORD_FILE="$PWD/.secrets/grafana_admin_password"
```

## 2. Kiểm tra trước runtime

Lệnh sau resolve base và overlay, không khởi động service. Khai báo biến password file theo bước trên trước khi chạy.

```bash
# Xem trạng thái nguồn trước khi sửa hoặc chụp evidence.
git status --short
git rev-parse HEAD

# Chỉ resolve cấu hình, không khởi động service.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml config
```

Compose config chỉ xác nhận cấu hình hợp nhất; nó không thay validator Prometheus/Loki/Alloy hoặc browser check. `promtool` không có sẵn. Ghi riêng check tĩnh và runtime; không tuyên bố runtime pass chỉ từ config. Không lưu resolved config nguyên trạng nếu có thông tin nhạy cảm; password file chỉ lộ đường dẫn host.

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

## 4. Demo tải — G3

Chỉ tiếp tục theo P2-06 sau khi gate G3 được cho phép. Không dùng pilot/research/outage scripts để tạo dashboard. Trước batch, lưu `scenario-plan.md` với mode/policy/topology/backend, workload/key, offered load/duration/bounds, drain/reset, time range và attempt budget theo registry. Kiểm tra flags/key distribution; dùng loadgen trực tiếp trên ingress P2.

Mỗi case: xác minh resolved config/image identity và namespace Redis riêng; ghi UTC start sau khi healthy/sample nền; chạy trong ngân sách cố định; lưu command/summary/trace/sent/drops/errors; drain, ghi UTC end và query/time range; giữ mọi attempt, kể cả lỗi hoặc thiếu mẫu. Không suy client goodput từ backend counters, không retry/chọn lượt đẹp nếu phạm vi không cho phép.

## 5. Redis outage — G4

Chỉ thực hiện theo P2-07 sau khi gate G4 được cho phép. Trước thao tác, xác minh Redis container thuộc đúng project `project3-monitoring-demo`, ghi healthy reference/cấu hình và thời điểm/budget, kiểm tra cleanup trap/watchdog unpause. Không restart host Redis, `FLUSHDB`, đổi clock hoặc cấu hình hệ thống. Sau đó xác nhận unpaused, drain và cleanup; lưu thời điểm thực tế. `up=1` không chứng minh Redis khỏe; fail-open có thể tăng backend traffic, fail-closed 503 khác quota 429. First success không đồng nghĩa stable recovery.

## 6. Dừng và giữ dữ liệu

Sau khi ghi artifact, chỉ dừng project của phiên bằng đúng bộ file/env:

```bash
# Dừng stack demo; giữ named volumes để xem lại dữ liệu.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml down
```

Không dùng `down -v`, `docker system prune`, `volume prune` hoặc xóa artifact làm cleanup mặc định. Nếu cần reset dữ liệu demo, xác định chính xác volume/project, lưu phần cần giữ và áp dụng quyền xóa đã có; không suy dữ liệu ignored là có thể bỏ.

Giữ TSDB trên volume riêng `project3-monitoring-demo`; Prometheus đặt retention 24h và 512MB cho blocks. WAL/metadata có thể khiến volume vượt retention size; đây không phải hard disk quota. Prometheus/Grafana memory limit là 512 MiB mỗi service; log rotation mỗi service là 10 MiB × 3 file. Đây là cấu hình ban đầu, chưa đo hoặc runtime xác minh; theo dõi dung lượng trước khi tăng thời lượng. Loki filesystem cần retention/cleanup riêng khi P2-04 được làm. Không commit credentials; lọc env nhạy cảm khỏi `docker inspect` evidence. Nếu Alloy cần Docker socket, chỉ mount vào Alloy: `:ro` không làm Docker API read-only, không expose daemon TCP/`privileged`; lọc project `project3-monitoring-demo` và allowlist `api1`, `api2`, `backend`. Filter giới hạn logs thu, không phải security boundary. Ghi trước/sau containers/process, paused state, ports, volumes và vị trí credentials; bàn giao cách dừng nếu để stack chạy.

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

## 8. Tra lỗi

| Hiện tượng | Kiểm tra | Tránh kết luận |
| --- | --- | --- |
| Target DOWN | DNS/network, port/path, content type, timeout, response | Không tự gọi là Redis outage |
| Target UP, panel trống | metric/labels, role, sample, datasource/time range | Không đổi null thành 0 |
| none có allowed=0 | semantics limiter, backend attempts | Không sửa counter |
| Backend success khác API response | transport, overload, drain, nguồn counter | Không gọi server success là client goodput |
| Loki thiếu/lặp log | project/service filter, socket, positions, readiness, timestamps | Không thu rộng hơn hoặc hứa exactly-once |
| Máy chậm/đĩa tăng | containers, log rate, storage/retention, tải | Không định lượng overhead bằng cảm nhận |

Nếu live demo chưa ổn, dùng [kịch bản và fallback T12](../DEMO_SCRIPT.md); chỉ dùng ảnh/video P2 đã tạo và kiểm tra thật.
