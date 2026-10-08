# Project 3 Proposal — ghi chú cho repo

[Bản đầy đủ trên Google Drive](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) · Đề cương chính thức; Roadmap được ưu tiên nếu có khác biệt

## Đề tài và bài toán

**Nghiên cứu và xây dựng cơ chế kiểm soát lưu lượng phân tán cho hệ thống API nhiều instance.** Proposal dùng tình huống doanh nghiệp giả định vận hành API bán hàng trong đợt flash sale. Nếu limiter giữ state cục bộ tại mỗi instance, tổng request được chấp nhận có thể vượt quota chung; nếu cập nhật Redis không atomic, concurrent requests vẫn có thể gây race condition. Traffic vượt kiểm soát có thể làm API/database chậm hoặc lỗi, ảnh hưởng người mua hợp lệ và tạo rủi ro mất giao dịch. Đây là kịch bản nghiên cứu, chưa có số liệu sự cố doanh nghiệp thật.

## Câu hỏi nghiên cứu

1. Thuật toán rate limiting ảnh hưởng thế nào đến latency, throughput và burst traffic?
2. Distributed shared state ảnh hưởng thế nào đến correctness và performance?
3. Hệ thống thay đổi thế nào khi tăng số lượng API instance?
4. Atomic operation như Redis Lua Script có cải thiện correctness khi có concurrent requests không?
5. Trong tải hỗn hợp hoặc khi Redis tạm thời unavailable, limiter thay đổi khả năng phục vụ client hợp lệ, quota correctness và độ trễ ra sao?

## Phạm vi và kết quả

- **Bắt buộc theo Proposal cập nhật:** API instances, Redis shared state, rate limiter, Fixed Window, Token Bucket, load testing và performance evaluation; kiểm chứng quyết định quota atomic dưới concurrent load; workload hỗn hợp để đo bảo vệ backend/client hợp lệ; fault injection Redis ngắn và có kiểm soát.
- **Mở rộng theo Proposal cập nhật:** Sliding Window, so sánh thêm Redis Functions với cơ chế atomic đã chọn và monitoring. Atomicity là phần lõi; Lua Script là một cơ chế có thể chọn, không phải thuật toán rate limiting thứ ba.
- **Đánh giá:** allow/reject correctness và overshoot; p50/p95/p99 latency; requests/giây; Redis CPU/memory và network overhead. Với workload hỗn hợp, đo goodput và p95/p99 của client hợp lệ, request vào backend, 429, timeout/5xx. Khi Redis unavailable, đo quota violation, availability và recovery; không suy kết quả thành độ sẵn sàng production.
- **Kết quả mong đợi:** prototype, so sánh thuật toán, phân tích trade-off correctness–performance, đánh giá scaling, bằng chứng bảo vệ backend và dữ liệu về hành vi khi Redis lỗi.

Proposal minh họa limiter gắn với API instances; Roadmap minh họa một lớp traffic control phía trước. Vị trí limiter chưa phải quyết định triển khai.
