# Project 3: Giới hạn lưu lượng phân tán

Prototype nghiên cứu rate limiter phân tán cho nhiều API instance: Fixed Window/Token Bucket, local state hoặc shared state qua Redis với thao tác atomic, backend giới hạn năng lực và chính sách fail-open/fail-closed. Bối cảnh là API flash sale giả định; phạm vi không bao gồm API Gateway cho môi trường vận hành thực tế.

Bắt đầu với [hướng dẫn đọc tài liệu](docs/README.md): lộ trình đọc, tài liệu hiện hành, thuật ngữ và cách dùng để viết báo cáo. Google Drive là nguồn yêu cầu; [thiết kế triển khai](docs/IMPLEMENTATION.md) ghi lựa chọn kỹ thuật. [Lộ trình](docs/PROJECT_ROADMAP.md) là lịch đề xuất; [đặc tả thí nghiệm](docs/experiments/EXPERIMENT_SPEC.md) giữ thiết kế ban đầu, còn [điều kiện đo hiện tại](docs/experiments/PROTOCOL_READINESS.md) dẫn tới quy trình đã khóa.

**Cập nhật 20/10/2026:** T09 đã thu thập đủ 138/138 lượt dự kiến, tổng hợp đủ 46/46 cấu hình; T10 chưa bắt đầu và chưa có kết luận RQ1–RQ5. Đang dừng trước T10, không chạy thêm tải. Xem [công việc còn lại](docs/REMAINING_WORK_PLAN.md). Các lệnh bên dưới là hướng dẫn tham khảo khi có yêu cầu chạy phù hợp, không thay đổi điểm dừng này.

[Giao diện demo Console](docs/CONSOLE.md) chạy trên máy, hỗ trợ cấu hình tùy chỉnh, chỉ số và tệp bằng chứng. [Ma trận 84 lượt thực chạy](docs/worklog/2026-10-12-console-matrix/README.md) giữ kho dữ liệu thô, checksum và bảng đối chiếu số đo để tham chiếu các lượt thử sơ bộ.

## Chạy prototype

Cần Go 1.26.1 trở lên, Docker Compose, Bash, curl và GNU `timeout` cho runner.

```bash
docker compose up -d --build --wait
curl -i -X POST -H 'X-Client-ID: buyer-1' http://localhost:8080/work
curl http://localhost:18083/metrics
docker compose down
```

Cấu hình mặc định: Redis Fixed Window có atomicity, 2 API instance, Q=20/1s, backend capacity=10 và service time=50ms. Biến môi trường Compose: `MODE=none|local|redis`, `ALGORITHM=fixed-window|token-bucket`, `FAIL_POLICY=open|closed`, `NAMESPACE`, `LIMIT`, `WINDOW`, `CAPACITY`, `RATE`, `REDIS_TIMEOUT`, `BACKEND_CAPACITY`, `BACKEND_SERVICE_TIME`. Ví dụ:

```bash
MODE=local ALGORITHM=token-bucket docker compose up -d --build --wait
```

Các cổng chỉ bind loopback: ingress 8080, API metrics 18081/18082, backend 18083, Redis 16379. `/healthz` là liveness; vẫn trả khỏe khi Redis lỗi để đo fail policy. `X-Client-ID` là định danh tin cậy của workload, không phải authentication. API trả 429 khi quota hết, 503 khi fail-closed hoặc backend overload, 502 khi lỗi transport backend.

## Kiểm thử và quy trình phát triển

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

Hai script đầu tạo project Compose riêng `project3-lab`, từ chối nếu project đã có container, reset mỗi case và dọn khi thoát. Hướng dẫn lịch sử: stack mặc định cần được dừng trước khi chạy vì dùng chung cổng loopback. Outage chỉ pause Redis lab 2s rồi unpause; không FLUSHDB, không chạm dịch vụ Redis bên ngoài. Tải và thời gian là giá trị pilot, không phải protocol được phê duyệt.

Mỗi lượt chạy lưu `metadata.json`, `requests.jsonl`, `summary.json`; runner thêm cấu hình Compose, metrics backend/API, Redis CPU/memory, logs và timestamps outage. Generator open-loop gửi POST, ghi cả request bị bỏ và schedule lag; goodput dùng tổng thời gian gồm drain, độ trễ của request hợp lệ thành công chỉ tính 2xx. Mode/algorithm truyền cho loadgen là nhãn; dùng Compose resolved để kiểm tra cấu hình thực.

Summary không phải oracle quota hay đánh giá recovery. Protocol hiện đã khóa; T09 hoàn tất. T10 chưa bắt đầu và không được chạy thêm tải. Chưa có kết luận RQ1–RQ5. Test đối chứng non-atomic có barrier chỉ chứng minh khả năng lost update, không đo tần suất race tự nhiên. Xem [trạng thái triển khai và việc còn lại](docs/IMPLEMENTATION_STATUS.md) và [chi tiết runner](scripts/README.md).

Workspace hội thoại: [ChatGPT Project 3](https://chatgpt.com/g/g-p-6ac5bc31497c81919197782e9d2226c6-project3/project). Hướng dẫn agent: [AGENTS.md](AGENTS.md).

Hồ sơ công cụ đo ngày 11/10 gồm [quy trình pilot cũ](docs/experiments/PILOT_PROTOCOL.md), [quy tắc phân tích](docs/experiments/ANALYSIS.md) và [hồ sơ kiểm chứng](docs/worklog/2026-10-11-measurement/README.md). Runner đo dùng project `project3-research-lab`, mặc định loopback 18080; tách khỏi runner ban đầu. [Đánh giá phạm vi và chiến lược học](docs/SCOPE_PROGRESS_2026-10-11.md) giữ lý do chưa mở rộng tính năng tại thời điểm đó.
