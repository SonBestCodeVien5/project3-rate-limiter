# ĐỀ CƯƠNG ĐỀ TÀI PROJECT 3

**Nghiên cứu và xây dựng cơ chế kiểm soát lưu lượng phân tán cho hệ thống API nhiều instance**

Sinh viên: ........................................................

MSSV: ........................................................

Lớp: ........................................................

Giảng viên hướng dẫn: ........................................................

> Đây là bản đề cương chi tiết để tra cứu kỹ thuật trong repo. [Bản Drive gửi giảng viên](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) được rút gọn theo cùng phạm vi, không phải bản sao nguyên văn. Thông tin cá nhân ở bản repo để người dùng tự điền. Các quyết định kỹ thuật là lựa chọn triển khai hiện tại; ngày chính thức, rubric và phê duyệt vẫn chờ xác nhận.

## 1. Bối cảnh doanh nghiệp

Đề tài xét tình huống giả định của một doanh nghiệp bán hàng trực tuyến, cung cấp chức năng cho khách hàng qua API. Khi có chiến dịch quảng cáo hoặc flash sale, nhiều khách hàng cùng truy cập trong thời gian ngắn. Bên cạnh nhu cầu sử dụng hợp lệ, một số client có thể gửi request với tần suất quá lớn do tự động hóa, cấu hình sai hoặc hành vi lạm dụng. Các nguồn traffic này cùng sử dụng năng lực xử lý có giới hạn của backend.

## 2. Vấn đề doanh nghiệp gặp phải

Khó khăn của doanh nghiệp là duy trì khả năng phục vụ khách hàng hợp lệ trong khi kiểm soát mức tài nguyên mà mỗi client được sử dụng. Nếu tiếp nhận mọi request, một số nguồn gửi quá nhiều có thể chiếm phần lớn năng lực xử lý, làm tăng độ trễ hoặc khiến request khác thất bại. Hệ quả có thể là trải nghiệm sử dụng bị gián đoạn, tăng công sức xử lý sự cố và nguy cơ mất giao dịch. Đây là tác động giả định để đặt bài toán; đề tài không có số liệu doanh thu hoặc sự cố của một doanh nghiệp cụ thể.

Khi hệ thống có nhiều API instance sau load balancer, request của cùng một client có thể đến các instance khác nhau. Load balancer phân phối request nhưng không tự tạo ra quota chung. Nếu mỗi instance tự đếm độc lập, client có thể được nhận tổng số request cao hơn mức doanh nghiệp muốn cho phép. Hơn nữa, tăng số API instance chưa chắc tăng được năng lực của backend dùng chung.

Vì vậy, nhu cầu cần khảo sát là một cơ chế kiểm soát lưu lượng trước backend, áp dụng quota nhất quán theo client trên nhiều instance. Cơ chế này phù hợp khi doanh nghiệp có chính sách giới hạn sử dụng API, có nhiều nơi tiếp nhận request và có nguy cơ traffic tăng vượt khả năng phục vụ. Giá trị kỳ vọng là hạn chế phần tải vượt policy, giảm áp lực lên backend và duy trì cơ hội phục vụ client hợp lệ; mức cải thiện phải được kiểm chứng thay vì mặc định có lợi.

## 3. Nhu cầu của doanh nghiệp

Mục tiêu nghiệp vụ là kiểm soát việc sử dụng API theo policy đã định và đánh giá khả năng phục vụ client hợp lệ khi có tải bất thường. Ba bên liên quan là người dùng/client hợp lệ, doanh nghiệp cung cấp dịch vụ và đội phát triển/vận hành cần hiểu hành vi hệ thống khi quá tải hoặc có lỗi.

Từ bài toán đó, đề tài xác định các yêu cầu cần khảo sát:

- Áp dụng quota theo client trước khi request được xử lý tại backend; phản hồi rõ khi request vượt quota để client có thể điều chỉnh cách gửi.
- Giữ quota chung nhất quán khi request đi qua nhiều API instance, kể cả khi nhiều request của cùng client đến đồng thời.
- Phân biệt request bị từ chối đúng policy với request thất bại do lỗi hệ thống; đánh giá cả khả năng phục vụ client hợp lệ và mức tải thực sự tới backend.
- Xác định hành vi khi không truy cập được trạng thái quota chung, đồng thời đo chi phí độ trễ và tài nguyên của cơ chế kiểm soát.

Đề tài xây dựng prototype để đánh giá các đánh đổi giữa tính đúng của quota, hiệu năng và khả năng phục vụ. Các ngưỡng quota trong prototype là tham số thí nghiệm; chính sách triển khai thực tế cần được xác nhận theo nhu cầu và năng lực hệ thống của doanh nghiệp. Các yêu cầu này được cụ thể hóa thành các câu hỏi nghiên cứu tại mục 5.

## 4. Giải pháp đề xuất

Rate limiter là cơ chế kiểm tra request theo giới hạn sử dụng đã cấu hình, chẳng hạn số request một client được gửi trong một khoảng thời gian. Request còn trong quota được chuyển tiếp; request vượt quota bị từ chối chủ động trước backend. Tính phân tán ở đây là việc kiểm tra được thực hiện tại nhiều API instance nhưng cùng tuân thủ một quota chung, thay vì mỗi instance cấp thêm một phần quota độc lập.

