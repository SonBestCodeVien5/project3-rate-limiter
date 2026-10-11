# Kế hoạch triển khai tự động — 11/10/2026

## Phạm vi được giao

Phân tích repo, khởi tạo prototype và tự thực hiện plan → code → test → review → recode/retest → commit; lưu hồ sơ để viết báo cáo. Không tự đánh dấu hoàn thành việc học, protocol chính thức hoặc kết luận nghiên cứu.

## Quyết định kỹ thuật cho lượt triển khai này

- Go (`net/http`), go-redis v9, Redis Lua, Docker Compose và Nginx round-robin. Go sẵn trong môi trường; ít thành phần, có race detector và benchmark/testing chuẩn. Đây là lựa chọn kỹ thuật của lượt triển khai được ủy quyền, không phải yêu cầu nguồn.
- Client → Nginx → middleware limiter trong mỗi API instance → một backend mô phỏng dùng chung. Roadmap đặt lớp limiter trước backend; Proposal minh họa middleware. Giữ khác biệt nguồn rõ ràng và chọn middleware để đo local vs shared mà không thêm dịch vụ gateway.
- Client key: `X-Client-ID` bắt buộc trên `/work`, 1 request = 1 token. Đây là định danh workload tin cậy trong testbed, không phải authentication.
- Fixed Window: cửa sổ epoch `[floor(t/W)*W, (floor(t/W)+1)*W)`, chỉ allow tăng counter; reject không kéo dài TTL. Token Bucket: ban đầu đầy B, refill liên tục r token/giây, cap B; reject không tiêu token. Local có mutex; Redis quyết định toàn bộ trong Lua và dùng Redis TIME.
- Policy mặc định pilot: Q=20, W=1s, B=20, r=20/s; các giá trị phải cấu hình và lưu theo run. Không coi đây là tham số thực nghiệm được duyệt.
- Namespace Redis bao gồm run/policy/algorithm; không FLUSHDB. Local state dọn theo thời gian hết hiệu lực. Redis TTL của bucket ít nhất thời gian nạp đầy; Fixed Window hết hạn ở biên cửa sổ.
- Redis error: fail-closed trả 503; fail-open tiếp tục backend với nhãn rõ. Quota reject trả 429 và Retry-After. Timeout hữu hạn, tắt retry tự động để tránh tiêu quota hai lần khi mất phản hồi.
- Backend có semaphore capacity hữu hạn, service time cấu hình; quá tải trả 503 và ghi arrivals. Đây là mô hình năng lực giới hạn, không mô phỏng nghiệp vụ bán hàng.
- Generator open-loop theo lịch, giới hạn in-flight; ghi request bị bỏ do generator đầy riêng, không che offered load. JSONL raw + config/code version + summary; status, decisions, client class, instance, thời gian, latency, schedule lag.
- Redis outage chỉ pause/unpause container của Compose testbed có tên riêng, có cleanup trap. Số liệu lần này là smoke/pilot, chưa dùng làm kết luận RQ1–RQ5.

## Các bước và điều kiện đạt

1. **Analysis:** đọc context theo thứ tự nguồn; ghi repo sạch, chưa có code, môi trường và khoảng trống.
2. **Plan:** khóa semantics kỹ thuật ở trên; chia nhiệm vụ core limiter, HTTP/infra, workload/artifacts.
3. **Code:** hoàn thiện local/Redis FW/TB, HTTP flow, no-limiter baseline, Compose, runner và hướng dẫn.
4. **Test:** ca xác định với clock giả, boundary/refill/independent keys, concurrency và race detector; integration với Redis thật; HTTP và end-to-end smoke.
5. **Review:** review chéo implementation/đo đạc, ghi finding theo mức độ; không giấu test thất bại.
6. **Recode/retest:** sửa finding, lưu kết quả chạy lại; phân biệt test đã chạy, chưa chạy, giới hạn môi trường.
7. **Commit:** kiểm tra diff, chỉ stage các file của lượt làm này, commit local với kết quả có thật. Theo chỉ dẫn bổ sung của người dùng, chia nhỏ theo phần phụ thuộc: analysis/plan → policy/local → Redis → HTTP/backend → hạ tầng → loadgen → scripts → docs/evidence. Một vòng workflow có thể tạo nhiều commit; không ép một vòng = một commit. Không push.

## Chưa thuộc hoàn tất tự động lần này

Tự kiểm tra kiến thức của sinh viên, xác nhận của giảng viên, ngày/rubric chính thức, khóa protocol sau pilot, benchmark lặp đủ độ tin cậy, báo cáo/slide cuối kỳ. Sliding Window/dashboard/HA không triển khai.
