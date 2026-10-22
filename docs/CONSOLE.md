# Demo Console: quy trình triển khai và vận hành

Console là giao diện local cho pilot, không thay đổi protocol hoặc phép đo của runner. Ba preset cố định là `mixed-none`, `mixed-local`, `mixed-redis` (tổng RPS 21..1000); chế độ `custom` cho phép chọn workload, mode, thuật toán, topology và policy trong các giới hạn bên dưới. Mỗi lượt chạy chọn một case, lặp 1..3 lượt. Roadmap/Proposal chỉ yêu cầu các thí nghiệm rate limiting; Console là lựa chọn kỹ thuật để trình bày demo.

**Trạng thái hiện tại (22/10/2026):** T09 và phân tích offline T10 đã hoàn tất; không có quyền tải mới. Các lệnh chạy trong tài liệu này ghi lại quy trình lịch sử. Saved-run UI là công cụ xem/so sánh artifact pilot và không thay kết quả T10. Xem [kết quả T10](analysis/T10_RESULTS.md), [trạng thái sẵn sàng](experiments/PROTOCOL_READINESS.md), [kế hoạch việc còn lại](REMAINING_WORK_PLAN.md) và gói [demo/source T12](DEMO_PACKAGE.md).

## Quy trình phát triển

1. **Bộ điều khiển và runner:** xác thực preset/tham số ở server, khóa một runner, tạo Run ID và artifact riêng, dùng runner hiện có làm nguồn thực thi; kiểm tra request sai, tranh chấp lượt chạy, hủy và đường dẫn artifact.
2. **Giao diện và số liệu:** stack mặc định chỉ đọc, request mẫu, snapshot trực tiếp có nhãn nguồn, trạng thái và summary theo lượt, tải artifact; chạy thử HTTP/UI.
3. **Rà soát và tích hợp:** `bash scripts/verify.sh`, chạy `go run ./cmd/console`, thử một preset trên Docker thật, kiểm tra `summary.json`, `policy.json`, `compose-resolved.json` và `docker ps` sau khi hoàn tất hoặc hủy; sửa rồi chạy lại phần bị ảnh hưởng.
4. **Commit:** commit các phần đã qua kiểm tra/rà soát theo thứ tự bộ điều khiển/runner, giao diện, tài liệu hoặc sửa tích hợp. Không coi giá trị pilot là ngưỡng đánh giá nghiên cứu.

## Chạy demo

Yêu cầu Go, Docker Compose, `curl`, Python 3, GNU `timeout` và `flock`. Chạy từ gốc repo:

```bash
go run ./cmd/console
# Mở http://127.0.0.1:8090
```

Phần **Stack mặc định** đọc các cổng loopback 8080/18081/18082/18083; nếu muốn dùng phần này, khởi động `docker compose up -d --build --wait` riêng. Nút request mẫu gửi một `POST /work` với client ID cố định `console-demo` vào stack mặc định. Phần benchmark gọi `scripts/research-pilot.sh` với một preset; runner dùng project `project3-research-lab` và cổng ingress 18080. Nó từ chối nếu project đã có container hoặc runner khác đang giữ khóa. Các lượt chạy nằm dưới `artifacts/console/<Run ID>/`, gồm request, trạng thái, log và `result/` của runner. CLI tương đương:

```bash
MIXED_RPS=120 bash scripts/research-pilot.sh --case mixed-redis --repetitions 1 --analyze --output artifacts/example-new-dir
```

Console chỉ bind `127.0.0.1`. `/api/runs/{id}/metrics` thăm dò `/metrics` trong container qua Docker exec khi lượt chạy hoạt động; đó là bộ đếm tích lũy theo container, lấy mẫu theo thời điểm, không phải delta hay kết quả cuối. Việc thăm dò có chi phí phụ; dùng artifact before/after và trace của runner để phân tích nghiên cứu. `summary.json` chỉ xuất hiện sau khi load generator gửi xong và drain; `analysis.json` là kết luận của analyzer, Console không tự suy diễn.

Chế độ **Tùy chỉnh** hỗ trợ `normal`, `mixed`, `burst`, `concurrent`; 1/2/4 API; tắt limiter/local/Redis; Fixed Window hoặc Token Bucket; fail-open/closed khi dùng Redis. Có thể đặt tổng tải 1..1000 RPS, tải hợp lệ 0..1000 RPS (không vượt tổng), thời lượng 3..30 giây, quota 1..1000, window 100..9999 ms, bucket capacity/refill 1..1000, backend capacity 1..100 và service time 0..1000 ms. Burst có mốc bắt đầu, thời lượng và RPS riêng cho luồng bất thường; concurrent có mốc và số request trong batch. `normal` dùng toàn bộ RPS làm tải hợp lệ. Với `concurrent`, số request batch quyết định tải thực tế; ô RPS chỉ là nhãn trong metadata. Trường không liên quan đến mode/profile được ẩn, nhưng request và `policy.json`/`compose-resolved.json` vẫn ghi đủ cấu hình để tái hiện. Đây là biên an toàn của demo, không phải tham số protocol nghiên cứu đã khóa.

