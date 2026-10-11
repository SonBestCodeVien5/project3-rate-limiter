# Phân tích repo và khoảng trống

Ngày làm việc theo phiên người dùng: 11/10/2026, Asia/Bangkok. Commit xuất phát: `1bcb44e`. Working tree ban đầu sạch, nhánh `main` tracking `origin/main`.

## Vấn đề doanh nghiệp → tác động

API flash sale giả định gặp tải tăng/bất thường; local quota có thể nhân theo số instance, cập nhật shared state không atomic có thể sai dưới concurrency. Backend quá tải làm giảm khả năng phục vụ khách hợp lệ. Đây là rủi ro giả định, chưa phải thiệt hại doanh thu quan sát được.

## Nguồn và yêu cầu

Đã đọc PROJECT_BRIEF, SOURCE_INDEX rồi Roadmap → Proposal → Supplementary Research Context → Positioning; đọc thêm PROJECT_ROADMAP, EXPERIMENT_SPEC, WEEK1_BUSINESS_CASE, SCOPE_REASSESSMENT. Dùng notes đã sync 08/10; không có bằng chứng nguồn đổi, không kết nối Drive chỉ để đọc lại.

Baseline bắt buộc gồm FW/TB, local/Redis, nhiều instance, atomicity, normal/burst/concurrent/scaling, mixed traffic và Redis outage hữu hạn. Dashboard, Sliding Window, HA/gateway nằm ngoài lượt triển khai.

Repo chỉ có Markdown và skill sync-context, chưa có app, test, build/CI, cấu hình hạ tầng hoặc raw data. Roadmap là lịch đề xuất; chưa có protocol được khóa. Cổng kiến thức tuần 1 chưa hoàn tất và không thể tự đánh dấu thay người học.

## Khác biệt nguồn cần xử lý

Roadmap minh họa lớp limiter trước backend; Proposal minh họa gắn limiter vào API. Chọn middleware trước backend dùng chung, ghi thành quyết định kỹ thuật ở PLAN, không sửa nội dung notes của nguồn. Atomicity là yêu cầu; Lua là cơ chế chọn cho prototype. Đối chứng không atomic được giới hạn trong integration test có barrier, không đưa vào chế độ API sử dụng thường xuyên.

## Môi trường quan sát

- Linux amd64, Python 3.12.3, Go 1.26.1, Docker 29.3.1, Compose v5.1.1.
- Git identity đã cấu hình; user yêu cầu commit tự động, không yêu cầu push.
- Sandbox chặn mạng/download và Docker socket; escalation cho tải dependency/chạy Docker đã được chấp thuận.
- Cache Go mặc định ngoài writable roots gây lỗi build; dùng `GOCACHE=/tmp/project3-go-cache`.
- Redis thật cho integration test chạy container riêng `project3-bootstrap-redis`, loopback port 16380; không sử dụng Redis/dữ liệu có sẵn.

## Điều chỉnh tiến độ

Tự động hóa phần triển khai kỹ thuật tuần 2–7 theo semantics cụ thể, không coi các tuần nghiên cứu/học đã hoàn tất. Dữ liệu lần này là verification/smoke; protocol, tải chính thức, số lượt lặp, quota violation trong outage và hồi phục vẫn cần pilot/đánh giá trước kết luận.
