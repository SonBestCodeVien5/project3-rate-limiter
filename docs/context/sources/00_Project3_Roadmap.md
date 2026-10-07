# Project 3 Roadmap — ghi chú cho repo

[Bản đầy đủ trên Google Drive](https://docs.google.com/document/d/1oVNMU3KTJ-dWL-3GRDb5tc9JJ75uzxaDmPf0P2yjeWA/edit) · Nguồn ưu tiên cao nhất

## Định hướng

Project 2 xây dựng một ứng dụng nghiệp vụ hoàn chỉnh (Gym Management System). Project 3 chuyển sang nghiên cứu khả năng mở rộng, độ ổn định và hiệu năng của backend. Đồ án tốt nghiệp sau này **có thể** mở rộng thành nền tảng quản lý traffic lớn hơn.

Bài toán bắt đầu từ traffic API không ổn định hoặc tăng đột biến, gây quá tải tài nguyên, tăng độ trễ và lỗi dịch vụ. Nhu cầu kỹ thuật là kiểm soát request theo user/API key/IP trước backend, hoạt động trên nhiều API instance, chia sẻ trạng thái, giữ quota chính xác và hạn chế bottleneck.

## Phạm vi Project 3

- **Chủ đề:** nghiên cứu và xây dựng cơ chế kiểm soát lưu lượng phân tán cho hệ thống API nhiều instance.
- **Kiến trúc định hướng:** client → load balancer → lớp traffic control/rate limiter → backend API instances. Sơ đồ có nhắc API Gateway và database để đặt ngữ cảnh; Project 3 tập trung vào **distributed rate limiter**, không xây dựng toàn bộ gateway.
- **Thành phần triển khai:** API instances, load balancer, Redis shared state, rate limiter.
- **So sánh nghiên cứu:** Fixed Window và Token Bucket; local state và Redis shared state; một và nhiều API instance; atomic operation với Lua Script. Sliding Window là mở rộng.
- **Thí nghiệm:** traffic bình thường, burst và concurrent requests. Đo correctness, p50/p95/p99 latency, requests/giây, overshoot và Redis CPU/memory.

## Ranh giới

Không triển khai API Gateway platform hoàn chỉnh, service mesh, Kubernetes production hoặc full cloud infrastructure trong Project 3. Adaptive rate limiting, circuit breaker, load shedding, retry control, multi-dimensional quota và observability-driven traffic control thuộc hướng mở rộng cho đồ án tốt nghiệp.

Tài liệu và báo cáo cần đi theo mạch: vấn đề doanh nghiệp → pain point → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → phát triển tương lai.
