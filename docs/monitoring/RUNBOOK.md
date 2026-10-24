# Runbook vận hành demo monitoring

**Trạng thái runtime:** P2-01/P2-02 hoàn tất; P2-03 G2 đã kiểm tra trên project `project3-monitoring-demo`. Cả ba scrape targets lên; JSON/exposition giữ contract; Grafana datasource/dashboard provision thành công; 11 PromQL expressions trả kết quả; browser cuộn qua dashboard và xác nhận đủ bảy panel. Người dùng sau đó mở lại stack để học; kiểm tra 23/10/2026 phát hiện folder/dashboard UID trùng khiến trang danh sách Grafana lặp đệ quy. Provider hiện dùng folder UID riêng `project3-monitoring-folder`, giữ dashboard UID `project3-monitoring-demo`; đã kiểm tra lại list, folder expansion, dashboard và targets. Stack được để chạy theo yêu cầu người dùng; chi tiết sửa lỗi và kiểm tra tại [bằng chứng sửa lỗi UID](../../artifacts/monitoring/grafana-uid-collision-fix/checks.md). G2 ban đầu, lệnh, giới hạn, UTC bounds và kết quả nằm trong [G2 smoke evidence](../../artifacts/monitoring/p2-03-g2/checks.md). [Thiết kế](DESIGN.md) quy định metrics/labels, [kế hoạch P2](PHASE2_PLAN.md) quản lý task state, [kế hoạch chung](../REMAINING_WORK_PLAN.md) quản lý baseline, [readiness](../experiments/PROTOCOL_READINESS.md) quản lý phép đo nghiên cứu.

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

### Quyền thư mục `file_sd`

Trước khi bật Compose monitoring, tạo và kiểm tra thư mục host được mount vào Prometheus. File target chỉ chứa alias và labels, nhưng Prometheus chạy với UID `nobody` nên manifest cần quyền đọc cho mọi user. Runner cũng kiểm tra thư mục do user hiện tại sở hữu, đọc/ghi/traverse được trước khi khởi chạy research resources; khi monitoring tắt, bước này không chạy.

```bash
target_dir=artifacts/monitoring/console-targets
mkdir -p "$target_dir"
stat -c '%U:%G %a %n' "$target_dir"
test -O "$target_dir" && test -r "$target_dir" && test -w "$target_dir" && test -x "$target_dir"
```

Nếu thư mục cụ thể này bị Docker tạo thành `root`-owned, trước hết xác nhận không có runner đang hoạt động và không còn `active.json`; chỉ sửa quyền sở hữu chính thư mục đó, không dùng `-R` hoặc chmod/chown thư mục cha:

```bash
sudo chown "$(id -u):$(id -g)" artifacts/monitoring/console-targets
```

Không xóa hoặc đổi quyền một manifest còn hoạt động. Runner từ chối khởi chạy opt-in nếu ownership/quyền không đạt; thông báo lỗi trỏ về mục này.

```bash
# Xem trạng thái nguồn trước khi sửa hoặc chụp evidence.
git status --short
git rev-parse HEAD

# Chỉ resolve cấu hình, không khởi động service.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml config
```

Compose config chỉ xác nhận cấu hình hợp nhất; nó không thay validator Prometheus/Loki/Alloy hoặc browser check. `promtool` không cài trên host; có thể chạy validator từ pinned Prometheus image như đã ghi ở bằng chứng P2-03. Ghi riêng check tĩnh và runtime; không tuyên bố runtime pass chỉ từ config. Không lưu resolved config nguyên trạng nếu có thông tin nhạy cảm; password file chỉ lộ đường dẫn host.

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
- Prometheus fixed targets `fixed-api1`, `fixed-api2`, `fixed-backend` scrape được; datasource Grafana đúng URL nội bộ và UID. Nếu các host port debug không publish thì kiểm tra từ đúng network, không mở toàn interface để tiện curl.
- Lấy baseline sau khi scrape ổn định; tối đa **10 request `/work` tuần tự** tổng cộng cho một gói smoke, dùng ID hợp lệ, ghi count/status và delta. Scrape probes không tính vào ngân sách `/work` và không làm tăng counters app.
- Ví dụ một request, không phải lệnh tạo loop/load:

```bash
curl --max-time 5 -i -X POST -H 'X-Client-ID: demo-buyer-1' \
  http://127.0.0.1:8080/work
```

