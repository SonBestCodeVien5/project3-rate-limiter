# Chạy kiểm tra và pilot

Các giá trị tải ở đây là lựa chọn kỹ thuật cho smoke/pilot, không phải kết luận RQ1–RQ5. T09 và phân tích offline T10 đã hoàn tất; xem [kết quả T10](../docs/analysis/T10_RESULTS.md) và [worklog tái lập](../docs/worklog/2026-10-20-t10/README.md). Hướng dẫn runner bên dưới có giá trị lịch sử, không cấp quyền chạy thêm tải; điểm dừng hiện tại nằm trong [kế hoạch việc còn lại](../docs/REMAINING_WORK_PLAN.md) và [readiness](../docs/experiments/PROTOCOL_READINESS.md). Cần Go, Docker Compose, `curl` và GNU `timeout`; `research-pilot.sh` cần thêm `flock` để khóa một runner trong cùng checkout. `pilot-matrix.sh` và `redis-outage.sh` dùng project `project3-lab`; `research-pilot.sh` dùng `project3-research-lab`. Mỗi runner từ chối nếu project của nó đã có container và dọn container do lượt chạy tạo ra khi thoát. Không dùng `FLUSHDB`.

```bash
bash scripts/verify.sh
bash scripts/pilot-matrix.sh
bash scripts/redis-outage.sh
```

- `verify.sh`: kiểm tra định dạng, vet, race tests, build, cú pháp shell, kiểm tra dọn dẹp và cấu hình Compose nếu có Docker. Test HTTP cần quyền mở socket localhost. Test Redis thực theo quy ước biến môi trường của package limiter; xem kết quả skipped để biết bài kiểm tra tích hợp nào chưa chạy.
- `pilot-matrix.sh`: không limiter, local/Redis × Fixed Window/Token Bucket; mỗi case 5 giây, tổng 300 RPS, trong đó 20 RPS hợp lệ chia đều 5 client. Đây là hai luồng đều theo lịch, chưa phải kịch bản burst có pha bật/tắt.
- `redis-outage.sh [OUTPUT]`: mỗi fail policy chạy baseline khi Redis khỏe rồi một lượt cùng cấu hình có Redis pause; mặc định 25 giây, 100/20 total/legitimate RPS, pause từ giây 4 trong 2 giây. Baseline dừng trước outage nếu có lỗi client hợp lệ, generator drop, lỗi truyền tải/limiter hoặc backend overload. p95 của client hợp lệ khi Redis khỏe nhân 1.5 được ghi trước outage và dùng làm ngưỡng recovery 1s/5 mẫu/3 cửa sổ. Analyzer đánh giá cả lượt Redis khỏe lẫn lượt outage và lưu revision/status tại thư mục policy cha của mỗi case. `OUTAGE_DURATION`, `OUTAGE_RPS`, `OUTAGE_LEGIT_RPS`, `OUTAGE_PAUSE_AT`, `OUTAGE_PAUSE_FOR`, `OUTAGE_HOST_PORT` cùng cấu hình Compose `LIMIT`, `WINDOW`, `CAPACITY`, `RATE`, `BACKEND_CAPACITY`, `BACKEND_SERVICE_TIME` cho phép hiệu chỉnh; đầu ra phải là đường dẫn mới. First success không đồng nghĩa recovery. Quota thiếu trạng thái/response vẫn unknown hoặc là cận dưới.

## Pilot ứng viên đo với 1/2/4 API

```bash
bash scripts/research-pilot.sh --case normal --case scale-1 --case scale-2 --case scale-4 --repetitions 2 --analyze
# Hoặc bỏ --case để chạy cả 11 case đã chọn, mỗi case một lượt.
```

