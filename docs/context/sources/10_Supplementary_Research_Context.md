# Supplementary Research Context — ghi chú cho repo

[Bản đầy đủ trên Google Drive](https://docs.google.com/document/d/13-_JUm5HfmGRa9ai6x5_NXxBiQZRQdn89VAX0zVvkI8/edit) · Bổ trợ kỹ thuật và phương pháp thí nghiệm

## Các biến cần so sánh

| Thuật toán | Đặc tính liên quan đến thí nghiệm |
| --- | --- |
| Fixed Window | Đơn giản, ít state; có thể cho burst tại ranh giới hai cửa sổ. |
| Token Bucket | Nạp token theo thời gian, cho phép burst theo sức chứa bucket; cần quản lý state và thời gian nạp. |
| Sliding Window | Giảm ảnh hưởng ranh giới Fixed Window nhưng tốn state/xử lý hơn; chỉ là mở rộng. |

Local state thuận tiện cho một instance nhưng không chia sẻ quota giữa nhiều instance. Redis lưu counter hoặc token bucket state dùng chung. Nhiều request đồng thời có thể cùng đọc state cũ rồi cùng được chấp nhận; cần đánh giá atomic command hoặc Lua Script để tránh race condition.

## Phương pháp được đề xuất trong nguồn

- Môi trường nhỏ có API service, Redis, load balancer và load generator; Docker Compose là một gợi ý, không phải tech stack đã chốt.
- Kịch bản: tải bình thường, burst, concurrent requests và scaling từ một lên nhiều API instances.
- Chỉ số: correctness/overshoot, p50/p95/p99 latency, requests/giây, Redis CPU/memory; có thể xét network overhead, recovery time và mức bảo vệ backend.
- Các mức RPS, concurrency và số instance nêu trong tài liệu gốc chỉ là **ví dụ**, không phải tham số đã phê duyệt.

## Giả thuyết cần kiểm chứng, không phải kết luận

1. Token Bucket xử lý burst khác hoặc tốt hơn Fixed Window theo tiêu chí được chọn.
2. Redis shared state cải thiện correctness của quota toàn hệ thống nhưng có chi phí latency.
3. Atomic operation giảm overshoot dưới concurrent load.
4. Tăng số API instance có thể tăng throughput nhưng tăng chi phí phối hợp state.

Tài liệu này xem Project 3 là nền tảng thí nghiệm về thuật toán, distributed state, concurrency và performance; không phải sản phẩm API Gateway hoàn chỉnh.

## Baseline đánh giá cập nhật

Bản nguồn đã bổ sung workload hỗn hợp để đo goodput/p95/p99 của client hợp lệ, request vào backend, 429, timeout và 5xx; so không limiter, local và Redis shared trên cùng tải và năng lực backend. Một thí nghiệm Redis outage có kiểm soát so fail-open/fail-closed bằng quota violation, availability và recovery. Policy cần được lưu phiên bản theo lượt chạy; raw requests, cấu hình môi trường và các lượt lặp phải truy lại được. Đây là testbed giới hạn, không phải Redis Cluster hay nền tảng HA production.
