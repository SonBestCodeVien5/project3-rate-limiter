# Kết quả phân tích T10 — T09 protocol v1.2

## Bối cảnh và cách đọc

Một đợt bán hàng tăng đột biến có thể làm backend quá tải, kéo dài độ trễ và làm khách hợp lệ gặp lỗi. Yêu cầu kỹ thuật là so sánh limiter Fixed Window (FW) và Token Bucket (TB), local state và Redis shared state, đo ảnh hưởng lên backend dưới tải hỗn hợp/burst, xem scaling theo topology, và quan sát fail-open/fail-closed khi Redis outage.

T09 dùng workload và topology mô phỏng theo protocol khóa, không đo doanh thu hay backend production. T10 phân tích 138 lượt hợp lệ trong 46 ô, ba repetition mỗi ô. Bảng máy và Markdown được sinh từ CSV export đã khóa cùng `analysis.json` đã băm trong archive; xem [bảng T10](../worklog/2026-10-20-t10/T10_TABLES.md), [dữ liệu từng lượt](../worklog/2026-10-20-t10/run-evidence.csv), [traceability](../worklog/2026-10-20-t10/traceability.csv) và [provenance](../worklog/2026-10-20-t10/provenance.json).

Trạng thái task hiện hành nằm trong [kế hoạch phần việc còn lại](../REMAINING_WORK_PLAN.md); điều kiện cho phép đo nằm trong [readiness protocol](../experiments/PROTOCOL_READINESS.md). Đây là phân tích offline của evidence T09 hiện có, không mở lại phép đo.

Các con số báo cáo median và min–max trên ba lượt riêng. Goodput mỗi lượt là số legitimate request thành công chia cho `elapsed_seconds_including_drain`; `run-evidence.csv` giữ tử số và thời lượng mẫu cho từng lượt. p50/p95/p99 là percentile từng lượt rồi tổng hợp, không phải percentile của trace gộp. Bảng và `retry-history.json` giữ trạng thái correctness, lượt không hợp lệ cùng lý do. Không có kiểm định ý nghĩa thống kê.

## RQ1 — FW so với TB trong normal, burst và mixed

Ở tải normal 20 RPS, cả hai thuật toán cùng các mode đều gần đạt 20 request hợp lệ/giây; p50/p95/p99 và allow/reject nằm trong [bảng RQ1](../worklog/2026-10-20-t10/T10_TABLES.md). Trong mixed và burst, TB có goodput và backend outcomes khác FW ở một số cặp được đối chiếu. Đây là mô tả các workload đã khóa; `B=Q` và `r=Q/W` không làm burst response tương đương.

Correctness oracle của FW vẫn **inconclusive** vì các cửa sổ quan sát không đủ chứng minh quota đầy đủ; một lượt đo hợp lệ không phải correctness pass. TB có các lượt `no_violation_observed_within_trace`, nghĩa là không quan sát vi phạm trong trace đó, không phải chứng minh tổng quát. Bảng giữ allow/reject, trạng thái oracle, số violation và lower bound overshoot. Với burst, p50/p95/p99 theo phase base/peak có ở từng dòng `run-evidence.csv`.

Hình: [latency p95 theo thuật toán và workload (SVG)](../worklog/2026-10-20-t10/figures/rq1-latency.svg) · [goodput normal (SVG)](../worklog/2026-10-20-t10/figures/rq1-normal.svg) · [goodput burst (SVG)](../worklog/2026-10-20-t10/figures/rq5-burst.svg).

## RQ2 — local state so với Redis shared state

Các cặp local/Redis giữ workload, algorithm, policy quota và topology cố định; các contrast FW/TB chỉ đổi algorithm, còn contrast no/local/Redis chỉ đổi state mode. [Bảng RQ2](../worklog/2026-10-20-t10/T10_TABLES.md) đưa p50/p95/p99 và goodput cạnh allow/reject/oracle; với Redis, bảng còn có CPU cores, memory đầu/cuối, network byte delta, rate và khoảng mẫu thực tế. Tải normal cho thấy Redis p95 cao hơn local một lượng nhỏ trong máy đo này; không suy rộng thành kết quả của mọi workload.

Redis counters là tổng TCP traffic từ workload, sampler INFO, healthcheck và thao tác admin, không phải bytes/request riêng của limiter hay wire overhead. Mỗi sample interval được tính từ timestamp INFO đầu tiên tới cuối cùng; tốc độ được tính từ delta trên khoảng đó. Ô không có sampler, gồm outage, để trống chứ không được ghi thành zero.

Hình: [Redis CPU (SVG)](../worklog/2026-10-20-t10/figures/rq2-redis-cpu.svg) · [Redis memory (SVG)](../worklog/2026-10-20-t10/figures/rq2-redis-memory.svg).

## RQ3 — sweep 50/180/250 RPS theo 1/2/4 API