Ví dụ tái hiện một lượt chạy tùy chỉnh qua CLI (các `CUSTOM_*` khác dùng mặc định trong [scripts/README.md](../scripts/README.md)):

```bash
CUSTOM_MODE=redis CUSTOM_ALGORITHM=token-bucket CUSTOM_PROFILE=burst \
CUSTOM_INSTANCES=4 CUSTOM_RPS=60 CUSTOM_LEGIT_RPS=10 CUSTOM_DURATION=6 \
CUSTOM_CAPACITY=15 CUSTOM_RATE=12 CUSTOM_BACKEND_CAPACITY=4 \
CUSTOM_BURST_RPS=100 bash scripts/research-pilot.sh --case custom --analyze
```

Khi hủy hoặc dừng Console bằng SIGINT/SIGTERM, controller gửi SIGTERM tới process group, đợi runner cleanup rồi kiểm tra container của project. Nếu Console bị SIGKILL/restart bất ngờ, lượt chạy dở được đánh dấu `interrupted`; kiểm tra `docker ps --filter label=com.docker.compose.project=project3-research-lab` và log trước khi chạy lại. Runner giữ khóa trong suốt tiến trình còn chạy. `cleanup-error` nghĩa là còn container hoặc không xác minh được cleanup; cần kiểm tra thủ công trước khi diễn tập tiếp.

Phạm vi hiện tại chưa cho chỉnh fault injection từ UI. Các biểu đồ, history database và truy cập LAN cũng chưa có.

## Kết quả tích hợp thực chạy

[Ma trận ngày 12/10/2026](worklog/2026-10-12-console-matrix/README.md) đã gửi 84 tổ hợp hợp lệ qua API Console: 4 profile × 7 tổ hợp mode/algorithm/fail policy × 3 topology. Mỗi cấu hình chạy một lượt 3 giây; 84 lượt chạy hoàn tất và artifact khớp. Analyzer ghi 2 vi phạm quan sát được, 40 lượt `inconclusive` (chưa đủ bằng chứng kết luận), 19 lỗi limiter Redis và 5 request bị generator bỏ. Playwright đã kiểm tra một lượt tùy chỉnh và tràn giao diện desktop/mobile; ma trận API không tương đương 84 lượt kiểm tra biểu mẫu. CSV bổ sung delta backend và tổng bộ đếm của mọi API; archive giữ dữ liệu gốc để dẫn báo cáo.

## Giao diện và hướng phát triển

Bộ chọn **Lượt xem kết quả** hiển thị riêng từng lượt 1..3, giữ lượt đang chọn khi thăm dò và ghi rõ lượt chưa có summary. Trạng thái oracle lấy trực tiếp từ `analysis.json` của lượt đó; thiếu hoặc lỗi JSON hiển thị chưa có analyzer, không suy diễn từ runner complete. Request bị generator bỏ hiển thị riêng; lỗi limiter là tổng delta `limiter_errors` của đủ API trong các bộ đếm, thiếu bất kỳ API nào hiển thị **Thiếu counters** (thiếu bộ đếm). Goodput/p95 hợp lệ ghi **Không áp dụng** khi không có request hợp lệ (kể cả chế độ concurrent); nếu đã gửi nhưng không có mẫu hợp lệ thành công thì p95 ghi **Không có mẫu thành công**.

Kiểm tra phần này bằng `go test ./internal/console` và `node internal/console/index_test.js` (Node chỉ dùng cho kiểm thử giao diện, không phải dependency runtime). Test API bao phủ summary/analyzer riêng từng lượt và JSON lỗi; kiểm thử giao diện bao phủ đổi lượt, polling, thiếu artifact và concurrent.

