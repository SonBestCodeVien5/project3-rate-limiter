# Báo cáo Project 3 — bản nháp phần đã có căn cứ

> Bản nháp nền, chưa phải báo cáo nộp cuối. Các kết quả benchmark chính thức và kết luận RQ1–RQ5 đang để trống có chủ đích; protocol chưa khóa. Cập nhật theo rubric/định dạng do giảng viên cung cấp và theo dữ liệu T10 khi đủ điều kiện.

## 1. Bài toán doanh nghiệp

Xét một doanh nghiệp bán hàng trực tuyến phục vụ người mua qua API trong đợt flash sale. Load balancer phân phối request tới nhiều API instance, phía sau là backend dùng chung. Nhu cầu nghiên cứu là giữ lưu lượng theo từng client trong quota đã định, đồng thời dành năng lực xử lý cho người mua hợp lệ khi có client gửi burst.

Đây là tình huống giả định để nghiên cứu. Dự án không có log sự cố, số liệu doanh thu, hay SLO của một doanh nghiệp cụ thể; vì vậy các tác động dưới đây là rủi ro có thể xảy ra, không phải thiệt hại thực tế đã đo.

## 2. Pain point và tác động

Nếu mỗi API instance tự giữ bộ đếm, request của cùng client có thể được chia qua nhiều instance và tổng quota bị vượt. Chuyển bộ đếm sang Redis tạo trạng thái dùng chung, nhưng thao tác đọc–quyết định–ghi không atomic vẫn có thể cho phép nhiều request đồng thời cùng vượt ngưỡng. Lưu lượng vượt kiểm soát có thể làm API hoặc backend/database chậm và lỗi, ảnh hưởng người mua hợp lệ và tạo rủi ro giao dịch không hoàn tất.

Do đó, chỉ báo số request bị giới hạn chưa đủ để chứng minh lợi ích. Đánh giá cần xem cùng lúc tính đúng quota, lượng request đến backend, khả năng phục vụ client hợp lệ và chi phí độ trễ/tài nguyên.

## 3. Yêu cầu kỹ thuật và phạm vi

### Baseline dự án

- Mô phỏng API nhiều instance sau load balancer với local state và Redis shared state.
- So sánh Fixed Window và Token Bucket; xem correctness khi concurrent requests và khi số API instance thay đổi.
- Dùng workload gồm client hợp lệ và client tạo burst; so không limiter, local limiter và Redis shared limiter trên cùng tải và cùng năng lực backend.
- Thử Redis outage ngắn, có kiểm soát để đánh giá fail-open/fail-closed, quota violation, availability và recovery. Đây không phải kiểm thử production HA.
- Đo allow/reject correctness, overshoot, latency p50/p95/p99, throughput, Redis CPU/memory; với mixed workload thêm goodput và p95/p99 của client hợp lệ, backend arrivals, 429, timeout/5xx. Với outage thêm availability và recovery.

### Lựa chọn kỹ thuật của prototype

Roadmap minh họa một lớp traffic control trước backend; Proposal minh họa limiter gắn với API instance. Prototype hiện đặt limiter middleware ở đầu mỗi API instance, trước backend mô phỏng dùng chung. Đây là quyết định triển khai để khảo sát, không giải quyết khác biệt giữa hai tài liệu nguồn. Local state dùng mutex trong từng tiến trình; Redis mode dùng Lua để gộp quyết định quota thành thao tác atomic. Backend dùng giới hạn concurrency và service time cấu hình để tạo năng lực có thể giữ cố định giữa các lượt. Mã liên quan: [thiết kế và policy](IMPLEMENTATION.md), [limiter](../internal/limiter/limiter.go), [API handler](../internal/server/server.go).

`X-Client-ID` là identity do generator tin cậy cung cấp, không phải xác thực người dùng. Khi quota hết API trả 429; lỗi limiter theo policy trả 503 ở fail-closed hoặc tiếp tục tới backend ở fail-open. Lỗi backend và overload được ghi riêng với reject hợp lệ của limiter.

### Ngoài baseline

