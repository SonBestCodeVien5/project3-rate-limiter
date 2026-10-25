# ĐỀ CƯƠNG ĐỀ TÀI PROJECT 3

**Nghiên cứu và xây dựng cơ chế kiểm soát lưu lượng phân tán cho hệ thống API nhiều instance**

Sinh viên: ........................................................

MSSV: ........................................................

Lớp: ........................................................

Giảng viên hướng dẫn: ........................................................

> Bản dự thảo để trao đổi với giảng viên; không phải rubric, lịch chính thức hay xác nhận phê duyệt. Đề tài và các trường cá nhân được giữ theo bản nguồn: [Google Doc proposal](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit). Các quyết định kỹ thuật mô tả dưới đây là lựa chọn triển khai hiện tại, không phải yêu cầu bổ sung hay phê duyệt của giảng viên.

## 1. Bối cảnh doanh nghiệp

Nhiều doanh nghiệp cung cấp dịch vụ qua API và mở rộng backend từ một máy chủ sang nhiều instance khi tải tăng. Đề tài dùng tình huống giả định của một ứng dụng bán hàng trực tuyến trong đợt flash sale: người mua hợp lệ và client tạo tải bất thường cùng truy cập API sau load balancer. Đây là kịch bản nghiên cứu, không phải sự cố đã được xác minh tại doanh nghiệp cụ thể.

## 2. Vấn đề doanh nghiệp gặp phải

Traffic có thể tăng đột biến do chiến dịch quảng cáo, ra mắt sản phẩm, client tự động hoặc bot. Nếu mỗi API instance giữ bộ đếm riêng, request của cùng một client có thể được load balancer phân phối qua nhiều instance và vượt quota chung. Cập nhật state đồng thời không atomic cũng có thể tạo race condition. Backend quá tải có thể làm tăng độ trễ, gây lỗi dịch vụ và ảnh hưởng người dùng hợp lệ; mất giao dịch là rủi ro giả định, chưa được đo trong đề tài.

Pain point phía doanh nghiệp là khách hàng hợp lệ phải cạnh tranh với traffic bất thường, từ đó có thể gặp request chậm hoặc thất bại và nguy cơ giao dịch bị gián đoạn. Quota chung và state dùng chung là yêu cầu kỹ thuật để khảo sát cách giảm vấn đề này. Testbed đo proxy ở mức request và backend; đề tài không đo giao dịch mua hàng hay doanh thu, nên tác động kinh doanh vẫn là giả thuyết.

## 3. Nhu cầu của doanh nghiệp

Cơ chế cần quyết định trước xử lý backend, hỗ trợ quota chung theo client trên nhiều API instance, giữ quota đúng khi có request đồng thời, và đo chi phí độ trễ, thông lượng cùng tài nguyên. Thí nghiệm tải hỗn hợp cần quan sát đồng thời client hợp lệ và backend; không giả định trước rằng limiter luôn cải thiện kết quả. Với Redis tạm thời unavailable, prototype phải có hành vi fail-open hoặc fail-closed để đo trade-off về khả năng phục vụ và quota enforcement. Đây là fault injection ngắn, có kiểm soát, không phải yêu cầu chịu lỗi production.

## 4. Giải pháp đề xuất

Xây dựng prototype rate limiter gắn trong middleware của API. Topology thí nghiệm là **client → load balancer → middleware rate limiter tại API → backend mô phỏng có concurrency giới hạn**. Redis chỉ là nhánh lưu state dùng chung khi chạy chế độ Redis; Redis không phải đích xử lý request. Ở chế độ local, mỗi API instance có state riêng để làm đối chứng. Backend mô phỏng giữ năng lực xử lý có thể kiểm soát khi thay số API instance.