Runner dùng Compose project riêng `project3-research-lab` và mặc định Nginx tại `127.0.0.1:18080`. Có thể chọn `--host-port` và `--output` (thư mục mới). Runner từ chối project đã có container, giới hạn từng lệnh quan trọng bằng timeout và dọn container do chính lượt chạy tạo. `render-topology.py` dựng upstream Nginx khớp chính xác 1, 2 hoặc 4 API từ `docker compose config --format json`; capacity backend dùng chung không đổi. Mỗi lượt có namespace mới, container mới, `policy.json` lấy từ môi trường đã resolve, cấu hình Compose, log, metrics, trace thô và dấu vết image/source. `--analyze` gọi analyzer sau mỗi case; bỏ cờ này nếu chỉ muốn giữ dữ liệu thô.

Các profile của generator: `normal` chỉ có lưu lượng client hợp lệ; `burst` giữ tải hợp lệ đều và tăng tải client bất thường trong khoảng đã chỉ định; `concurrent` lên lịch nhiều request cùng key tại một mốc rồi ghi độ trễ gửi thực tế; `mixed` giữ ổn định cả hai luồng. Tham số và điều kiện loại lượt đo nằm trong [protocol pilot](../docs/experiments/PILOT_PROTOCOL.md). Đây là hướng dẫn lịch sử; protocol chính thức v1.2 cùng phụ lục v1.3 đã hoàn tất T09, sau đó T10 phân tích offline. Không dùng hướng dẫn này để khởi chạy thêm tải. Xem [kết quả T10](../docs/analysis/T10_RESULTS.md) và [trạng thái sẵn sàng hiện tại](../docs/experiments/PROTOCOL_READINESS.md).

`--case custom` chạy riêng một case và đọc các biến `CUSTOM_*`; bỏ `--case` vẫn chạy 11 case chuẩn. Mặc định custom: `MODE=redis`, `ALGORITHM=fixed-window`, `INSTANCES=2`, `PROFILE=mixed`, `RPS=120`, `LEGIT_RPS=20`, `DURATION=6`, `LIMIT=20`, `WINDOW_MS=1000`, `CAPACITY=20`, `RATE=20`, `BACKEND_CAPACITY=10`, `BACKEND_SERVICE_MS=50`, `FAIL_POLICY=closed`, `BURST_START=2`, `BURST_DURATION=2`, `BURST_RPS=200`, `CONCURRENT_AT=2`, `CONCURRENT_COUNT=100` (mọi tên có tiền tố `CUSTOM_`). Giới hạn và điều kiện phối hợp tương ứng với [Console](../docs/CONSOLE.md). Runner kiểm tra trước khi tạo output; request và cấu hình Compose đã resolve nằm trong artifact. `normal` yêu cầu `CUSTOM_LEGIT_RPS=CUSTOM_RPS`; `concurrent` yêu cầu `CUSTOM_LEGIT_RPS=0` và batch count quyết định tải thực. Các giá trị này chỉ mô tả pilot/demo lịch sử, không phải hướng dẫn chạy thêm tải.

Hai script pilot nhận đường dẫn thư mục output ở đối số thứ nhất; mặc định nằm dưới `artifacts/`. Mỗi case lưu cấu hình Compose đã resolve, HTTP metrics backend trước/sau, metrics API, log container, tài nguyên Redis và dữ liệu generator. Redis CPU là counter tích lũy, cần lấy delta theo thời gian; không diễn giải trực tiếp thành % CPU. Kịch bản outage chỉ lấy Redis INFO trước/sau để tránh client đo bị treo khi Redis pause. Các thao tác INFO, snapshot, pause/unpause đều có timeout; cleanup luôn thử unpause trước khi dọn lab.

## Bằng chứng pilot Console

[84 tổ hợp custom đã chạy ngày 12/10](../docs/worklog/2026-10-12-console-matrix/README.md) có CSV/JSON, archive dữ liệu thô và manifest SHA256 trong Git. Các cột backend_* là delta snapshot; api_* là tổng delta của mọi API. Giữ nhãn request bị bỏ/lỗi Redis/phát hiện oracle khi dẫn số liệu. Các lượt 3 giây này kiểm tra ma trận cấu hình, không phải benchmark nghiên cứu chính thức.