Sliding Window, dashboard/quản trị policy, Redis Cluster, gateway hoàn chỉnh, service mesh, Kubernetes/cloud production và hệ thống HA không thuộc phạm vi cần để trả lời câu hỏi hiện tại. Có thể xem xét như hướng phát triển sau khi baseline được đánh giá.

## 4. Giải pháp và mô hình thử nghiệm

Prototype gồm load generator, Nginx round-robin, hai API instance, Redis dùng chung và backend mô phỏng có concurrency giới hạn. Chế độ `none` làm baseline; `local` và `redis` lần lượt biểu diễn state riêng từng API và state chia sẻ. Hai thuật toán có semantics khác nhau: Fixed Window reset quota tại biên cửa sổ; Token Bucket cho burst tối đa theo capacity và refill theo thời gian. Cấu hình pilot mặc định không làm cho hai thuật toán tương đương về burst.

Phép đo dự kiến bao gồm normal, burst, concurrent, topology một/nhiều instance, mixed legitimate/abusive traffic và outage Redis. So sánh cần giữ cùng workload, policy phù hợp với câu hỏi, backend và môi trường trong từng cặp; lưu revision, cấu hình, runtime images và artifacts để truy nguyên. Chi tiết phép đo cần hoàn tất và khóa trước benchmark chính thức theo [protocol readiness](experiments/PROTOCOL_READINESS.md) và [hướng dẫn báo cáo số liệu](experiments/REPORTING.md).

Phân biệt các nhóm số đo khi viết kết quả:

- **Correctness:** allow/reject so với oracle; violations/overshoot. `Inconclusive` do trace hoặc cửa sổ không đủ không phải là pass.
- **Hiệu năng:** throughput và latency; p95/p99 được tính theo từng lượt rồi tóm tắt giữa các lượt, không gộp mẫu để tạo percentile chung.
- **Bảo vệ backend và client hợp lệ:** backend arrivals/overload, legitimate goodput và latency của client hợp lệ. 429 là reject quota; 5xx có thể gồm overload hoặc fail-closed; timeout/transport error có thể không xác định backend đã nhận request hay chưa.
- **Redis outage:** availability của client hợp lệ, quota violation và recovery theo định nghĩa/cửa sổ đã chốt trước lượt đo. Fail-open có thể chấp nhận request khi không xác minh được quota; đó là trade-off policy, không tự nó chứng minh race condition.
- **Chất lượng lượt đo:** offered/sent/completed, drops, limiter errors, clock discontinuity và tính khớp giữa trace, summary, metrics và cấu hình. Lượt lỗi/không hợp lệ phải được giữ cùng lý do, không chọn riêng lượt thuận lợi.

## 5. Tình trạng evidence và đánh giá hiện tại

Prototype và pilot tooling đã tồn tại, nhưng protocol chính thức chưa khóa và chưa có kết luận cuối cho RQ1–RQ5. Gate T01–T03 mới đạt ổn định trong phiên đo hiện tại và chất lượng sáu lượt pilot normal/mixed; độ chính xác UTC tuyệt đối và độ bền sau resume/restart chưa xác minh. Các lượt pilot cũ gồm calibration dừng vì discontinuity đồng hồ và ma trận 84 cấu hình có mismatch oracle, kết quả inconclusive, limiter errors hoặc generator drops; chúng không thay benchmark chính thức. T04 đang hiệu chỉnh; T05/T07 và các bước sau còn chờ. Evidence hiện có cho T06 là phép kiểm tra Redis thật: với quota gần cạn, đúng hai đơn vị còn lại được chấp nhận trong cả Fixed Window và Token Bucket. Non-atomic control chủ động đồng bộ 16 readers để buộc lost update, tạo overshoot 15 khi quota là 1; đây là minh họa race có điều kiện, không đo tần suất tự nhiên. T06 không đo HTTP performance hay Redis throughput. Xem [T01–T03 gate](worklog/2026-10-19-measurement-gate/README.md), [T06 atomicity](worklog/2026-10-19-atomicity/README.md), [readiness](experiments/PROTOCOL_READINESS.md), [checkpoint](context/SESSION_CHECKPOINT.md) và các [pilot cũ](worklog/2026-10-13-calibration/README.md).