So sánh Fixed Window (FW) và Token Bucket (TB), local state và Redis shared state, một và nhiều API instance. FW và TB được cấu hình cùng tốc độ dài hạn mục tiêu, nhưng có semantics burst khác nhau; không xem chúng là tương đương từng thời điểm. Lua Script là lựa chọn triển khai atomic cho quyết định quota trên Redis. Đối chứng không atomic chỉ dùng test có barrier để tạo race có kiểm soát, không dùng làm phép đo HTTP performance.

`X-Client-ID` là định danh tin cậy do load generator cung cấp trong testbed, không phải xác thực người dùng hay bảo đảm danh tính trong môi trường thật. Phạm vi không bao gồm nền tảng API Gateway hoàn chỉnh, production HA, service mesh, production Kubernetes/cloud, nền tảng authentication hoặc dịch vụ không liên quan.

## 5. Câu hỏi nghiên cứu

- **RQ1:** Các thuật toán rate limiting ảnh hưởng thế nào tới latency, throughput và burst traffic?
- **RQ2:** Distributed shared state ảnh hưởng thế nào tới correctness và performance?
- **RQ3:** Khi tăng số lượng API instance, hệ thống thay đổi thế nào?
- **RQ4:** Atomic operation như Redis Lua Script có cải thiện correctness trong môi trường concurrent request không?
- **RQ5:** Khi có client tạo tải bất thường hoặc Redis tạm thời unavailable, limiter thay đổi khả năng phục vụ client hợp lệ, quota correctness và độ trễ ra sao?

## 6. Kiến trúc hệ thống

Client gửi request qua load balancer đến một API instance. Middleware rate limiter tại API quyết định allow/reject trước khi gọi backend mô phỏng. Với Redis mode, middleware truy cập Redis để đọc và cập nhật state quota dùng chung; với local mode, quyết định dựa trên state tại instance. Backend chỉ nhận request được middleware cho qua và có thể trả overload khi hết concurrency. Sơ đồ API Gateway/traffic control chỉ làm bối cảnh kiến trúc; đề tài không xây dựng gateway riêng.

## 7. Phạm vi Project 3

**Bắt buộc:**

- API instances, Redis shared state và rate limiter với Fixed Window và Token Bucket.
- So sánh local state với Redis shared state, scaling khi tăng từ một lên nhiều API instance, và workload bình thường, burst, concurrent cùng tải hỗn hợp giữa client hợp lệ và client tạo tải bất thường.
- Load testing và performance evaluation; kiểm tra quyết định quota atomic dưới concurrent load bằng test non-atomic có kiểm soát.
- Một Redis outage ngắn, có kiểm soát để so sánh fail-open/fail-closed về availability, quota violation và recovery.

**Mở rộng tùy thời gian:** Sliding Window, so sánh Redis Functions với cơ chế atomic được chọn, và monitoring. Monitoring là phần demo/học tập tùy chọn, tách khỏi nguồn đo T09/T10; xem [phạm vi monitoring Phase 2](monitoring/PHASE2_PLAN.md).

## 8. Đánh giá hệ thống

Thiết kế đánh giá gắn với câu hỏi nghiên cứu:

