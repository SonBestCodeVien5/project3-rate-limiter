# Positioning Against Existing Solutions — ghi chú cho repo

[Bản đầy đủ trên Google Drive](https://docs.google.com/document/d/1jTDYHtqYIJ8YR2O12_2SMH8QRvUGPmGJHNXH_H2ZfpU/edit)

Nginx, Envoy, các limiter dựa trên Redis và Cloud API Gateway đã có khả năng rate limiting ở những mức độ khác nhau. Project 3 **không** nhằm thay thế sản phẩm production. Đóng góp của dự án là một nền tảng thí nghiệm nhỏ để phân tích thuật toán, trade-off của distributed state, correctness khi concurrent requests và performance.

Khi so sánh với giải pháp hiện có, chỉ dùng chúng để định vị vấn đề nghiên cứu; không mở rộng phạm vi thành gateway hoặc service mesh.

Baseline cập nhật chứng minh đóng góp bằng dữ liệu về quota correctness dưới concurrency, khả năng phục vụ client hợp lệ khi backend quá tải, và trade-off của fail-open/fail-closed khi Redis unavailable. Đây là tiêu chí đánh giá của Project 3, không phải tuyên bố đạt production readiness.
