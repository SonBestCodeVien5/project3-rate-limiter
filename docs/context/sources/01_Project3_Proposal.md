# Project 3 Proposal — ghi chú nguồn cho repo

[Bản Google Doc proposal](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) · Roadmap được ưu tiên nếu có khác biệt. Bản Drive được rút gọn để gửi giảng viên; [PROPOSAL.md](../../PROPOSAL.md) giữ bản chi tiết kỹ thuật cùng phạm vi, không phải bản sao nguyên văn. Đây là ghi chú tóm lược, không phải xác nhận của giảng viên. Các quyết định triển khai hiện tại không tạo thêm yêu cầu nguồn hay hàm ý được giảng viên phê duyệt.

## Bài toán và yêu cầu

Đề tài dùng kịch bản giả định ứng dụng bán hàng có nhiều API instance sau load balancer. Pain point doanh nghiệp là khách hợp lệ phải cạnh tranh với traffic bất thường, có thể gặp request chậm/thất bại và nguy cơ giao dịch gián đoạn. Tác động kinh doanh chưa được xác minh: testbed chỉ đo proxy ở mức request/backend, không đo giao dịch hay doanh thu. Về kỹ thuật, local counters có thể khiến một client vượt quota chung; cập nhật Redis đồng thời không atomic có thể gây race.

Prototype cần quyết định quota trước backend, so sánh Fixed Window/Token Bucket, local/Redis shared state và scaling từ một lên nhiều API instance. Phạm vi bắt buộc gồm tải normal, burst, concurrent và mixed legitimate/abusive, kiểm tra atomic quota bằng test race có kiểm soát, cùng Redis outage ngắn để đo fail-open/fail-closed. Không mở rộng thành gateway, production HA/cloud/Kubernetes, service mesh hay auth platform.

## Làm rõ nhu cầu ban đầu theo góp ý giảng viên

Ngày 26/10/2026, người dùng yêu cầu đào sâu mục 1–3 của bản Drive theo hướng tài liệu xác định nhu cầu ban đầu trong SDLC, vẫn giữ dạng proposal gửi giảng viên. Bản cập nhật làm rõ các bên liên quan, tình huống doanh nghiệp cần kiểm soát API, việc chia tải không tự tạo quota chung và giá trị kỳ vọng cần kiểm chứng. Tác động kinh doanh vẫn là giả định, chưa phải kết quả doanh nghiệp thực tế.

Các yêu cầu tập trung vào quota theo client trước backend, quota chung khi nhiều instance/request đồng thời, phản hồi phân biệt policy reject với lỗi, hành vi khi shared state gián đoạn và chi phí hiệu năng/tài nguyên. Ngưỡng quota của prototype là tham số thí nghiệm; policy triển khai thực tế cần xác nhận theo nhu cầu và năng lực hệ thống. Redis, FW/TB và Lua là lựa chọn triển khai, không phải công nghệ doanh nghiệp bắt buộc phải dùng.

Rate limiter không tự nhận diện bot hoặc bảo đảm mọi request hợp lệ thành công. Bản Drive giữ đủ năm RQ và các so sánh none/local/Redis, concurrency, mixed backend protection và bounded outage; phần đánh giá, sản phẩm, kế hoạch và nguồn tham khảo không đổi. Các làm rõ này không mở thêm phạm vi đo hay thay đổi kết quả baseline.

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

Thông tin evidence repo (không liệt kê chi tiết trong bản Drive rút gọn): baseline T09/T10 hiện có 46 cấu hình × 3 lượt = 138 lượt được chấp nhận. T10 đánh dấu FW correctness **inconclusive**, không phải pass; outage thiếu resource sampling. Xem [T10_RESULTS.md](../../analysis/T10_RESULTS.md), [protocol readiness](../../experiments/PROTOCOL_READINESS.md), [kế hoạch baseline](../../REMAINING_WORK_PLAN.md) và [T06 provenance/giới hạn](../../worklog/2026-10-19-atomicity/README.md). Protocol được khóa; ghi chú này không cấp quyền đo mới.

Sliding Window, Redis Functions so với cơ chế atomic đã chọn và monitoring là tùy chọn. Monitoring Phase 2 là demo/học tập riêng, không đổi nguồn đo T09/T10; [registry Phase 2](../../monitoring/PHASE2_PLAN.md) giữ trạng thái và phạm vi của nó.

## Kế hoạch hoàn thiện và sản phẩm bàn giao

Bản chi tiết cập nhật ngày 25/10/2026 tách kết quả mong đợi khỏi tiến độ T09/T10 đã ghi nhận. Theo yêu cầu người dùng, bản Drive gửi giảng viên rút gọn còn bảy mục, bỏ mã task và chi tiết vận hành; giữ nguyên câu hỏi, phạm vi nghiên cứu, cách đánh giá và các giới hạn FW/scaling. Các mốc còn lại là hoàn thiện báo cáo, rà soát nguồn/lập luận, hoàn thiện slide/demo và rà soát trước nộp; trình tự tương đối, ngày chính thức và rubric vẫn chờ xác nhận. Mọi lượt đo mới cần phạm vi và kế hoạch riêng được thống nhất.

Sản phẩm dự kiến gồm báo cáo, mã nguồn/cấu hình/hướng dẫn tái lập, evidence đo và phân tích, slide, demo. Phần lý thuyết dẫn RFC 3290 A.2, Raghavan và cộng sự (SIGCOMM 2007), Dean/Barroso (CACM 2013) và tài liệu Redis Lua; nguồn giải thích thiết kế, không thay evidence của dự án. Các bổ sung không đổi phạm vi nghiên cứu, kết quả hoặc giới hạn đã ghi nhận.
