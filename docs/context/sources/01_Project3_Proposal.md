# Project 3 Proposal — ghi chú nguồn cho repo

[Bản Google Doc proposal](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) · Roadmap được ưu tiên nếu có khác biệt. Bản repo đầy đủ để trao đổi nằm tại [PROPOSAL.md](../../PROPOSAL.md); đây là ghi chú tóm lược, không phải xác nhận của giảng viên. Các quyết định triển khai hiện tại không tạo thêm yêu cầu nguồn hay hàm ý được giảng viên phê duyệt.

## Bài toán và yêu cầu

Đề tài dùng kịch bản giả định ứng dụng bán hàng có nhiều API instance sau load balancer. Pain point doanh nghiệp là khách hợp lệ phải cạnh tranh với traffic bất thường, có thể gặp request chậm/thất bại và nguy cơ giao dịch gián đoạn. Tác động kinh doanh chưa được xác minh: testbed chỉ đo proxy ở mức request/backend, không đo giao dịch hay doanh thu. Về kỹ thuật, local counters có thể khiến một client vượt quota chung; cập nhật Redis đồng thời không atomic có thể gây race.

Prototype cần quyết định quota trước backend, so sánh Fixed Window/Token Bucket, local/Redis shared state và scaling từ một lên nhiều API instance. Phạm vi bắt buộc gồm tải normal, burst, concurrent và mixed legitimate/abusive, kiểm tra atomic quota bằng test race có kiểm soát, cùng Redis outage ngắn để đo fail-open/fail-closed. Không mở rộng thành gateway, production HA/cloud/Kubernetes, service mesh hay auth platform.

## Câu hỏi nghiên cứu

- **RQ1:** FW và TB ảnh hưởng latency, throughput và burst behavior thế nào?
- **RQ2:** Redis shared state ảnh hưởng correctness và performance thế nào so với local state?
- **RQ3:** Kết quả thay đổi thế nào khi tăng số API instance?
- **RQ4:** Redis Lua Script atomicity ảnh hưởng correctness dưới concurrent requests thế nào so với forced-race non-atomic control?
- **RQ5:** Mixed traffic và Redis outage thay đổi goodput/latency của client hợp lệ, quota correctness và availability/recovery ra sao?

## Giải pháp và đánh giá

Topology thực nghiệm: client → load balancer → API middleware limiter → backend mô phỏng có giới hạn concurrency. Redis là nhánh shared state, không phải đích request. `X-Client-ID` do generator tin cậy cung cấp, không phải xác thực. FW/TB cùng tốc độ dài hạn mục tiêu nhưng có burst semantics khác nhau. Lua Script được chọn cho quyết định atomic Redis; forced-race non-atomic control chỉ kiểm chứng correctness trong test, không đo HTTP performance.

Đánh giá ghi latency p50/p95/p99 từng lượt (ms), request/giây, goodput (legitimate success / thời gian chạy gồm drain), allow/reject, overshoot, backend arrivals/success/overload, và CPU/memory/network của Redis. RQ5 ghi p95/p99 riêng cho successful legitimate requests; outage availability = legitimate successes / legitimate requests sent trong outage phase. Latency tách success, reject và error; không giả định chỉ tính request có phản hồi. Tổng Redis network traffic không cô lập overhead của limiter. 429 là quota reject; 503 phải phân biệt Redis fail-closed với backend overload. Outage báo first success tách với stable recovery. Backend mô phỏng có thể giới hạn kết luận về scaling.

## Bằng chứng hiện có và phần mở rộng

Baseline T09/T10 hiện có 46 cấu hình × 3 lượt = 138 lượt được chấp nhận. T10 đánh dấu FW correctness **inconclusive**, không phải pass; outage thiếu resource sampling. Xem [T10_RESULTS.md](../../analysis/T10_RESULTS.md), [protocol readiness](../../experiments/PROTOCOL_READINESS.md), [kế hoạch baseline](../../REMAINING_WORK_PLAN.md) và [T06 provenance/giới hạn](../../worklog/2026-10-19-atomicity/README.md). Protocol được khóa; ghi chú này không cấp quyền đo mới.

Sliding Window, Redis Functions so với cơ chế atomic đã chọn và monitoring là tùy chọn. Monitoring Phase 2 là demo/học tập riêng, không đổi nguồn đo T09/T10; [registry Phase 2](../../monitoring/PHASE2_PLAN.md) giữ trạng thái và phạm vi của nó.