- **RQ1:** Giữ workload, quota và topology cố định để so sánh FW/TB trong tải bình thường, burst và mixed. Ghi latency p50/p95/p99 theo từng lượt, goodput, request/giây, allow/reject và overshoot; một burst hợp lệ theo TB không tự nó là overshoot của FW.
- **RQ2:** Giữ workload, policy và topology cố định để so local với Redis. Đánh giá correctness và latency/throughput; Redis CPU, memory và network traffic là số đo của tiến trình/container quan sát được. Tổng network traffic Redis có thể gồm workload, healthcheck, sampler và thao tác quản trị, nên không gọi đó là overhead riêng cho mỗi request của limiter.
- **RQ3:** So topology một/nhiều API khi các điều kiện khác giữ nguyên. Backend concurrency và service time được giới hạn để có đối chứng, nhưng backend mô phỏng có thể trở thành bottleneck; kết quả không đại diện cho scaling của dịch vụ production.
- **RQ4:** Kiểm tra invariant quota bằng các test concurrency trên Redis thật và đối chứng non-atomic được barrier buộc đọc cùng state cũ. Kết quả chứng minh hành vi của phép test có kiểm soát, không đo tần suất race tự nhiên hoặc HTTP performance của bản non-atomic. Provenance và giới hạn của T06 được ghi tại [hồ sơ T06](worklog/2026-10-19-atomicity/README.md).
- **RQ5:** Trên cùng tải hỗn hợp, so không limiter, local và Redis; ghi backend arrivals/success/overload, goodput và p95/p99 latency riêng của legitimate requests thành công, cùng các mã 429/5xx, timeout và canceled. 429 là reject quota dự kiến; 503 có thể là Redis fail-closed hoặc backend overload và phải phân biệt theo nguyên nhân. Trong outage phase, availability được tính bằng legitimate successes / legitimate requests sent trong chính phase đó; recovery báo riêng. First success là request hợp lệ đầu tiên thành công, còn stable recovery yêu cầu chuỗi cửa sổ đạt điều kiện ổn định, hai khái niệm không thay thế nhau.

Latency được đo bằng mili giây; kết quả tách success, reject và error. p50/p95/p99 được tính riêng từng lượt rồi mới tổng hợp, không tính trên trace gộp. Throughput được báo theo request/giây; goodput là số request hợp lệ thành công chia cho thời gian lượt chạy gồm drain. Backend arrivals là request tới backend, kể cả success và overload. Các loại reject hợp lệ và lỗi hệ thống được giữ riêng. Báo cáo nêu cấu hình, protocol, revision và artifact liên quan; đây là kết quả testbed chứ không phải cam kết về vận hành thật.

## 9. Kết quả mong đợi

Sản phẩm là prototype và đánh giá có thể tái lập về trade-off giữa correctness, latency, throughput, tài nguyên và khả năng phục vụ client hợp lệ dưới các workload đã định. Mục tiêu là trả lời câu hỏi nghiên cứu bằng số đo và giới hạn rõ ràng, không phải chứng minh trước rằng một thuật toán hoặc mode luôn tốt hơn.

Đã có baseline đo T09 và phân tích offline T10: 46 cấu hình, 3 lượt mỗi cấu hình, 138 lượt được chấp nhận theo protocol. T10 ghi Fixed Window correctness là **inconclusive** do chưa đủ độ phủ cửa sổ; đây không phải correctness pass. Redis network counters là tổng traffic quan sát được, outage run thiếu resource sampling, và kết quả scaling bị giới hạn bởi backend mô phỏng. Chi tiết, nguồn, protocol khóa và giới hạn được duy trì trong [phân tích kết quả T10](analysis/T10_RESULTS.md), [protocol đo](experiments/PROTOCOL_READINESS.md) và [kế hoạch phần việc baseline](REMAINING_WORK_PLAN.md).

## 10. Hướng phát triển thành Đồ án tốt nghiệp

Nếu được chọn làm hướng tương lai riêng, đề tài có thể mở rộng sang API Gateway/Traffic Management Platform, adaptive rate limiting, circuit breaker, load shedding, retry control, multi-dimensional quota hoặc traffic control dựa trên observability. Đây không thuộc phạm vi Project 3.

## 11. Lý do lựa chọn đề tài

Khi backend chuyển sang nhiều instance, kiểm soát quota và bảo vệ backend cần phối hợp qua ranh giới instance, đồng thời phải cân nhắc correctness, độ trễ và khả năng phục vụ người dùng hợp lệ. Distributed rate limiting là một bài toán kỹ thuật cụ thể để khảo sát các trade-off đó bằng prototype và testbed có kiểm soát. Kết quả có thể làm nền tảng học tập cho hướng nghiên cứu traffic management rộng hơn, nhưng không khẳng định sẵn khả năng áp dụng production.