## Generator độc lập

```bash
go run ./cmd/loadgen -target http://localhost:8080/work \
  -duration 10s -rps 100 -legitimate-rps 20 -legitimate-clients 5 \
  -max-inflight 100 -timeout 2s -run-id example \
  -mode redis -algorithm fixed-window -fail-policy closed
```

Generator dùng `POST /work` để tầng truyền tải không tự retry request idempotent trên kết nối được tái sử dụng; không theo redirect. `rps` là tổng tải, đã bao gồm `legitimate-rps`. Các client hợp lệ dùng key `legitimate-0001` trở đi; lưu lượng còn lại dùng một key `abusive-0001`. Định danh này chỉ phục vụ workload, không phải authentication.

Giới hạn tối đa 10 phút/lượt, 2 triệu request dự kiến và 10.000 request in-flight. Khi hết chỗ hoặc trễ lịch quá `-max-schedule-lag`, generator ghi một record request bị bỏ thay vì chờ hoặc dồn tải bù. Kiểm tra `generator_dropped` và `schedule_lag` trước khi kết luận offered load đã đạt yêu cầu.

Output gồm `metadata.json`, `requests.jsonl`, `summary.json`; thư mục dành cho generator phải chưa tồn tại. Metadata lưu argv, cấu hình, revision, trạng thái Git và thông tin tối thiểu về môi trường chạy. Mode/algorithm/fail-policy ở CLI chỉ là nhãn do người chạy cung cấp; cấu hình Compose đã resolve mới là bằng chứng cấu hình server trong runner.

Summary có p50/p95/p99 nearest-rank, số lượng status/error/decision, goodput và độ trễ đuôi của các request hợp lệ thành công. Mẫu độ trễ tổng gồm mọi request đã gửi, kể cả timeout; `latency_by_decision` tách allow/reject/fail policy. Percentile bằng 0 khi không có mẫu nghĩa là chưa có dữ liệu. Rate/goodput tính trên toàn thời gian thực từ lúc bắt đầu đến khi drain xong, không chỉ duration cấu hình. Timeout là tập con của lỗi truyền tải; HTTP status có thể đồng thời có lỗi trong response body. Số backend arrivals lấy từ header chỉ xác nhận những request client nhận được; cần đối chiếu counter backend để tính cả request bị mất phản hồi.

Chưa có oracle độc lập trong summary: không gọi việc Token Bucket nhận hơn Q trong cửa sổ Fixed Window là overshoot. JSONL lưu thời điểm quyết định, client key và instance để hỗ trợ phân tích tiếp theo. Quy trình công cụ đo đã bổ sung profile burst/concurrent, topology 1/2/4 và analyzer độc lập; xem các phần bên dưới. Ghi chú này mô tả nhu cầu trước khi khóa protocol; protocol chính thức v1.2 cùng phụ lục v1.3 đã hoàn tất T09, rồi T10 phân tích offline. Xem [kết quả T10](../docs/analysis/T10_RESULTS.md) và [readiness hiện tại](../docs/experiments/PROTOCOL_READINESS.md); hướng dẫn chạy trong tài liệu này không cấp quyền tải mới.

Để hiệu chỉnh tải khi phát hiện generator drops, có thể đặt `MIXED_RPS` và `BACKEND_CAPACITY` cho cả nhóm mixed, ví dụ `MIXED_RPS=120 BACKEND_CAPACITY=4 bash scripts/research-pilot.sh --case mixed-none --case mixed-local --case mixed-redis --analyze`. Không trộn kết quả hai cấu hình tải/backend khác nhau trong một phép so sánh; metadata/config resolved lưu giá trị thực. Mặc định 300 RPS có thể cần hiệu chỉnh theo máy; xem kết quả pilot thực tế thay vì giả định một con số luôn đạt.
