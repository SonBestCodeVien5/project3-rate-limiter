# Báo cáo Project 3 — bản nháp phần đã có căn cứ

> Bản nháp nền, chưa phải báo cáo nộp cuối. **Tính đến 20/10/2026, T09 đã thu thập đủ dữ liệu (138/138 vị trí chạy dự kiến dùng được; 46/46 cấu hình được tổng hợp), nhưng T10 chưa bắt đầu.** Vì vậy kết quả được thu thập nhưng chưa phân tích; phần kết quả chính thức và kết luận RQ1–RQ5 vẫn để trống có chủ đích. Không chạy thêm tải; dừng trước T10. Cập nhật theo rubric/định dạng do giảng viên cung cấp và sau khi có chỉ dẫn tiếp tục phân tích.

## 1. Bài toán doanh nghiệp

Xét một doanh nghiệp bán hàng trực tuyến phục vụ người mua qua API trong đợt flash sale. Bộ cân bằng tải phân phối yêu cầu tới nhiều tiến trình API, phía sau là backend dùng chung. Nhu cầu nghiên cứu là giữ lưu lượng theo từng client trong hạn mức đã định, đồng thời dành năng lực xử lý cho người mua hợp lệ khi có client tạo tải đột biến.

Đây là tình huống giả định để nghiên cứu. Dự án không có log sự cố, số liệu doanh thu, hay SLO của một doanh nghiệp cụ thể; vì vậy các tác động dưới đây là rủi ro có thể xảy ra, không phải thiệt hại thực tế đã đo.

## 2. Điểm nghẽn và tác động

Nếu mỗi tiến trình API tự giữ bộ đếm, yêu cầu của cùng client có thể được phân phối qua nhiều tiến trình và tổng hạn mức bị vượt. Chuyển bộ đếm sang Redis tạo trạng thái dùng chung, nhưng thao tác đọc–quyết định–ghi nếu không được thực hiện nguyên tử vẫn có thể cho phép nhiều yêu cầu đồng thời vượt ngưỡng. Lưu lượng vượt kiểm soát có thể làm API hoặc backend/database chậm và lỗi, ảnh hưởng người mua hợp lệ và tạo rủi ro giao dịch không hoàn tất.

Do đó, chỉ báo số yêu cầu bị giới hạn chưa đủ để chứng minh lợi ích. Đánh giá cần xem đồng thời tính đúng của hạn mức, lượng yêu cầu tới backend, khả năng phục vụ client hợp lệ và chi phí về độ trễ/tài nguyên.

## 3. Yêu cầu kỹ thuật và phạm vi

### Baseline dự án

- Mô phỏng nhiều tiến trình API sau bộ cân bằng tải với trạng thái cục bộ và trạng thái Redis dùng chung.
- So sánh Fixed Window và Token Bucket; kiểm tra tính đúng khi có yêu cầu đồng thời và khi thay đổi số tiến trình API.
- Dùng mẫu tải gồm client hợp lệ và client tạo tải đột biến; so sánh không giới hạn, giới hạn cục bộ và giới hạn dùng Redis chung trên cùng mức tải và năng lực backend.
- Thử ngắt Redis ngắn, có kiểm soát để đánh giá chính sách cho qua/từ chối, vi phạm hạn mức, khả năng phục vụ và phục hồi. Đây không phải kiểm thử sẵn sàng cao production.
- Đo tính đúng khi cho phép/từ chối, mức vượt hạn mức, độ trễ p50/p95/p99, thông lượng, CPU/bộ nhớ Redis; với mẫu tải hỗn hợp bổ sung goodput của client hợp lệ (số yêu cầu được xử lý thành công mỗi giây), p95/p99 độ trễ của client hợp lệ, số yêu cầu tới backend, 429, timeout/5xx. Với outage bổ sung khả năng phục vụ và phục hồi.

### Lựa chọn kỹ thuật của prototype

