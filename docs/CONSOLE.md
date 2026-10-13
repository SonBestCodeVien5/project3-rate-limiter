# Demo Console: workflow triển khai và vận hành

Console là giao diện local cho pilot, không thay đổi protocol hoặc phép đo của runner. Ba preset cố định là `mixed-none`, `mixed-local`, `mixed-redis` (tổng RPS 21..1000); chế độ `custom` cho phép chọn workload, mode, thuật toán, topology và policy trong các giới hạn bên dưới. Mỗi run chọn một case, lặp 1..3 lượt. Roadmap/Proposal chỉ yêu cầu các thí nghiệm rate limiting; Console là lựa chọn kỹ thuật để trình bày demo.

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

Chế độ **Tùy chỉnh** hỗ trợ `normal`, `mixed`, `burst`, `concurrent`; 1/2/4 API; tắt limiter/local/Redis; Fixed Window hoặc Token Bucket; fail-open/closed khi dùng Redis. Có thể đặt tổng tải 1..1000 RPS, tải hợp lệ 0..1000 RPS (không vượt tổng), thời lượng 3..30 giây, quota 1..1000, window 100..9999 ms, bucket capacity/refill 1..1000, backend capacity 1..100 và service time 0..1000 ms. Burst có mốc bắt đầu, thời lượng và RPS riêng cho luồng bất thường; concurrent có mốc và số request trong batch. `normal` dùng toàn bộ RPS làm tải hợp lệ. Với `concurrent`, số request batch quyết định tải thực tế; ô RPS chỉ là nhãn trong metadata. Trường không liên quan đến mode/profile được ẩn, nhưng request và `policy.json`/`compose-resolved.json` vẫn ghi đủ cấu hình để tái hiện. Đây là biên an toàn của demo, không phải tham số protocol nghiên cứu đã khóa.

Ví dụ tái hiện một run tùy chỉnh qua CLI (các `CUSTOM_*` khác dùng mặc định trong [scripts/README.md](../scripts/README.md)):

```bash
CUSTOM_MODE=redis CUSTOM_ALGORITHM=token-bucket CUSTOM_PROFILE=burst \
CUSTOM_INSTANCES=4 CUSTOM_RPS=60 CUSTOM_LEGIT_RPS=10 CUSTOM_DURATION=6 \
CUSTOM_CAPACITY=15 CUSTOM_RATE=12 CUSTOM_BACKEND_CAPACITY=4 \
CUSTOM_BURST_RPS=100 bash scripts/research-pilot.sh --case custom --analyze
```

Khi hủy hoặc dừng Console bằng SIGINT/SIGTERM, controller gửi SIGTERM tới process group, đợi runner cleanup rồi kiểm tra container của project. Nếu Console bị SIGKILL/restart bất ngờ, run dở được đánh dấu `interrupted`; kiểm tra `docker ps --filter label=com.docker.compose.project=project3-research-lab` và log trước khi chạy lại. Runner giữ khóa trong suốt tiến trình còn chạy. `cleanup-error` nghĩa là còn container hoặc không xác minh được cleanup; cần kiểm tra thủ công trước khi diễn tập tiếp.

Phạm vi hiện tại chưa cho chỉnh fault injection từ UI. Các biểu đồ, history database và truy cập LAN cũng chưa có.

## Kết quả tích hợp thực chạy

[Ma trận ngày 12/10/2026](worklog/2026-10-12-console-matrix/README.md) đã gửi 84 tổ hợp hợp lệ qua API Console: 4 profile × 7 tổ hợp mode/algorithm/fail policy × 3 topology. Mỗi cấu hình chạy một lượt 3 giây; 84 runner complete và artifact khớp, nhưng analyzer có 2 observed_violations/40 inconclusive, 19 Redis limiter errors và 5 generator drops. Playwright đã kiểm tra một lượt custom và overflow desktop/mobile ở vòng triển khai; không coi ma trận API là 84 lượt kiểm tra form. CSV bổ sung backend deltas và tổng counters của mọi API; archive giữ dữ liệu gốc để dẫn báo cáo.

