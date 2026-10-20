# Cổng đo pilot sau khi sửa lỗi

**Trạng thái hiện tại (20/10/2026):** T09 đã hoàn tất; T10 chưa bắt đầu, chưa có kết luận RQ và không được chạy thêm tải. Các lệnh dưới đây mô tả cổng pilot lịch sử. Xem [kế hoạch việc còn lại](../REMAINING_WORK_PLAN.md).

Đây là cổng pilot có thể chạy lại, không phải protocol đã khóa hay benchmark chính thức. Cổng giữ nguyên PRESET: Redis Fixed Window, 2 API instance, 5 key hợp lệ, Q=B=20, W=1000 ms, refill 20/s, backend capacity 4/service 50 ms, 30 giây mỗi lượt, giới hạn Redis 100 ms và giới hạn generator từ `research-pilot.sh`. Cổng chạy normal 20 RPS × 3, sau đó mixed tổng 120 / hợp lệ 20 RPS × 3. Chất lượng được kiểm tra sau từng lượt. Cờ chất lượng lặp lại sẽ dừng chuỗi; các lượt không hợp lệ và log vẫn được giữ trong thư mục output duy nhất.

Dùng checkout sạch, detached tại revision cố định và đường dẫn output mới:

```sh
python3 scripts/observe-clock.py --output artifacts/clock-observe-NEW --duration-seconds 90
```

Trước tiên kiểm tra `summary.json`. Chỉ chạy gate nếu `clock_steps_above_5ms` rỗng; nếu phát hiện bước nhảy thì môi trường chưa sẵn sàng. Lần quan sát ngày 19/10/2026 trước đó ghi nhận ba bước nhảy realtime khoảng 2.93–2.96 giây trong 90 giây ([worklog clock lịch sử](../worklog/2026-10-19-clock/README.md)). Sau remediation T01, observer 90 giây mới đã đạt và gate T03 gồm sáu lượt đã qua kiểm tra chất lượng; bằng chứng và giới hạn nằm trong [worklog T02/T03](../worklog/2026-10-19-measurement-gate/README.md).

```sh
bash scripts/run-measurement-gate.sh --output-root artifacts/measurement-gate-NEW --timeout-seconds 240
```

Gate từ chối checkout đo có thay đổi và đường dẫn output đã tồn tại. Giới hạn 240 giây mỗi lượt gồm build, khởi động, tải và cleanup; chỉ điều chỉnh trước khi bắt đầu nếu host cần thời gian dài hơn, đồng thời ghi lại thay đổi. Observer lưu `samples.jsonl`, `summary.json` và `metadata.json`; `clock_steps_above_5ms` báo độ lệch wall/monotonic. Danh sách bước nhảy rỗng chỉ đạt kiểm tra ban đầu; gate từng lượt vẫn kiểm tra clock residual. Hai kiểm tra này và cả sáu lượt gate đạt đều không khóa protocol nghiên cứu hay xác lập độ ổn định clock ngoài khoảng đã quan sát. Nếu sau này được yêu cầu lặp lại và không chắc phiên liên tục, trước hết cần observer mới đạt; calibration T04–T08 và khóa protocol là các điều kiện riêng cho phép đo chính thức.
