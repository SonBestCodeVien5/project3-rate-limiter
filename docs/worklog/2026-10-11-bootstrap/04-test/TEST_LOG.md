# Kiểm thử ban đầu

## Lỗi môi trường đã gặp

1. `go get` trong sandbox không mở được socket DNS. Sau escalation tải go-redis v9.17.0 thành công; checksum ở go.sum.
2. Docker socket không truy cập được từ sandbox. Escalation đã chấp thuận, chạy container Redis riêng loopback 16380.
3. Go cache mặc định ngoài writable roots gây `read-only file system` và lỗi package phụ gây hiểu nhầm. Đổi `GOCACHE=/tmp/project3-go-cache`.
4. HTTP tests dùng httptest không bind socket trong sandbox. Chạy có quyền loopback đã PASS. Không tính lỗi môi trường là lỗi implementation.
5. Git index trong sandbox readonly; commit được chạy qua escalation theo yêu cầu user, không push.

## Kết quả

- [local-initial.log](local-initial.log): race tests local PASS; Redis tests SKIP do không truyền địa chỉ (ghi rõ trong log).
- [redis-initial.log](redis-initial.log): local và Redis thật PASS với `REDIS_TEST_ADDR=127.0.0.1:16380` và `-race -v`.
- Redis control không atomic buộc 16 goroutine cùng đọc counter 0: 16 admissions với Q=1, counter cuối 1, overshoot 15. Đây là controlled interleaving, không phải tần suất race quan sát tự nhiên.
- Agent HTTP và experiment chạy race tests riêng thành công; kết quả toàn bộ được lưu tại `06-retest/verify.log` sau tích hợp.

Review sau test tìm lỗi có thể xảy ra mà test đầu không bắt được; xem `05-review`. Test pass không thay cho review semantics/measurement.