Ở 50 và 180 RPS, goodput gần offered load và backend overload bằng 0 hoặc tối đa vài request trong ba lượt. Ở 250 RPS, backend capacity 10/service time 50 ms trở thành nút thắt: các mode có khoảng 1.750 overload trên 7.500 backend arrivals mỗi lượt median và goodput gần 191/s. Vì vậy kết quả 250 RPS không chứng minh API scaling, cũng không chọn mode thắng. Chi tiết arrivals/success/overload/canceled và tails theo cả 27 cấu hình nằm trong [bảng RQ3](../worklog/2026-10-20-t10/T10_TABLES.md).

Hình cho biết từng điểm là 1, 2 hay 4 API: [none (SVG)](../worklog/2026-10-20-t10/figures/rq3-scale-none.svg) · [local (SVG)](../worklog/2026-10-20-t10/figures/rq3-scale-local.svg) · [Redis (SVG)](../worklog/2026-10-20-t10/figures/rq3-scale-redis.svg).

## RQ4 — atomicity/concurrency từ T06

T06 kiểm tra các invariant với Redis thật: FW và TB gần hết quota còn đúng hai lượt cho 16 request đồng thời; control không nguyên tử dùng barrier buộc 16 reader cùng thấy counter 0 với quota 1, tạo overshoot 15. Bài test đã chạy ở source revision `26b5decb835dbb136eb2d45b361920a414434f6b`; SHA-256 của `internal/limiter/redis_test.go` là `b51ef6d5c7c63dac5ae84e729911d4f7fc34cc761384c85674a56cff4d4ca46f`. Patch test chưa commit, nên revision ghi trên không chứa patch đó. Revision T09 dùng cho 138 lượt là `0291a80fb404fea0eafee8c3431acc3631bb423e`; đây là hai nguồn evidence riêng. T06 chỉ là bằng chứng trong test đã chạy, không đo HTTP performance hay tần suất race tự nhiên. Xem [T06 evidence](../worklog/2026-10-19-atomicity/README.md).

## RQ5 — bảo vệ backend và Redis outage

Trong mixed, no limiter có median 1.575 backend overload; Redis TB có 12. Trong burst, Redis TB có 16 overload median. Các limiter đồng thời tạo 429 hợp lệ theo policy; 5xx, timeout và canceled được giữ riêng trong [bảng RQ5](../worklog/2026-10-20-t10/T10_TABLES.md), không gộp outcome dự kiến thành lỗi đo.

Ở outage, availability được đo riêng trong các phase: fail-open là 1.00 trong thời gian Redis pause, fail-closed là 0.00; hai policy đều đạt 1.00 trước pause. Sau khi Redis hồi phục, bảng ghi availability, goodput/tails, backend outcomes, stable recovery và first success riêng. Stable recovery là median 4.000 ms cho fail-open (min–max 3.000–4.000) và 4.000 ms cho fail-closed; first success median lần lượt khoảng 87,7 ms và 108,6 ms. Stable recovery dùng window 1.000 ms, tối thiểu 5 legitimate samples, 3 cửa sổ sạch liên tiếp; ngưỡng p95 healthy khóa trước đo là 81.9048105 ms fail-open và 82.577208 ms fail-closed. Không đồng nhất first success với stable recovery và không thay bằng recovery calibration T07.

Hình: [backend overload mixed/burst (SVG)](../worklog/2026-10-20-t10/figures/rq5-mixed-backend.svg) · [availability chỉ trong pha Redis pause (SVG)](../worklog/2026-10-20-t10/figures/rq5-outage.svg) · [stable recovery (SVG)](../worklog/2026-10-20-t10/figures/rq5-recovery.svg).

## Lịch sử attempt và giới hạn kết luận

Ledger v1.1 ghi 120 attempt bắt đầu, 119 kết thúc, 98 ban đầu được chấp nhận, 21 bị loại và một attempt chưa kết thúc. Sau sửa checker offline cho Compose project label, import chọn 104 lượt và còn 34 thiếu. Ledger v1.2 ghi 36 attempt mới: 31 chấp nhận và 5 invalid vì `generator_drops`. Với p1-128, hai attempt đầu có generator drop, attempt 3 đạt; p1-129 có ba attempt v1.2 generator drop rồi một attempt v1.3 được cho phép riêng và đạt. Final selection lấy attempt đủ điều kiện sớm nhất theo validation, không theo performance. [Retry history](../worklog/2026-10-20-t10/retry-history.json) giữ lý do và archive-relative path của cả attempt bị loại; [traceability](../worklog/2026-10-20-t10/traceability.csv) nối từng planned run ID với accepted artifact và SHA-256.

Kết quả áp dụng cho prototype và workload trong protocol. Fixed Window correctness còn inconclusive; Redis network counters là tổng traffic; outage không lấy Redis resource samples; độ chính xác UTC và độ bền restart/resume chưa xác minh; backend mô phỏng hạn chế suy luận scaling. Tác động flash-sale vẫn là giả định kinh doanh, không phải kết quả đo. Phát triển tiếp theo nên trình bày rõ các giới hạn này trong báo cáo, không mở rộng baseline thành gateway, HA production hay backend production.
