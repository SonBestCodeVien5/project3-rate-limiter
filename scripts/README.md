# Chạy kiểm tra và pilot

Các giá trị tải ở đây là lựa chọn kỹ thuật để smoke/pilot, chưa phải protocol được khóa hoặc kết luận RQ1–RQ5. Cần Go, Docker Compose, `curl` và GNU `timeout`. Các script Docker dùng cố định project `project3-lab`, từ chối chạy nếu project này đã có container, và dọn container do lượt chạy tạo ra khi thoát. Không dùng `FLUSHDB`.

```bash
bash scripts/verify.sh
bash scripts/pilot-matrix.sh
bash scripts/redis-outage.sh
```

- `verify.sh`: kiểm tra định dạng, vet, race tests, build, cú pháp shell, test cleanup và cấu hình Compose nếu có Docker. Test HTTP cần quyền mở socket localhost. Test Redis thực theo quy ước biến môi trường của package limiter; cần xem kết quả skipped để biết integration nào chưa chạy.
- `pilot-matrix.sh`: không limiter, local/Redis × Fixed Window/Token Bucket; mỗi case 5 giây, tổng 300 RPS, trong đó 20 RPS hợp lệ chia đều 5 client. Đây là hai luồng đều theo lịch, chưa phải kịch bản burst có pha bật/tắt.
- `redis-outage.sh`: Redis shared, mặc định Fixed Window, lần lượt fail-open/fail-closed; mỗi workload 10 giây, tổng 100 RPS, 20 RPS hợp lệ. Yêu cầu pause khoảng giây 3, giữ khoảng 2 giây rồi unpause. Có thể chọn `ALGORITHM=token-bucket`. Thời gian thao tác Docker cộng vào khoảng ngắt; dùng timestamp yêu cầu/hoàn tất trong `outage-events.txt` khi phân pha, không giả định pause chính xác 2 giây.

Hai script pilot nhận đường dẫn folder output ở đối số thứ nhất; mặc định dưới `artifacts/`. Mỗi case lưu cấu hình Compose đã resolve, HTTP metrics trước/sau của backend, metrics của API, log container, tài nguyên Redis và dữ liệu generator. Redis CPU là counter tích lũy cần lấy chênh lệch theo thời gian; không diễn giải trực tiếp thành % CPU. Outage chỉ lấy Redis INFO trước/sau để tránh client đo đạc bị kẹt khi Redis pause. Các thao tác INFO, snapshot, pause/unpause đều có timeout; cleanup luôn cố unpause trước khi dọn lab.

## Generator độc lập

```bash
go run ./cmd/loadgen -target http://localhost:8080/work \
  -duration 10s -rps 100 -legitimate-rps 20 -legitimate-clients 5 \
  -max-inflight 100 -timeout 2s -run-id example \
  -mode redis -algorithm fixed-window -fail-policy closed
```

Generator dùng `POST /work` để transport không tự retry request idempotent trên connection tái sử dụng; không theo redirect. `rps` là tổng tải, đã bao gồm `legitimate-rps`. Các client hợp lệ dùng key `legitimate-0001` trở đi; traffic còn lại dùng một key `abusive-0001`. Định danh này chỉ phục vụ workload, không phải authentication.

Giới hạn tối đa 10 phút/lượt, 2 triệu request dự kiến và 10.000 request in-flight. Khi hết slot hoặc trễ lịch quá `-max-schedule-lag`, generator ghi một record bị bỏ thay vì chờ hoặc dồn tải bù. Cần kiểm tra `generator_dropped` và `schedule_lag` trước khi coi offered load đã đạt yêu cầu.

Output gồm `metadata.json`, `requests.jsonl`, `summary.json`; folder dành cho generator phải chưa tồn tại. Metadata lưu argv, cấu hình, revision, trạng thái Git và môi trường chạy tối thiểu. Mode/algorithm/fail-policy ở CLI chỉ là nhãn do người chạy cung cấp; cấu hình Compose mới là bằng chứng cấu hình server trong runner.

Summary có p50/p95/p99 nearest-rank, status/error/decision counts, goodput và tail latency của client hợp lệ thành công. Mẫu latency tổng gồm mọi request đã gửi, kể cả timeout; `latency_by_decision` tách allow/reject/fail policy. Percentile bằng 0 khi không có mẫu nghĩa là chưa có dữ liệu. Rate/goodput dùng toàn thời gian thực từ lúc bắt đầu đến khi drain xong, không chỉ duration cấu hình. Timeout là tập con transport error; HTTP status có thể trùng response-body error. Số backend arrivals từ header chỉ là xác nhận nhận được ở client, cần đối chiếu counter backend để tính cả request bị mất phản hồi.

Chưa có oracle độc lập trong summary: không gọi việc Token Bucket nhận hơn Q trong cửa sổ Fixed Window là overshoot. JSONL lưu thời điểm quyết định, client key và instance để hỗ trợ phân tích tiếp theo. Protocol chính thức vẫn cần workload burst, so sánh một/nhiều instance, lặp nhiều lượt, oracle từng thuật toán và tiêu chí recovery cụ thể.