- Counter delta ở trạng thái đã drain phù hợp từng nguồn; không bắt rate/increase của Prometheus bằng exact count. Chưa đủ sample thì ghi chờ/thiếu mẫu, không báo hỏng hoặc ép 0.
- Browser mở dashboard đúng panels/units; saved Console JSON caller vẫn tương thích. Request mẫu kiểm tra fixed ingress; nó không kiểm tra đường Prometheus tới research runner.
- Khi P2-04 đã triển khai: thấy log startup thật từ service allowlist trong Loki/Grafana; ghi source timestamp, ingestion delay và labels. Không gây outage ở G2 chỉ để có warning.
- Ghi kiểm tra reset/restart/positions đã làm và chưa làm. Nếu restart cần thêm request vượt ngân sách thì ghi phạm vi mới trước khi tiếp tục.

**P2-03A — scrape run Console hiện có:** G1 đã triển khai opt-in và focused checks; G2/G3 runtime acceptance còn chờ. Khi đã được phép chạy runtime, `Gửi một request mẫu` vẫn vào fixed stack `project3-monitoring-demo`. Nút **Chạy benchmark** tiếp tục gọi `research-pilot.sh` tạo topology trong `project3-research-lab`. Checkbox opt-in trên cùng form yêu cầu runner hiện tại đăng ký API/backend target của case qua `project3-monitoring-scrape` và Prometheus `file_sd`; không tạo generator/workflow mới, không mount Docker socket. Fixed job `project3-demo` vẫn chỉ dành cho stack cố định; research job `project3-console-run` hiển thị riêng. Cấu hình hiện dùng file SD refresh 1s, scrape 1s, rate window 4s và lookback 4s; các khoảng này chưa runtime-validated. Sau khi xác nhận target `UP` và baseline scrape mới, runner đợi lookback 4s trước workload, không phát `/work`; ghi riêng khoảng setup/overhead, không cộng vào hoặc lấy khỏi duration benchmark. Thiếu target/config sai thì fail trước khi tải. Giữ `api1`…`api4` + `backend` allowlist, không đăng ký Redis/Nginx; không đưa Run ID vào metric labels.

Mỗi repeat là một case riêng: ghi target/topology/config hiệu lực, revision + dirty state, image IDs, UTC load start/end chính xác, baseline, lookback window, drain và final-scrape time trong artifacts. Giữ nguyên duration yêu cầu; khoảng quan sát trước tải không phát `/work` và không tính vào benchmark. Console link dùng UTC load bounds chính xác của case, không shift `from` để che đầu workload. Runner chờ Prometheus không còn series `up` của case trước trước khi đăng ký case mới, rồi ghi riêng baseline/lookback phase; nếu cách ly không xác nhận được thì fail trước load; nếu sample thiếu hoặc query vẫn bị nhiễm, ghi incomplete thay vì điều chỉnh duration/range ngầm. Gỡ manifest target trước scoped Compose cleanup. Prometheus named volume giữ samples sau khi case được cleanup theo retention 24h. Console link tới dashboard UID `project3-monitoring-demo`, folder UID `project3-monitoring-folder`, datasource UID `project3-prometheus`, selector `job=project3-console-run` và UTC load range. Selector không gộp fixed-stack traffic hoặc case khác. Monitoring Compose sở hữu external network `project3-monitoring-scrape`; research runner chỉ nối service allowlist, không tạo/xóa network. Nếu còn manifest từ lần bị kill, không tự quét/xóa; runner từ chối đăng ký mới cho tới khi ownership được xác minh và file cũ được dọn an toàn. Target DOWN/absent và scrape gap được ghi là thiếu; không ép về 0. Fixed job dùng alias `fixed-*`, Console file_sd dùng `console-*` để tránh DNS mơ hồ trên shared network. Runner đăng ký target sau khi Compose healthy và JSON baseline được lưu; sau lookback phải xác nhận target UP lại. Final scrape phải mới hơn thời điểm generator drain; cleanup chỉ gỡ manifest nếu nội dung còn khớp targets đã đăng ký.

Fixed stack dùng scrape 2s/rate 20s. Research dùng scrape 1s, `file_sd` refresh 1s và rate window 4s; các timing này chưa runtime-validated; không bảo đảm rate ổn định, nhất là case 3s. Không đổi duration hoặc protocol để lấp mẫu; báo thiếu/thưa/inconclusive. P2-06 G3 acceptance dùng tối đa 30s và cần xác minh timing thực tế. Opt-in research run đổi network/runtime và chỉ là telemetry demo mới; ghi phần setup/scrape overhead riêng, không đổi measurement source hoặc kết luận T09/T10. G2 cũ của P2-03 không dùng lại; một request mẫu không chứng minh integration, G3 phải chạy đúng nút **Chạy benchmark** đã opt-in và thấy API/backend samples trong Grafana.