Trong prototype, luồng xử lý là client → load balancer → API instance có rate limiter → backend mô phỏng giới hạn concurrency. Redis là lựa chọn lưu trạng thái quota dùng chung; local state là đối chứng để đánh giá khác biệt khi các instance không chia sẻ trạng thái. Fixed Window (FW) và Token Bucket (TB) là hai thuật toán được so sánh. Quyết định kiểm tra và cập nhật quota cần được thực hiện như một thao tác atomic để tránh nhiều request đồng thời cùng sử dụng phần quota còn lại. Đây là lựa chọn triển khai để đáp ứng yêu cầu, không phải yêu cầu doanh nghiệp bắt buộc phải dùng Redis hay một thuật toán cụ thể.

Phạm vi thực nghiệm gồm tải bình thường, burst, concurrent và tải hỗn hợp giữa client hợp lệ với client tạo tải bất thường. So sánh không limiter, local và Redis trên cùng workload/backend; kiểm tra atomicity với Redis thật và đối chứng non-atomic tạo race có kiểm soát. Một Redis outage ngắn được dùng để so sánh fail-open (tiếp tục cho request đi qua) và fail-closed (từ chối khi không kiểm tra được quota), làm rõ đánh đổi giữa khả năng phục vụ và quota enforcement.

Client trong testbed được nhận diện bằng `X-Client-ID` do load generator tin cậy cung cấp; đây không phải xác thực người dùng. Rate limiter không tự nhận diện bot hoặc bảo đảm mọi request hợp lệ đều thành công: kết quả còn phụ thuộc định danh, policy và năng lực backend. Prototype tập trung vào cơ chế giới hạn lưu lượng và đánh giá bằng số đo; không xây dựng API Gateway hoàn chỉnh, service mesh, nền tảng xác thực, hệ thống HA production, Kubernetes/cloud production hoặc dịch vụ không liên quan. Sliding Window và monitoring là phần mở rộng tùy thời gian.

FW và TB được cấu hình cùng tốc độ dài hạn mục tiêu nhưng có burst semantics khác nhau. Lua Script là lựa chọn triển khai atomic trên Redis; đối chứng non-atomic chỉ phục vụ test có barrier, không dùng đo HTTP performance.

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

## 9. Kết quả mong đợi và tiến độ

Sản phẩm là prototype và đánh giá có thể tái lập về trade-off giữa correctness, latency, throughput, tài nguyên và khả năng phục vụ client hợp lệ dưới các workload đã định. Mục tiêu là trả lời câu hỏi nghiên cứu bằng số đo và giới hạn rõ ràng, không phải chứng minh trước rằng một thuật toán hoặc mode luôn tốt hơn.

**Tiến độ ghi nhận ngày 25/10/2026:** Baseline đo T09 và phân tích offline T10 đã hoàn tất: 46 cấu hình, 3 lượt mỗi cấu hình, 138 lượt được chấp nhận theo protocol. T10 ghi Fixed Window correctness là **inconclusive** do chưa đủ độ phủ cửa sổ; đây không phải correctness pass. Redis network counters là tổng traffic quan sát được, outage run thiếu resource sampling, và kết quả scaling bị giới hạn bởi backend mô phỏng. T06 có kiểm tra atomicity riêng với Redis thật và đối chứng non-atomic có barrier; giới hạn và provenance được nêu trong hồ sơ T06.

**Kết quả dự kiến:** Hồ sơ cuối cùng sẽ tổng hợp câu trả lời cho RQ1–RQ5 từ evidence phù hợp, giữ riêng số đo formal, kiểm tra correctness và giới hạn của từng phép đo. Không giả định trước kết quả sẽ xác nhận thuật toán hay mode nào tốt hơn.

Chi tiết số liệu, nguồn và giới hạn được duy trì trong [phân tích kết quả T10](analysis/T10_RESULTS.md), [protocol đo](experiments/PROTOCOL_READINESS.md), [hồ sơ T06](worklog/2026-10-19-atomicity/README.md) và [kế hoạch phần việc baseline](REMAINING_WORK_PLAN.md).

## 10. Hướng phát triển thành Đồ án tốt nghiệp

Nếu được chọn làm hướng tương lai riêng, đề tài có thể mở rộng sang API Gateway/Traffic Management Platform, adaptive rate limiting, circuit breaker, load shedding, retry control, multi-dimensional quota hoặc traffic control dựa trên observability. Đây không thuộc phạm vi Project 3.

## 11. Lý do lựa chọn đề tài

Khi backend chuyển sang nhiều instance, kiểm soát quota và bảo vệ backend cần phối hợp qua ranh giới instance, đồng thời phải cân nhắc correctness, độ trễ và khả năng phục vụ người dùng hợp lệ. Distributed rate limiting là một bài toán kỹ thuật cụ thể để khảo sát các trade-off đó bằng prototype và testbed có kiểm soát. Kết quả có thể làm nền tảng học tập cho hướng nghiên cứu traffic management rộng hơn, nhưng không khẳng định sẵn khả năng áp dụng production.