**Kết quả chính thức:** `[Chưa có — điền sau T09/T10, kèm bảng/hình, run IDs, revision, manifest và giới hạn tương ứng.]`

**Trả lời RQ1–RQ5:** `[Để trống đến khi có protocol được khóa, dữ liệu hợp lệ và phân tích T10. Không suy câu trả lời từ smoke test hoặc pilot.]`

**Hạn chế cần bàn luận:** gate clock mới chỉ chứng minh ổn định trong phiên quan sát, chưa xác minh UTC tuyệt đối hoặc restart/resume. Các Fixed Window oracle ở gate T03 là inconclusive do chỉ quan sát cửa sổ một phần. Kiểm tra atomicity ép race bằng barrier nên không ước lượng tần suất race trong tải tự nhiên. Backend là mô phỏng; phép đo cùng host có thể chịu ảnh hưởng từ scheduler, generator, logging và tài nguyên dùng chung. Không ngoại suy kết quả sang doanh thu, production readiness hay hệ thống phân tán lớn hơn.

## 6. Kết luận tạm thời và hướng phát triển

Ở trạng thái hiện tại, dự án đã có prototype để khảo sát state cục bộ/chia sẻ, hai thuật toán quota, atomic decision với Redis Lua, mixed workload và hai chính sách khi Redis lỗi. Evidence hiện tại chứng minh có công cụ và các hành vi pilot cụ thể, nhưng chưa hỗ trợ kết luận cuối về thuật toán/mode nào tốt hơn hoặc mức cải thiện bao nhiêu.

Sau khi môi trường clock đạt gate và protocol được khóa, phần tiếp theo là chạy đủ các lượt đã định, phân tích theo từng câu hỏi nghiên cứu, rồi cập nhật kết luận và hình/bảng có thể truy ngược về artifacts. Hướng mở rộng như Sliding Window, dashboard hoặc nền tảng traffic control rộng hơn chỉ nên cân nhắc sau khi hoàn thành baseline và theo yêu cầu của giảng viên.

## 7. Việc còn lại cho bản nộp

- Hoàn thành T10: bảng/hình cho RQ1–RQ5, biến thiên giữa lượt, attribution lỗi và liên kết tới run/cell/revision; không thay kết quả thiếu bằng số 0 hoặc gộp percentile sai.
- Bổ sung chương kết quả/kết luận sau T10; hiện không điền phát hiện hay effect size.
- Đối chiếu yêu cầu hình thức và rubric khi được cung cấp; xác nhận ngày nộp/bảo vệ. H01 phần tự kiểm tra kiến thức vẫn do người học hoàn tất.
- Bổ sung tài liệu tham khảo có thật, trích dẫn chính xác và rà soát cùng slide/demo khi bộ kết quả cuối đã thống nhất.

## Tài liệu tham khảo

Các khái niệm rate limiting và lý do chọn các biến đo cần gắn với nguồn học thuật sau khi người viết đã đọc và xác định đúng ấn phẩm. Tài liệu Redis dưới đây chỉ hỗ trợ các tuyên bố triển khai về atomic scripting và thời gian server; không thay thế nguồn học thuật hoặc kết quả thí nghiệm.

1. Redis, “Scripting with Lua.” Tài liệu chính thức mô tả việc thực thi script là atomic và blocking trên Redis. Dùng để dẫn giải lựa chọn gộp quyết định quota vào một script; không phải bằng chứng thực nghiệm của dự án. https://redis.io/docs/latest/develop/programmability/eval-intro/
2. Redis, “TIME.” Đặc tả chính thức về timestamp giây và microsecond do Redis trả về; dùng cho mô tả nguồn thời gian shared-state. https://redis.io/docs/latest/commands/time/

Danh mục này còn sơ bộ; bổ sung nguồn thuật toán/queueing chỉ khi phần tổng quan thực sự dùng các khẳng định cần trích dẫn, và hoàn thiện định dạng theo rubric khi được cung cấp.