Roadmap minh họa một lớp kiểm soát lưu lượng trước backend; Proposal minh họa bộ giới hạn gắn với tiến trình API. Prototype hiện đặt middleware giới hạn ở đầu mỗi tiến trình API, trước backend mô phỏng dùng chung. Đây là lựa chọn triển khai để khảo sát, không nhằm giải quyết khác biệt giữa hai tài liệu nguồn. Trạng thái cục bộ dùng mutex trong từng tiến trình; chế độ Redis dùng Lua để gộp quyết định hạn mức thành một thao tác nguyên tử. Backend dùng giới hạn yêu cầu xử lý đồng thời và thời gian xử lý cấu hình được để giữ năng lực ổn định giữa các lượt. Mã liên quan: [thiết kế và policy](IMPLEMENTATION.md), [limiter](../internal/limiter/limiter.go), [API handler](../internal/server/server.go).

`X-Client-ID` là mã định danh do bộ tạo tải đáng tin cậy cung cấp, không phải xác thực người dùng. Khi hết hạn mức, API trả 429; lỗi bộ giới hạn theo policy trả 503 ở chế độ từ chối khi lỗi hoặc tiếp tục tới backend ở chế độ cho qua khi lỗi. Lỗi backend và quá tải được ghi riêng với lần từ chối hợp lệ của bộ giới hạn.

### Ngoài baseline

Sliding Window, dashboard/quản trị policy, Redis Cluster, gateway hoàn chỉnh, service mesh, Kubernetes/cloud production và hệ thống sẵn sàng cao không thuộc phạm vi cần để trả lời câu hỏi hiện tại. Có thể xem xét như hướng phát triển sau khi baseline được đánh giá.

## 4. Giải pháp và mô hình thử nghiệm

Prototype gồm bộ tạo tải, Nginx phân phối vòng tròn, hai tiến trình API, Redis dùng chung và backend mô phỏng có giới hạn xử lý đồng thời. Chế độ `none` làm baseline; `local` và `redis` lần lượt biểu diễn trạng thái riêng của từng API và trạng thái dùng chung. Hai thuật toán có cách hoạt động khác nhau: Fixed Window đặt lại hạn mức ở ranh giới cửa sổ; Token Bucket cho phép tải đột biến tối đa theo dung lượng bucket và được nạp lại theo thời gian. Cấu hình pilot mặc định không làm cho hai thuật toán có cách xử lý tải đột biến tương đương.

T09 đã thu thập đủ ma trận theo protocol v1.2 đã khóa; lượt bổ sung v1.3 chỉ lấp vị trí chạy còn thiếu duy nhất theo phụ lục đã cho phép. Ma trận gồm các cấu hình normal, burst, hỗn hợp, topology một/nhiều tiến trình API và outage Redis; T10 chưa bắt đầu. Bằng chứng về tính đúng khi có yêu cầu đồng thời đến từ các bài kiểm tra Redis của T06, không phải một nghiên cứu tải HTTP đồng thời riêng. Khi T10 được tiếp tục, việc so sánh cần giữ cùng mẫu tải, policy phù hợp với câu hỏi, backend và môi trường trong từng cặp; lưu revision, cấu hình, runtime images và artifacts để truy nguyên. Tham khảo [protocol readiness](experiments/PROTOCOL_READINESS.md) và [hướng dẫn báo cáo số liệu](experiments/REPORTING.md).

Phân biệt các nhóm số đo khi viết kết quả:

