# Project 3 Proposal — ghi chú cho repo

[Bản đầy đủ trên Google Drive](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) · Đề cương chính thức; Roadmap được ưu tiên nếu có khác biệt

## Đề tài và bài toán

**Nghiên cứu và xây dựng cơ chế kiểm soát lưu lượng phân tán cho hệ thống API nhiều instance.** Khi backend mở rộng ra nhiều instance, limiter dùng state cục bộ có thể áp quota khác nhau tại mỗi instance. Traffic tăng đột biến còn có thể làm CPU, memory, database và response time xấu đi. Giải pháp đề xuất là prototype có load balancer, API instances, rate limiter và Redis shared state.

## Câu hỏi nghiên cứu

1. Thuật toán rate limiting ảnh hưởng thế nào đến latency, throughput và burst traffic?
2. Distributed shared state ảnh hưởng thế nào đến correctness và performance?
3. Hệ thống thay đổi thế nào khi tăng số lượng API instance?
4. Atomic operation như Redis Lua Script có cải thiện correctness khi có concurrent requests không?

## Phạm vi và kết quả

- **Bắt buộc theo Proposal:** API instances, Redis shared state, rate limiter, Fixed Window, Token Bucket, load testing và performance evaluation.
- **Mở rộng theo Proposal:** Sliding Window, Redis Lua Script và monitoring. Roadmap lại đặt atomic operation với Lua Script trong trọng tâm nghiên cứu; giữ nghiên cứu atomicity trong phạm vi và làm rõ cơ chế khi lập kế hoạch.
- **Đánh giá:** allow/reject correctness và overshoot; p50/p95/p99 latency; requests/giây; Redis CPU/memory và network overhead.
- **Kết quả mong đợi:** prototype, so sánh thuật toán, phân tích trade-off correctness–performance và đánh giá scaling.

Proposal minh họa limiter gắn với API instances; Roadmap minh họa một lớp traffic control phía trước. Vị trí limiter chưa phải quyết định triển khai.
