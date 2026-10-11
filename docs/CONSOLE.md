# Demo Console: workflow triển khai và vận hành

Console là giao diện local cho pilot mixed traffic, không thay đổi protocol hoặc phép đo của runner. Ba preset đầu tiên là `mixed-none`, `mixed-local`, `mixed-redis`; mỗi lần chỉ chọn một preset, `MIXED_RPS` 21..1000 và repetitions 1..3. Các giá trị còn lại do `research-pilot.sh` quyết định. Roadmap/Proposal chỉ yêu cầu các thí nghiệm rate limiting; Console là lựa chọn kỹ thuật để trình bày demo.

## Workflow phát triển

1. **Controller và runner:** xác thực preset/tham số ở server, khóa một runner, tạo Run ID/artifacts riêng, giữ runner hiện hữu làm nguồn thực thi; test request sai, cạnh tranh run, hủy và path artifact.
2. **Giao diện và số liệu:** read-only stack mặc định, request mẫu, live snapshot có nhãn nguồn, status và summary theo lượt, tải artifacts; chạy thử HTTP/UI.
3. **Rà soát và tích hợp:** `bash scripts/verify.sh`, chạy `go run ./cmd/console`, thử một preset trên Docker thật, kiểm tra `summary.json`, `policy.json`, `compose-resolved.json` và `docker ps` sau complete/hủy; sửa rồi chạy lại phần bị ảnh hưởng.
4. **Commit:** commit các phần đã qua test/review theo thứ tự controller/runner, giao diện, tài liệu hoặc sửa tích hợp. Không coi pilot values là ngưỡng đánh giá nghiên cứu.

## Chạy demo

Yêu cầu Go, Docker Compose, `curl`, Python 3, GNU `timeout` và `flock`. Chạy từ gốc repo:

```bash
go run ./cmd/console
# Mở http://127.0.0.1:8090
```

Phần **Stack mặc định** đọc các cổng loopback 8080/18081/18082/18083; nếu muốn dùng phần này, khởi động `docker compose up -d --build --wait` riêng. Nút request mẫu gửi một `POST /work` với client ID cố định `console-demo` vào stack mặc định. Phần benchmark gọi `scripts/research-pilot.sh` với một preset; runner dùng project `project3-research-lab` và cổng ingress 18080. Nó từ chối nếu project đã có container hoặc runner khác đang giữ khóa. Các run nằm dưới `artifacts/console/<Run ID>/`, gồm request, trạng thái, log và `result/` của runner. CLI tương đương:

```bash
MIXED_RPS=120 bash scripts/research-pilot.sh --case mixed-redis --repetitions 1 --analyze --output artifacts/example-new-dir
```

Console chỉ bind `127.0.0.1`. `/api/runs/{id}/metrics` poll `/metrics` trong container qua Docker exec khi run hoạt động; đó là counter tích lũy theo container, lấy mẫu theo thời điểm, không phải delta hay kết quả cuối. Polling có overhead; dùng artifact before/after và trace của runner để phân tích nghiên cứu. `summary.json` chỉ xuất hiện sau khi load generator drain; `analysis.json` là kết luận của analyzer, Console không tự suy diễn.

Khi hủy hoặc dừng Console bằng SIGINT/SIGTERM, controller gửi SIGTERM tới process group, đợi runner cleanup rồi kiểm tra container của project. Nếu Console bị SIGKILL/restart bất ngờ, run dở được đánh dấu `interrupted`; kiểm tra `docker ps --filter label=com.docker.compose.project=project3-research-lab` và log trước khi chạy lại. Runner giữ khóa trong suốt tiến trình còn chạy. `cleanup-error` nghĩa là còn container hoặc không xác minh được cleanup; cần kiểm tra thủ công trước khi diễn tập tiếp.

Phạm vi hiện tại không cho chỉnh quota, backend capacity, thuật toán hay fault injection từ UI; dùng CLI và artifact để thử các phép đo đó. Các biểu đồ, history database và truy cập LAN cũng chưa có.
