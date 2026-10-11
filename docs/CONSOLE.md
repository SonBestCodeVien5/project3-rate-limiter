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

## Giao diện và hướng phát triển

Bản hiện tại đặt chỉ số cuối lượt thành các thẻ riêng (request đã gửi, 2xx, 429, goodput và p95 của client hợp lệ, backend arrivals xác nhận). Cấu hình thực tế, snapshot từng instance và artifact vẫn xem được; JSON thô nằm trong phần mở rộng để dòng dài không kéo giãn trang. Cách phân cấp thẻ chỉ số và phần xem chi tiết được tham khảo từ [Custom Dashboards của Langfuse](https://langfuse.com/docs/metrics/features/custom-dashboards); Console không dùng Langfuse hay dữ liệu LLM.

Các mục sau là **đề xuất tùy chọn**, không phải yêu cầu Roadmap/Proposal hoặc tính năng đã triển khai:

| Ưu tiên | Tính năng có thể thêm | Điều kiện trước khi làm |
| --- | --- | --- |
| 1 | So sánh ba run `mixed-none/local/redis` cạnh nhau theo goodput hợp lệ, p95/p99, 429/5xx và backend arrivals | Chỉ ghép run có cùng workload, backend config, số API và revision; hiển thị khác biệt cấu hình nếu không khớp. |
| 2 | Biểu đồ nhỏ từ artifacts sau run: traffic hợp lệ/toàn tải, quyết định limiter và backend overload theo thời gian | Kiểm tra timestamp, đơn vị, dropped requests và tác động của xử lý dữ liệu; không gọi snapshot cuối là live. |
| 3 | Mở thêm preset `normal`, `burst`, `concurrent`, `scale-1/2/4` với tham số được khóa theo từng preset | Pilot và protocol phải xác định tổ hợp hợp lệ, giới hạn tải, phép so sánh và nhãn cấu hình thực tế. |
| 4 | Hiện tiến trình runner và Redis CPU/memory sample rõ thời điểm lấy | Cần đo overhead polling/sampling trước khi dùng số liệu này trong báo cáo. |
| 5 | Trình diễn Redis outage có thời lượng cố định và cleanup được kiểm chứng | Chỉ sau khi fault injection CLI ổn định; không mở lệnh Docker hay thời lượng tùy ý từ trình duyệt. |
| Sau cùng | Export gói artifact/báo cáo hoặc dashboard lưu lịch sử nhiều run | Chỉ thêm khi một buổi demo/đánh giá thật cần; không thay trace và analyzer hiện có. |

Prometheus/Grafana hay Loki/Alloy chỉ nên xem xét nếu cần quan sát dài hạn hoặc tìm log qua nhiều run mà artifacts hiện tại không đáp ứng. Truy cập LAN cần thiết kế quyền điều khiển process riêng. Những mục này không thuộc bản Console local hiện tại.