- **Tính đúng:** quyết định cho phép/từ chối so với oracle; vi phạm/vượt hạn mức. `Inconclusive` do trace hoặc cửa sổ quan sát chưa đủ không được tính là đạt.
- **Hiệu năng:** thông lượng và độ trễ; p95/p99 được tính theo từng lượt rồi tóm tắt giữa các lượt, không gộp mẫu để tạo một percentile chung.
- **Bảo vệ backend và client hợp lệ:** số yêu cầu tới backend/quá tải, số yêu cầu hợp lệ được xử lý thành công mỗi giây và độ trễ của client hợp lệ. 429 là từ chối do hết hạn mức; 5xx có thể gồm quá tải hoặc chế độ từ chối khi lỗi; timeout/lỗi truyền tải có thể không cho biết backend đã nhận yêu cầu hay chưa.
- **Redis outage:** khả năng phục vụ client hợp lệ, vi phạm hạn mức và phục hồi theo định nghĩa/cửa sổ đã chốt trước lượt đo. Chế độ cho qua khi lỗi có thể nhận yêu cầu khi không xác minh được hạn mức; đây là đánh đổi về policy, tự nó không chứng minh có race condition.
- **Chất lượng lượt đo:** tải chào mời/đã gửi/đã hoàn tất, request rơi, lỗi bộ giới hạn, clock discontinuity và sự khớp giữa trace, summary, metrics và cấu hình. Phải giữ lại lượt lỗi/không hợp lệ cùng lý do, không chỉ chọn lượt thuận lợi.

## 5. Tình trạng evidence và đánh giá hiện tại

**Calibration lịch sử:** T04 hoàn tất 10 cấu hình normal/burst với một lượt mỗi cấu hình. T05 hoàn tất 27 cấu hình scaling hợp lệ, đồng thời lưu riêng một lượt lỗi do bộ tạo tải và ba lượt gián đoạn. T05 ghi nhận backend chung giới hạn khoảng 190 success/s ở offered 250 RPS; không suy ra khả năng mở rộng API hoặc chế độ nào tốt hơn. T07 hoàn tất calibration capacity10 có giới hạn: bốn ca healthy/outage gửi đủ 12.000 request, không rơi request, hai healthy gate đạt, recovery ổn định sau 4 giây theo tiêu chí cửa sổ 1s/min5/3 cửa sổ sạch; first success được báo riêng. Exporter smoke đánh dấu cả bốn ca dùng được sau một sửa lỗi null-resource riêng; revision đo gốc không đổi. Batch capacity4 quá tải/observer lỗi trước đó vẫn là bằng chứng sơ bộ, không ghép với cấu hình khác như cùng phép đo.

Các pilot trước đó gồm calibration dừng do clock discontinuity và ma trận 84 cấu hình có oracle mismatch, kết quả inconclusive, limiter errors hoặc generator drops; chúng không thay thế benchmark chính thức. Gate T01–T03 đạt ổn định trong phiên đo hiện tại và chất lượng sáu lượt pilot normal/mixed; độ chính xác UTC tuyệt đối và độ bền sau resume/restart chưa xác minh. Bằng chứng T06 là kiểm tra Redis thật: khi quota gần cạn, đúng hai đơn vị còn lại được chấp nhận ở cả Fixed Window và Token Bucket. Đối chứng non-atomic đồng bộ chủ động 16 reader để buộc lost update, tạo overshoot 15 khi quota là 1; đây là minh họa race có điều kiện, không đo tần suất tự nhiên. T06 không đo hiệu năng HTTP hay thông lượng Redis.

T09 đã thu thập đủ dữ liệu với 138/138 vị trí chạy dự kiến dùng được và 46/46 cấu hình đã tổng hợp. T10 chưa bắt đầu; phân tích và kết luận RQ1–RQ5 đang chờ yêu cầu tiếp tục riêng. Xem [gate T01–T03](worklog/2026-10-19-measurement-gate/README.md), [calibration T04](worklog/2026-10-19-calibration-next/README.md), [scaling T05](worklog/2026-10-19-calibration-next/T05-README.md), [atomicity T06](worklog/2026-10-19-atomicity/README.md), [calibration recovery T07](worklog/2026-10-19-outage-recovery/README.md), [bằng chứng sơ bộ T07](worklog/2026-10-19-outage/README.md), [readiness](experiments/PROTOCOL_READINESS.md), [checkpoint](context/SESSION_CHECKPOINT.md) và các [pilot cũ](worklog/2026-10-13-calibration/README.md).

**Kết quả chính thức:** `[Đã thu thập dữ liệu T09; điền sau khi hoàn tất phân tích T10, kèm bảng/hình, run IDs, revision, manifest và giới hạn tương ứng.]`