Bản hiện tại đặt chỉ số cuối lượt thành các thẻ riêng (request đã gửi, 2xx, 429, goodput và p95 của client hợp lệ, số yêu cầu được xác nhận đã tới backend). Cấu hình thực tế, snapshot từng instance và artifact vẫn xem được; JSON thô nằm trong phần mở rộng để dòng dài không kéo giãn trang. Cách phân cấp thẻ chỉ số và phần xem chi tiết được tham khảo từ [Custom Dashboards của Langfuse](https://langfuse.com/docs/metrics/features/custom-dashboards); Console không dùng Langfuse hay dữ liệu LLM.

Phần **So sánh các lượt đã lưu** chọn ba lượt hoàn tất riêng cho none/local/Redis, rồi đọc metadata load generator, policy, Compose đã resolve, nginx config, revision/working tree và image ID/digest qua danh sách artifact cho phép. Với `image-inspect.json`, mỗi mục inspect phải khớp đúng ID trong `images.json`; fingerprint của image dùng toàn bộ RootFS layer digests, Config, OS/architecture/variant và platform. Chỉ coi hai ID khác nhau là cùng nội dung khi các trường thực tế này khớp; không suy ra từ revision. Lượt cũ thiếu inspect tiếp tục được so theo ID chính xác; inspect sai định dạng hoặc không khớp ID sẽ bị từ chối. Ghép lượt cũ với lượt có inspect vẫn có thể bị từ chối thận trọng dù ID trùng. Bảng bị từ chối nếu thiếu bằng chứng, working tree chưa sạch, mode thực tế khác lựa chọn, hoặc workload/phân bố key, policy, backend, topology, runtime hay image identity không khớp. Mode và namespace là hai khác biệt được phép; fail policy và thuật toán vẫn phải khớp. Summary và metadata phải có cùng run_id của lượt được chọn; policy phải có đủ trường thuật toán, fail policy và quota. Bảng ghi Run ID/lượt, trạng thái oracle và delta lỗi limiter của đủ API; nếu thiếu bộ đếm thì ghi rõ. Bảng hiển thị goodput hợp lệ, p95/p99 của request hợp lệ thành công, 429/5xx/timeout/lỗi truyền tải, request bị generator bỏ và request backend nhận/quá tải theo delta bộ đếm từ analyzer. Không gộp percentile, xếp hạng hoặc tuyên bố mode thắng. Đây là lớp trình bày tùy chọn, không xác nhận protocol hay chất lượng trace; cần kiểm tra oracle và các artifact. Lượt lịch sử có working tree bẩn vẫn bị từ chối dù thay đổi chỉ nằm ở tài liệu.

Các mục sau là **đề xuất tùy chọn**, không phải yêu cầu Roadmap/Proposal hoặc tính năng đã triển khai:

[Kiểm chứng nội dung image ngày 13/10](worklog/2026-10-13-console-content/README.md) đã chạy ba Console mode trên Docker thật: bảng được chấp nhận khi nội dung runtime khớp, cơ chế kiểm tra từ chối thay workload/layer và bảng không gây tràn giao diện trang desktop/mobile. Một lượt vẫn có bước nhảy clock; đây là tích hợp giao diện, không phải benchmark hoặc kết quả gate chính thức đạt. UI nhắc kiểm tra clock/tải thực/oracle trước diễn giải.

| Ưu tiên | Tính năng có thể thêm | Điều kiện trước khi làm |
| --- | --- | --- |
| 2 | Biểu đồ nhỏ từ các artifact sau lượt chạy: traffic hợp lệ/toàn tải, quyết định limiter và backend overload theo thời gian | Kiểm tra timestamp, đơn vị, dropped requests và tác động của xử lý dữ liệu; không gọi snapshot cuối là live. |
| 3 | Thêm preset có tham số khóa cho normal/burst/concurrent/scale; các profile/topology này đã chọn được trong custom | Pilot và protocol phải xác định tổ hợp hợp lệ, giới hạn tải, phép so sánh và nhãn cấu hình thực tế. |
| 4 | Hiện tiến trình runner và Redis CPU/memory sample rõ thời điểm lấy | Cần đo overhead polling/sampling trước khi dùng số liệu này trong báo cáo. |
| 5 | Trình diễn Redis outage có thời lượng cố định và cleanup được kiểm chứng | Chỉ sau khi fault injection CLI ổn định; không mở lệnh Docker hay thời lượng tùy ý từ trình duyệt. |
| Sau cùng | Export gói artifact/báo cáo hoặc dashboard lưu lịch sử nhiều lượt chạy | Chỉ thêm khi một buổi demo/đánh giá thật cần; không thay trace và analyzer hiện có. |

Prometheus/Grafana hay Loki/Alloy chỉ nên xem xét nếu cần quan sát dài hạn hoặc tìm log qua nhiều lượt chạy mà các artifact hiện tại không đáp ứng. Truy cập LAN cần thiết kế quyền điều khiển process riêng. Những mục này không thuộc bản Console local hiện tại.