## 12. Kế hoạch công việc và sản phẩm bàn giao

Các mốc dưới đây là trình tự tương đối theo phụ thuộc công việc, không phải ngày chính thức. Baseline T09/T10 và kiểm tra T06 đã có evidence; phần còn lại tập trung hoàn thiện hồ sơ, tiếp nhận yêu cầu hình thức và đồng bộ sản phẩm trình bày. Mọi lượt đo mới (nếu cần) chỉ thực hiện sau khi phạm vi và kế hoạch thí nghiệm được thống nhất riêng.

- **Mốc 1 — Hoàn thiện báo cáo:** đối chiếu yêu cầu trình bày/rubric và phản hồi giảng viên khi được cung cấp; hoàn thiện phần phương pháp, kết quả RQ1–RQ5, giới hạn và trích dẫn, truy nguyên số liệu về protocol, revision và artifacts. Giữ rõ các kết quả inconclusive và những phân tích chưa thực hiện.
- **Mốc 2 — Rà soát nguồn và lập luận:** đọc các phần nguồn được dẫn trong cơ sở lý thuyết, giải thích liên hệ với thiết kế Project 3 và xác nhận hiểu biết; hoàn thiện định dạng tài liệu tham khảo theo yêu cầu nộp.
- **Mốc 3 — Hoàn thiện slide và demo:** rút gọn câu chuyện từ vấn đề doanh nghiệp đến yêu cầu kỹ thuật, giải pháp, thí nghiệm và đánh giá; chọn các evidence đại diện đã có, chuẩn bị demo giới hạn theo kịch bản và kiểm tra liên kết giữa slide, báo cáo và artifacts.
- **Mốc 4 — Rà soát trước khi nộp/trình bày:** kiểm tra nhất quán thuật ngữ, số liệu, giới hạn và sản phẩm; cập nhật theo phản hồi giảng viên và xác nhận lịch chính thức khi có thông tin.

**Sản phẩm bàn giao dự kiến:**

- Báo cáo Project 3 có tài liệu tham khảo và traceability.
- Mã nguồn prototype, cấu hình thí nghiệm và hướng dẫn tái lập.
- Bộ evidence đo lường và phân tích gắn với protocol, revision, run/cell và artifacts.
- Slide trình bày.
- Demo prototype theo kịch bản giới hạn.

Quy cách cuối cùng của báo cáo, slide và demo sẽ theo yêu cầu chính thức nếu được cung cấp.

## 13. Cơ sở lý thuyết và tài liệu tham khảo

Token Bucket mô hình hóa việc tích lũy quyền gửi theo thời gian và cho phép burst trong giới hạn bucket; RFC 3290 phụ lục A.2 cung cấp nền tảng thuật ngữ cho mô hình này [1]. Nghiên cứu về distributed rate limiting đặt ra trade-off giữa phối hợp trạng thái toàn cục, độ chính xác, chi phí trao đổi thông tin và khả năng mở rộng [2]. Project 3 khảo sát một trường hợp hẹp hơn là quota request dùng Redis shared state trên testbed, không tái triển khai thuật toán điều phối băng thông của công trình đó. Công trình về tail latency giải thích vì sao cần quan sát p95/p99 bên cạnh throughput; nó không dự đoán rằng limiter sẽ cải thiện các số đo này [3]. Redis Lua scripting cung cấp primitive thực thi atomic và blocking cho thao tác quota [4]; semantics đó là căn cứ triển khai, còn correctness và hiệu năng của prototype cần evidence riêng.

Các nguồn này hỗ trợ cách đặt câu hỏi và lựa chọn thiết kế; chúng không thay thế kết quả thực nghiệm Project 3. Định dạng danh mục có thể được điều chỉnh theo yêu cầu nộp chính thức.

1. Yoram Bernet, Steven Blake, Daniel Grossman và Andrew Smith. *An Informal Management Model for Diffserv Routers*. RFC 3290, Informational, tháng 5/2002, phụ lục A.2. [Bản RFC](https://www.rfc-editor.org/rfc/rfc3290.html#appendix-A.2).
2. Barath Raghavan, Kashi Vishwanath, Sriram Ramabhadran, Kenneth Yocum và Alex C. Snoeren. *Cloud Control with Distributed Rate Limiting*. ACM SIGCOMM, 2007, mục 1–3. [Bản tác giả](https://cseweb.ucsd.edu/~kvishwanath/papers/fp076-raghavan.pdf).
3. Jeffrey Dean và Luiz André Barroso. *The Tail at Scale*. Communications of the ACM, 56(2), 2013, tr. 74–80; phần được viện dẫn: tr. 74–76. DOI: `10.1145/2408776.2408794`. [Bản tác giả](https://www.barroso.org/publications/TheTailAtScale.pdf).
4. Redis. *Scripting with Lua*. Tài liệu chính thức, phần mở đầu về atomic/blocking execution. [Tài liệu](https://redis.io/docs/latest/develop/programmability/eval-intro/).
