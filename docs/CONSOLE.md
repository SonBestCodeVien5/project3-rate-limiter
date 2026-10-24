# Demo Console: quy trình triển khai và vận hành

Console là giao diện local cho pilot, không thay đổi protocol hoặc phép đo của runner. Ba preset cố định là `mixed-none`, `mixed-local`, `mixed-redis` (tổng RPS 21..1000); chế độ `custom` cho phép chọn workload, mode, thuật toán, topology và policy trong các giới hạn bên dưới. Mỗi lượt chạy chọn một case, lặp 1..3 lượt. Roadmap/Proposal chỉ yêu cầu các thí nghiệm rate limiting; Console là lựa chọn kỹ thuật để trình bày demo.

**Trạng thái hiện tại:** T09 và phân tích offline T10 đã hoàn tất; tài liệu mô tả Console, không cấp quyền tải mới. Saved-run UI xem/so sánh artifact pilot, không thay kết quả T10. Stack monitoring cố định và dashboard đã được kiểm tra trong P2-03. Nút `Gửi một request mẫu` gửi một request qua ingress fixed stack. Nút **Chạy benchmark** dùng `research-pilot.sh` trên project `project3-research-lab`; checkbox monitoring tùy chọn đăng ký API/backend của case hiện tại qua file_sd. Triển khai P2-03A mới có kiểm tra G1; G2 scrape/runtime và G3 Console acceptance vẫn chờ bằng chứng/quyền tương ứng. Xem [registry P2](monitoring/PHASE2_PLAN.md), [kết quả T10](analysis/T10_RESULTS.md), [readiness](experiments/PROTOCOL_READINESS.md), [kế hoạch task](REMAINING_WORK_PLAN.md) và [demo/source T12](DEMO_SCRIPT.md#source-và-phiên-bản).

## Chạy demo

Yêu cầu Go, Docker Compose, `curl`, Python 3, GNU `timeout` và `flock`. Chạy từ gốc repo:

```bash
go run ./cmd/console
# Mở http://127.0.0.1:8090
```

Phần **Stack mặc định** đọc các cổng loopback 8080/18081/18082/18083; nếu muốn dùng request mẫu, khởi động stack monitoring theo [runbook](monitoring/RUNBOOK.md) (`project3-monitoring-demo`). Nút request mẫu gửi một `POST /work` với client ID cố định `console-demo` tới ingress đó; sau scrape, counter của fixed stack hiện trên dashboard. Compose base mặc định là Redis/Fixed Window. Giá trị **Không limiter, 120 RPS, 1 lượt** ở form benchmark là cấu hình cho research run mới, không phải trạng thái stack đang chạy. Nút **Chạy benchmark** gọi `scripts/research-pilot.sh` trong project `project3-research-lab` và ingress 18080. Runner từ chối project đã có container hoặc runner khác đang giữ khóa. Khi bật checkbox monitoring, runner đăng ký `api1`…`api4` và `backend` trên network `project3-monitoring-scrape`, chờ scrape baseline/lookback trước load, giữ target tới final scrape sau drain, rồi gỡ manifest trước cleanup. Không nối Redis/Nginx hoặc đưa Run ID vào target labels. Opt-out giữ nguyên đường chạy hiện tại. Các lượt nằm dưới `artifacts/console/<Run ID>/`, gồm request, trạng thái, log và `result/` runner. CLI bên dưới mặc định không bật monitoring:

```bash
MIXED_RPS=120 bash scripts/research-pilot.sh --case mixed-redis --repetitions 1 --analyze --output artifacts/example-new-dir
```

Console chỉ bind `127.0.0.1`. `/api/runs/{id}/metrics` thăm dò `/metrics` trong container qua Docker exec khi lượt chạy hoạt động; đây là bộ đếm tích lũy theo container, không phải delta hay time series. Run monitoring lưu UTC baseline/lookback, thời điểm bắt đầu và kết thúc lịch tải lấy từ metadata loadgen, thời điểm generator drain từ `summary.json`, final scrape theo từng service và Grafana URL theo đúng bounds tải. Sau khi run kết thúc, Console hiển thị link với `job=project3-console-run` và cửa sổ rate 4s; samples nằm trong Prometheus TSDB sau Compose cleanup theo retention. `analysis.json` là kết luận của analyzer, Console không tự suy diễn. Opt-in telemetry thay đổi runtime qua shared scrape network; không dùng run đó để đại diện T09/T10. Nếu runner bị hủy/lỗi, record giữ trạng thái incomplete; manifest còn sót sau kill cứng làm runner kế tiếp từ chối đăng ký cho tới khi xác minh ownership.

Chế độ **Tùy chỉnh** hỗ trợ `normal`, `mixed`, `burst`, `concurrent`; 1/2/4 API; tắt limiter/local/Redis; Fixed Window hoặc Token Bucket; fail-open/closed khi dùng Redis. Có thể đặt tổng tải 1..1000 RPS, tải hợp lệ 0..1000 RPS (không vượt tổng), thời lượng 3..30 giây, quota 1..1000, window 100..9999 ms, bucket capacity/refill 1..1000, backend capacity 1..100 và service time 0..1000 ms. Burst có mốc bắt đầu, thời lượng và RPS riêng cho luồng bất thường; concurrent có mốc và số request trong batch. `normal` dùng toàn bộ RPS làm tải hợp lệ. Với `concurrent`, số request batch quyết định tải thực tế; ô RPS chỉ là nhãn trong metadata. Trường không liên quan đến mode/profile được ẩn, nhưng request và `policy.json`/`compose-resolved.json` vẫn ghi đủ cấu hình để tái hiện. Đây là biên an toàn của demo, không phải tham số protocol nghiên cứu đã khóa.

Ví dụ tái hiện một lượt chạy tùy chỉnh qua CLI (các `CUSTOM_*` khác dùng mặc định trong [scripts/README.md](../scripts/README.md)):

```bash
CUSTOM_MODE=redis CUSTOM_ALGORITHM=token-bucket CUSTOM_PROFILE=burst \
CUSTOM_INSTANCES=4 CUSTOM_RPS=60 CUSTOM_LEGIT_RPS=10 CUSTOM_DURATION=6 \
CUSTOM_CAPACITY=15 CUSTOM_RATE=12 CUSTOM_BACKEND_CAPACITY=4 \
CUSTOM_BURST_RPS=100 bash scripts/research-pilot.sh --case custom --analyze
```

Khi hủy hoặc dừng Console bằng SIGINT/SIGTERM, controller gửi SIGTERM tới process group, đợi runner cleanup rồi kiểm tra container của project. Nếu Console bị SIGKILL/restart bất ngờ, lượt chạy dở được đánh dấu `interrupted`; kiểm tra `docker ps --filter label=com.docker.compose.project=project3-research-lab` và log trước khi chạy lại. Runner giữ khóa trong suốt tiến trình còn chạy. `cleanup-error` nghĩa là còn container hoặc không xác minh được cleanup; cần kiểm tra thủ công trước khi diễn tập tiếp.


## Kết quả tích hợp thực chạy

[Ma trận ngày 12/10/2026](worklog/2026-10-12-console-matrix/README.md) đã gửi 84 tổ hợp hợp lệ qua API Console: 4 profile × 7 tổ hợp mode/algorithm/fail policy × 3 topology. Mỗi cấu hình chạy một lượt 3 giây; 84 lượt chạy hoàn tất và artifact khớp. Analyzer ghi 2 vi phạm quan sát được, 40 lượt `inconclusive` (chưa đủ bằng chứng kết luận), 19 lỗi limiter Redis và 5 request bị generator bỏ. Playwright đã kiểm tra một lượt tùy chỉnh và tràn giao diện desktop/mobile; ma trận API không tương đương 84 lượt kiểm tra biểu mẫu. CSV bổ sung delta backend và tổng bộ đếm của mọi API; archive giữ dữ liệu gốc để dẫn báo cáo.

## Giao diện và hướng phát triển

Bộ chọn **Lượt xem kết quả** hiển thị riêng từng lượt 1..3, giữ lượt đang chọn khi thăm dò và ghi rõ lượt chưa có summary. Trạng thái oracle lấy trực tiếp từ `analysis.json` của lượt đó; thiếu hoặc lỗi JSON hiển thị chưa có analyzer, không suy diễn từ runner complete. Request bị generator bỏ hiển thị riêng; lỗi limiter là tổng delta `limiter_errors` của đủ API trong các bộ đếm, thiếu bất kỳ API nào hiển thị **Thiếu counters** (thiếu bộ đếm). Goodput/p95 hợp lệ ghi **Không áp dụng** khi không có request hợp lệ (kể cả chế độ concurrent); nếu đã gửi nhưng không có mẫu hợp lệ thành công thì p95 ghi **Không có mẫu thành công**.

Kiểm tra phần này bằng `go test ./internal/console` và `node internal/console/index_test.js` (Node chỉ dùng cho kiểm thử giao diện, không phải dependency runtime). Test API bao phủ summary/analyzer riêng từng lượt và JSON lỗi; kiểm thử giao diện bao phủ đổi lượt, polling, thiếu artifact và concurrent.

Phần **So sánh các lượt đã lưu** chọn ba lượt hoàn tất riêng cho none/local/Redis, rồi đọc metadata load generator, policy, Compose đã resolve, nginx config, revision/working tree và image ID/digest qua danh sách artifact cho phép. Với `image-inspect.json`, mỗi mục inspect phải khớp đúng ID trong `images.json`; fingerprint của image dùng toàn bộ RootFS layer digests, Config, OS/architecture/variant và platform. Chỉ coi hai ID khác nhau là cùng nội dung khi các trường thực tế này khớp; không suy ra từ revision. Lượt cũ thiếu inspect tiếp tục được so theo ID chính xác; inspect sai định dạng hoặc không khớp ID sẽ bị từ chối. Ghép lượt cũ với lượt có inspect vẫn có thể bị từ chối thận trọng dù ID trùng. Bảng bị từ chối nếu thiếu bằng chứng, working tree chưa sạch, mode thực tế khác lựa chọn, hoặc workload/phân bố key, policy, backend, topology, runtime hay image identity không khớp. Mode và namespace là hai khác biệt được phép; fail policy và thuật toán vẫn phải khớp. Summary và metadata phải có cùng run_id của lượt được chọn; policy phải có đủ trường thuật toán, fail policy và quota. Bảng ghi Run ID/lượt, trạng thái oracle và delta lỗi limiter của đủ API; nếu thiếu bộ đếm thì ghi rõ. Bảng hiển thị goodput hợp lệ, p95/p99 của request hợp lệ thành công, 429/5xx/timeout/lỗi truyền tải, request bị generator bỏ và request backend nhận/quá tải theo delta bộ đếm từ analyzer. Không gộp percentile, xếp hạng hoặc tuyên bố mode thắng. Đây là lớp trình bày tùy chọn, không xác nhận protocol hay chất lượng trace; cần kiểm tra oracle và các artifact. Lượt lịch sử có working tree bẩn vẫn bị từ chối dù thay đổi chỉ nằm ở tài liệu.

Biểu đồ artifact, preset khóa, tiến trình runner và outage UI là đề xuất tùy chọn; chưa phải tính năng hiện có hoặc yêu cầu baseline. Fault injection từ UI, history database và truy cập LAN hiện chưa có.

Prometheus/Grafana thuộc stack cố định P2 đã được kiểm tra; request mẫu trong Console đi qua đúng ingress fixed stack. P2-03A đã thêm opt-in scrape cho nút **Chạy benchmark** hiện có mà không đổi generator; runtime acceptance chưa được ghi nhận tại đây. Alloy/Loki còn chờ. Truy cập LAN cần thiết kế quyền điều khiển process riêng.