## 4. Demo tải — G3

Chỉ tiếp tục P2-06 sau khi P2-03A đã qua các gate cần thiết và G3 được cho phép. Trước batch, lưu `scenario-plan.md` với mode/policy/topology/backend, workload/key, offered load/duration/bounds, drain, time range và budget. Dùng đúng nút Console **Chạy benchmark** hiện có với monitoring opt-in; không dùng CLI/research script thay cho G3 Console acceptance. Chạy cả ma trận qua cùng `research-pilot.sh`, loadgen, 2 API + backend và cùng cấu hình, chỉ đổi mode; đây là topology của Console research runner, tách khỏi fixed-stack traffic.

Ngân sách tổng tối đa **6 case**, **30 giây/case**, **120 RPS**, **1 attempt/case**; G3 acceptance dùng một trong sáu, không thêm case thứ bảy. Mỗi case xác minh Compose/policy/image identity và namespace Redis mới; đợi targets UP/baseline sample rồi ghi UTC start; sau generator drain đợi final scrape và ghi UTC end. Giữ command, target-state, config, summary/trace/sent/drops và link dashboard theo bounds. Gỡ target file trước scoped cleanup; Prometheus volume giữ samples trong retention. Không suy client goodput từ backend counters, không retry/chọn lượt đẹp. Thiếu target/sample là incomplete, không pass.

## 5. Redis outage — G4

**P2-07 hiện chưa có đường thực thi G4 trên kiến trúc Console-run.** Không pause Redis của `project3-monitoring-demo` để làm gián đoạn case ở `project3-research-lab`; không gọi `scripts/redis-outage.sh` thay Console, vì script tự dựng project và load riêng. Nếu sau này G4 được cho phép, fault hook phải nhắm Redis thuộc đúng run hiện tại sau khi xác minh project/service identity, để runner/owner giữ load path duy nhất; phải có watchdog/trap unpause và cleanup/cancel tests trước tải. Ngân sách giữ nguyên: tối đa 4 healthy/outage × fail-open/closed, 30s/case, 20 RPS, 1 attempt/case; pause một lần 2s tại giây 10. Không pause khi thiếu identity/owner; giữ G4 chưa thực hiện nếu prerequisite chưa sẵn. Không restart host Redis, `FLUSHDB`, đổi clock hoặc cấu hình hệ thống. `up=1` không chứng minh Redis khỏe; fail-open có thể tăng backend traffic, fail-closed 503 khác quota 429. First success không đồng nghĩa stable recovery.

## 6. Dừng và giữ dữ liệu

Sau khi ghi artifact, chỉ dừng project của phiên bằng đúng bộ file/env:

```bash
# Dừng stack demo; giữ named volumes để xem lại dữ liệu.
docker compose -p project3-monitoring-demo \
  -f compose.yaml -f compose.observability.yaml down
```

Không dùng `down -v`, `docker system prune`, `volume prune` hoặc xóa artifact làm cleanup mặc định. Nếu cần reset dữ liệu demo, xác định chính xác volume/project, lưu phần cần giữ và áp dụng quyền xóa đã có; không suy dữ liệu ignored là có thể bỏ.

Giữ TSDB trên volume riêng `project3-monitoring-demo`; Prometheus đặt retention 24h và 512MB cho blocks. WAL/metadata có thể khiến volume vượt retention size; đây không phải hard disk quota. Prometheus/Grafana memory limit là 512 MiB mỗi service; log rotation mỗi service là 10 MiB × 3 file. Đây là cấu hình ban đầu, chưa đo hoặc runtime xác minh; theo dõi dung lượng trước khi tăng thời lượng. Loki filesystem cần retention/cleanup riêng khi P2-04 được làm. Không commit credentials; lọc env nhạy cảm khỏi `docker inspect` evidence. Nếu Alloy cần Docker socket, chỉ mount vào Alloy: `:ro` không làm Docker API read-only, không expose daemon TCP/`privileged`; tương lai lọc rõ fixed `project3-monitoring-demo` allowlist `api1`/`api2`/`backend` và research `project3-research-lab` allowlist `api1`…`api4`/`backend` cho run opt-in. Đây là filter, không phải security boundary. Ghi trước/sau containers/process, paused state, ports, volumes và vị trí credentials; bàn giao cách dừng nếu để stack chạy.

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