**Trả lời RQ1–RQ5:** `[Để trống đến khi có phân tích T10 theo yêu cầu tiếp tục riêng. Không suy câu trả lời từ smoke test hoặc pilot.]`

**Hạn chế cần bàn luận:** gate clock mới chỉ chứng minh ổn định trong phiên quan sát, chưa xác minh UTC tuyệt đối hoặc restart/resume. Các Fixed Window oracle ở gate T03 là inconclusive do chỉ quan sát cửa sổ một phần. Kiểm tra atomicity ép race bằng barrier nên không ước lượng tần suất race trong tải tự nhiên. Backend là mô phỏng; phép đo cùng host có thể chịu ảnh hưởng từ scheduler, generator, logging và tài nguyên dùng chung. Không ngoại suy kết quả sang doanh thu, production readiness hay hệ thống phân tán lớn hơn.

## 6. Kết luận tạm thời và hướng phát triển

Ở trạng thái hiện tại, dự án đã có prototype để khảo sát trạng thái cục bộ/chia sẻ, hai thuật toán hạn mức, quyết định nguyên tử bằng Redis Lua, mẫu tải hỗn hợp và hai chính sách khi Redis lỗi. Bằng chứng hiện tại cho thấy đã có công cụ và các hành vi pilot cụ thể; dữ liệu T09 cũng đã được thu thập đầy đủ. Tuy nhiên, T10 chưa bắt đầu nên chưa có căn cứ để kết luận cuối về thuật toán/chế độ nào tốt hơn hoặc mức cải thiện là bao nhiêu.

Protocol đã khóa và các lượt đo T09 đã hoàn tất. Phần tiếp theo là tiếp tục T10 theo yêu cầu riêng, phân tích từng câu hỏi nghiên cứu rồi cập nhật kết luận và hình/bảng có thể truy ngược về artifacts. Hướng mở rộng như Sliding Window, dashboard hoặc nền tảng kiểm soát lưu lượng rộng hơn chỉ nên cân nhắc sau khi hoàn thành baseline và theo yêu cầu của giảng viên.

## 7. Việc còn lại cho bản nộp

- Khi được yêu cầu tiếp tục, hoàn thành T10: bảng/hình cho RQ1–RQ5, biến thiên giữa lượt, phân tích nguyên nhân lỗi và liên kết tới run/cấu hình/revision; không thay kết quả thiếu bằng số 0 hoặc gộp percentile sai.
- Bổ sung chương kết quả/kết luận sau T10; hiện không điền phát hiện hay effect size.
- Đối chiếu yêu cầu hình thức và rubric khi được cung cấp; xác nhận ngày nộp/bảo vệ. H01 phần tự kiểm tra kiến thức vẫn do người học hoàn tất.
- Bổ sung tài liệu tham khảo có thật, trích dẫn chính xác và rà soát cùng slide/demo khi bộ kết quả cuối đã thống nhất.

## Tài liệu tham khảo

Các khái niệm rate limiting và lý do chọn các biến đo cần gắn với nguồn học thuật sau khi người viết đã đọc và xác định đúng ấn phẩm. Tài liệu Redis dưới đây chỉ hỗ trợ các tuyên bố triển khai về atomic scripting và thời gian server; không thay thế nguồn học thuật hoặc kết quả thí nghiệm.

1. Redis, “Scripting with Lua.” Tài liệu chính thức mô tả việc thực thi script là atomic và blocking trên Redis. Dùng để dẫn giải lựa chọn gộp quyết định quota vào một script; không phải bằng chứng thực nghiệm của dự án. https://redis.io/docs/latest/develop/programmability/eval-intro/
2. Redis, “TIME.” Đặc tả chính thức về timestamp giây và microsecond do Redis trả về; dùng cho mô tả nguồn thời gian shared-state. https://redis.io/docs/latest/commands/time/

Danh mục này còn sơ bộ; bổ sung nguồn thuật toán/queueing chỉ khi phần tổng quan thực sự dùng các khẳng định cần trích dẫn, và hoàn thiện định dạng theo rubric khi được cung cấp.