## Giao diện và hướng phát triển

Bộ chọn **Lượt xem kết quả** hiển thị riêng từng lượt 1..3, giữ lượt đang chọn khi polling và ghi rõ lượt chưa có summary. Trạng thái oracle lấy trực tiếp từ `analysis.json` của lượt đó; thiếu hoặc lỗi JSON hiển thị chưa có analyzer, không suy diễn từ runner complete. Generator drops hiển thị riêng; lỗi limiter là tổng delta `limiter_errors` của đủ API trong analyzer counters, thiếu bất kỳ API nào hiển thị **Thiếu counters**. Goodput/p95 hợp lệ ghi **Không áp dụng** khi không có request hợp lệ (bao gồm concurrent); nếu đã gửi nhưng không có mẫu hợp lệ thành công thì p95 ghi **Không có mẫu thành công**.

Kiểm tra phần này bằng `go test ./internal/console` và `node internal/console/index_test.js` (Node chỉ dùng cho test giao diện, không phải dependency runtime). Test API bao phủ summary/analyzer riêng từng lượt và JSON lỗi; test giao diện bao phủ đổi lượt, polling, thiếu evidence và concurrent.

Bản hiện tại đặt chỉ số cuối lượt thành các thẻ riêng (request đã gửi, 2xx, 429, goodput và p95 của client hợp lệ, backend arrivals xác nhận). Cấu hình thực tế, snapshot từng instance và artifact vẫn xem được; JSON thô nằm trong phần mở rộng để dòng dài không kéo giãn trang. Cách phân cấp thẻ chỉ số và phần xem chi tiết được tham khảo từ [Custom Dashboards của Langfuse](https://langfuse.com/docs/metrics/features/custom-dashboards); Console không dùng Langfuse hay dữ liệu LLM.

Các mục sau là **đề xuất tùy chọn**, không phải yêu cầu Roadmap/Proposal hoặc tính năng đã triển khai:

| Ưu tiên | Tính năng có thể thêm | Điều kiện trước khi làm |
| --- | --- | --- |
| 1 | So sánh ba run `mixed-none/local/redis` cạnh nhau theo goodput hợp lệ, p95/p99, 429/5xx và backend arrivals | Chỉ ghép run có cùng workload, backend config, số API và revision; hiển thị khác biệt cấu hình nếu không khớp. |
| 2 | Biểu đồ nhỏ từ artifacts sau run: traffic hợp lệ/toàn tải, quyết định limiter và backend overload theo thời gian | Kiểm tra timestamp, đơn vị, dropped requests và tác động của xử lý dữ liệu; không gọi snapshot cuối là live. |
| 3 | Thêm preset có tham số khóa cho normal/burst/concurrent/scale; các profile/topology này đã chọn được trong custom | Pilot và protocol phải xác định tổ hợp hợp lệ, giới hạn tải, phép so sánh và nhãn cấu hình thực tế. |
| 4 | Hiện tiến trình runner và Redis CPU/memory sample rõ thời điểm lấy | Cần đo overhead polling/sampling trước khi dùng số liệu này trong báo cáo. |
| 5 | Trình diễn Redis outage có thời lượng cố định và cleanup được kiểm chứng | Chỉ sau khi fault injection CLI ổn định; không mở lệnh Docker hay thời lượng tùy ý từ trình duyệt. |
| Sau cùng | Export gói artifact/báo cáo hoặc dashboard lưu lịch sử nhiều run | Chỉ thêm khi một buổi demo/đánh giá thật cần; không thay trace và analyzer hiện có. |

Prometheus/Grafana hay Loki/Alloy chỉ nên xem xét nếu cần quan sát dài hạn hoặc tìm log qua nhiều run mà artifacts hiện tại không đáp ứng. Truy cập LAN cần thiết kế quyền điều khiển process riêng. Những mục này không thuộc bản Console local hiện tại.
