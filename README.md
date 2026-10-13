# Project 3: Distributed Rate Limiting

Prototype nghiên cứu quota phân tán cho API nhiều instance: Fixed Window/Token Bucket, local/Redis atomic state, backend giới hạn năng lực và fail-open/fail-closed. Bối cảnh là API flash sale giả định; không phải API Gateway production.

Bắt đầu với [Project Brief](docs/context/PROJECT_BRIEF.md) và [thứ tự nguồn](docs/context/SOURCE_INDEX.md). Google Drive là nguồn yêu cầu; [thiết kế triển khai](docs/IMPLEMENTATION.md) ghi lựa chọn kỹ thuật. [Roadmap](docs/PROJECT_ROADMAP.md) là lịch đề xuất; [đặc tả thí nghiệm](docs/experiments/EXPERIMENT_SPEC.md) chưa khóa protocol đo chính thức.

[Demo Console local](docs/CONSOLE.md) đã triển khai với cấu hình custom và metrics/artifacts. [Ma trận 84 lượt thực chạy](docs/worklog/2026-10-12-console-matrix/README.md) giữ raw archive, checksum và bảng đối chiếu số đo để tham chiếu báo cáo pilot.

## Chạy prototype

Cần Go 1.26.1 trở lên, Docker Compose, Bash, curl và GNU `timeout` cho runner.

```bash
docker compose up -d --build --wait
curl -i -X POST -H 'X-Client-ID: buyer-1' http://localhost:8080/work
curl http://localhost:18083/metrics
docker compose down
```

Mặc định: Redis atomic Fixed Window, 2 API instance, Q=20/1s, backend capacity=10 và service time=50ms. Biến môi trường Compose: `MODE=none|local|redis`, `ALGORITHM=fixed-window|token-bucket`, `FAIL_POLICY=open|closed`, `NAMESPACE`, `LIMIT`, `WINDOW`, `CAPACITY`, `RATE`, `REDIS_TIMEOUT`, `BACKEND_CAPACITY`, `BACKEND_SERVICE_TIME`. Ví dụ:

```bash
MODE=local ALGORITHM=token-bucket docker compose up -d --build --wait
```

Các cổng chỉ bind loopback: ingress 8080, API metrics 18081/18082, backend 18083, Redis 16379. `/healthz` là liveness; vẫn trả khỏe khi Redis lỗi để đo fail policy. `X-Client-ID` là định danh tin cậy của workload, không phải authentication. API trả 429 khi quota hết, 503 khi fail-closed hoặc backend overload, 502 khi lỗi transport backend.

## Kiểm thử và workflow

```bash
bash scripts/verify.sh
# Chạy thêm integration với Redis thật đang hoạt động:
REDIS_TEST_ADDR=127.0.0.1:16379 bash scripts/verify.sh
```

Verify chạy format check → vet → race tests → build → shell checks → cleanup tests → Compose validation. Không có `REDIS_TEST_ADDR`, các test Redis được ghi SKIP. Trong sandbox cache readonly, thêm `GOCACHE=/tmp/project3-go-cache`; HTTP tests cần quyền bind localhost.

Lượt phát triển dùng vòng plan → code → test → review → sửa/retest → commit; [hồ sơ đầy đủ](docs/worklog/2026-10-11-bootstrap/README.md) phân mục theo từng bước, giữ cả lỗi môi trường và giới hạn kiểm chứng. Commit được thực hiện sau review và verify, không gắn thao tác commit tự động vào test runner.

## Smoke/pilot và dữ liệu

```bash
bash scripts/pilot-matrix.sh
bash scripts/redis-outage.sh
# Pilot normal/burst/concurrent và scaling 1/2/4:
bash scripts/research-pilot.sh --analyze
# Một lượt tùy chỉnh khi stack đang chạy:
go run ./cmd/loadgen -duration 10s -rps 100 -legitimate-rps 20 \
  -mode redis -algorithm fixed-window -fail-policy closed -out artifacts/my-run
```

Hai script đầu tạo project Compose riêng `project3-lab`, từ chối nếu project đã có container, reset mỗi case và dọn khi thoát. Hãy dừng stack mặc định trước khi chạy vì dùng chung cổng loopback. Outage chỉ pause Redis lab 2s rồi unpause; không FLUSHDB, không chạm dịch vụ Redis bên ngoài. Tải và thời gian là giá trị pilot, không phải protocol được duyệt.

Mỗi run lưu `metadata.json`, `requests.jsonl`, `summary.json`; runner thêm config Compose, metrics backend/API, Redis CPU/memory, logs và timestamps outage. Generator open-loop gửi POST, ghi cả dropped requests và schedule lag; goodput dùng tổng thời gian gồm drain, latency hợp lệ thành công chỉ tính 2xx. Mode/algorithm truyền cho loadgen là nhãn; dùng Compose resolved để kiểm tra cấu hình thực.

Summary chưa phải oracle quota hoặc đánh giá recovery. Cần khóa tải, warm-up, số lượt lặp, kiểm chứng generator và phân tích riêng từng thuật toán trước kết luận RQ1–RQ5. Test đối chứng non-atomic có barrier chỉ chứng minh khả năng lost update, không đo tần suất race tự nhiên. Xem [trạng thái triển khai và việc còn lại](docs/IMPLEMENTATION_STATUS.md) và [chi tiết runner](scripts/README.md).

Workspace hội thoại: [ChatGPT Project 3](https://chatgpt.com/g/g-p-6ac5bc31497c81919197782e9d2226c6-project3/project). Hướng dẫn agent: [AGENTS.md](AGENTS.md).

Vòng công cụ đo tiếp theo có [protocol ứng viên](docs/experiments/PILOT_PROTOCOL.md), [analyzer độc lập](docs/experiments/ANALYSIS.md) và [hồ sơ kiểm chứng](docs/worklog/2026-10-11-measurement/README.md). Runner mới dùng project `project3-research-lab`, mặc định loopback 18080; tách khỏi runner bootstrap. [Đánh giá scope và chiến lược học](docs/SCOPE_PROGRESS_2026-10-11.md) giải thích vì sao chưa mở rộng tính năng.
