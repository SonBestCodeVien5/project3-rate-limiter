# Kết quả phân tích T10 — T09 protocol v1.2

## Bối cảnh và cách đọc

Muốn xem cách diễn giải biểu đồ và ký hiệu trục, mở [Cách đọc bảng và hình](#cách-đọc-bảng-và-hình).

Một đợt bán hàng tăng đột biến có thể làm backend quá tải, kéo dài độ trễ và làm khách hợp lệ gặp lỗi. Yêu cầu kỹ thuật là so sánh limiter Fixed Window (FW) và Token Bucket (TB), local state và Redis shared state, đo ảnh hưởng lên backend dưới tải hỗn hợp/burst, xem scaling theo topology, và quan sát fail-open/fail-closed khi Redis outage.

T09 dùng workload và topology mô phỏng theo protocol khóa, không đo doanh thu hay backend production. T10 phân tích 138 lượt hợp lệ trong 46 ô, ba repetition mỗi ô. Bảng máy và Markdown được sinh từ CSV export đã khóa cùng `analysis.json` đã băm trong archive; xem [bảng T10](../worklog/2026-10-20-t10/T10_TABLES.md), [dữ liệu từng lượt](../worklog/2026-10-20-t10/run-evidence.csv), [traceability](../worklog/2026-10-20-t10/traceability.csv) và [provenance](../worklog/2026-10-20-t10/provenance.json).

Trạng thái task hiện hành nằm trong [kế hoạch phần việc còn lại](../REMAINING_WORK_PLAN.md); điều kiện cho phép đo nằm trong [readiness protocol](../experiments/PROTOCOL_READINESS.md). Đây là phân tích offline của evidence T09 hiện có, không mở lại phép đo.

Các con số báo cáo median và min–max trên ba lượt riêng. Goodput mỗi lượt là số legitimate request thành công chia cho `elapsed_seconds_including_drain`; `run-evidence.csv` giữ tử số và thời lượng mẫu cho từng lượt. p50/p95/p99 là percentile từng lượt rồi tổng hợp, không phải percentile của trace gộp. Bảng và `retry-history.json` giữ trạng thái correctness, lượt không hợp lệ cùng lý do. Không có kiểm định ý nghĩa thống kê.

## Cách đọc bảng và hình

Mỗi ô có ba repetition; `median (min–max)` là trung vị và khoảng quan sát giữa ba lượt, không phải confidence interval hay kiểm định ý nghĩa. p50/p95/p99 được tính riêng mỗi lượt rồi mới tóm tắt; p95 trên hình là median của ba p95, không phải p95 của trace gộp. Offered RPS là tải dự kiến; goodput là legitimate request thành công chia cho thời gian thực gồm drain. Backend overload là số request, không phải latency hay tỷ lệ; arrivals đã chứa success và overload. Chỉ so sánh các contrast giữ workload, policy và topology cố định.

Đọc các hình theo RQ: mixed overload so sánh số backend overload giữa none/local/Redis; burst goodput là legitimate success mỗi giây và no-limiter lặp lại làm mốc; outage availability chỉ bao phủ phase Redis pause, còn stable recovery tách riêng first success. Hình scaling giữ mode cố định, trục X là 1/2/4 API và legend là 50/180/250 RPS; ở 250 RPS backend mô phỏng là bottleneck, nên goodput gần 191/s không chứng minh API scaling. Hình latency dùng p95 theo từng run. Redis CPU là cores trung bình, không phải peak hay chi phí Lua; memory là snapshot cuối lượt, không phải peak. Outage không có resource sample nên khoảng trống không phải zero.

Các hình dùng median với thanh min–max; trục Y có thể bị thu hẹp nên đọc số trục và bảng, không so độ cao ảnh đơn thuần. `e` là ký hiệu khoa học: `1e-2 = 0.01`, `1e-6 = 0.000001`, `1e+6 = 1,000,000`. CPU `0.011` core tương đương khoảng 1.1% một core; mixed `0.031–0.032` là 3.1–3.2%, burst `0.016` là 1.6%. Memory `1.285` tại mốc `1e6` là 1,285,000 bytes (xấp xỉ 1.285 MB thập phân). Goodput normal có offset `+1.999e1`: nhãn `0.0076` biểu diễn `19.9976 request/s`; offset là phép cộng. Xem số chính xác cùng [bảng](../worklog/2026-10-20-t10/T10_TABLES.md), [traceability](../worklog/2026-10-20-t10/traceability.csv) và [provenance](../worklog/2026-10-20-t10/provenance.json).

## RQ1 — FW so với TB trong normal, burst và mixed

Ở tải normal 20 RPS, cả hai thuật toán cùng các mode đều gần đạt 20 request hợp lệ/giây; p50/p95/p99 và allow/reject nằm trong [bảng RQ1](../worklog/2026-10-20-t10/T10_TABLES.md). Trong mixed và burst, TB có goodput và backend outcomes khác FW ở một số cặp được đối chiếu. Đây là mô tả các workload đã khóa; `B=Q` và `r=Q/W` không làm burst response tương đương.

Correctness oracle của FW vẫn **inconclusive**. Analyzer đánh dấu tất cả FW window là partial vì trace phía client không xác lập đầy đủ khoảng quan sát trong miền giờ server/Redis; tăng thời lượng trace thụ động tự nó không làm oracle đổi trạng thái. Các decision trong trace vẫn có thể được đối chiếu với quota khi state mới, trace đầy đủ, không outage/cancel và không thiếu/không rõ decision, nhưng đó không chứng minh toàn bộ traffic của window. TB có các lượt `no_violation_observed_within_trace`, nghĩa là không quan sát vi phạm trong trace đó, không phải chứng minh tổng quát. Bảng giữ allow/reject, trạng thái oracle, số violation và lower bound overshoot. Với burst, p50/p95/p99 theo phase base/peak có ở từng dòng `run-evidence.csv`.

Hình: [latency p95 theo thuật toán và workload (SVG)](../worklog/2026-10-20-t10/figures/rq1-latency.svg) · [goodput normal (SVG)](../worklog/2026-10-20-t10/figures/rq1-normal.svg) · [goodput burst (SVG)](../worklog/2026-10-20-t10/figures/rq5-burst.svg).

## RQ2 — local state so với Redis shared state

Các cặp local/Redis giữ workload, algorithm, policy quota và topology cố định; các contrast FW/TB chỉ đổi algorithm, còn contrast no/local/Redis chỉ đổi state mode. [Bảng RQ2](../worklog/2026-10-20-t10/T10_TABLES.md) đưa p50/p95/p99 và goodput cạnh allow/reject/oracle; với Redis, bảng còn có CPU cores, memory đầu/cuối, network byte delta, rate và khoảng mẫu thực tế. Tải normal cho thấy Redis p95 cao hơn local một lượng nhỏ trong máy đo này; không suy rộng thành kết quả của mọi workload.

Redis counters là tổng TCP traffic từ workload, sampler INFO, healthcheck và thao tác admin, không phải bytes/request riêng của limiter hay wire overhead. Mỗi sample interval được tính từ timestamp INFO đầu tiên tới cuối cùng; tốc độ được tính từ delta trên khoảng đó. Ô không có sampler, gồm outage, để trống chứ không được ghi thành zero.

Hình: [Redis CPU (SVG)](../worklog/2026-10-20-t10/figures/rq2-redis-cpu.svg) · [Redis memory (SVG)](../worklog/2026-10-20-t10/figures/rq2-redis-memory.svg).

## RQ3 — sweep 50/180/250 RPS theo 1/2/4 API

Ở 50 và 180 RPS, goodput gần offered load và backend overload bằng 0 hoặc tối đa vài request trong ba lượt. Ở 250 RPS, backend capacity 10/service time 50 ms trở thành nút thắt: các mode có khoảng 1.750 overload trên 7.500 backend arrivals mỗi lượt median và goodput gần 191/s. Vì vậy kết quả 250 RPS không chứng minh API scaling, cũng không chọn mode thắng. Chi tiết arrivals/success/overload/canceled và tails theo cả 27 cấu hình nằm trong [bảng RQ3](../worklog/2026-10-20-t10/T10_TABLES.md).

Hình cho biết từng điểm là 1, 2 hay 4 API: [none (SVG)](../worklog/2026-10-20-t10/figures/rq3-scale-none.svg) · [local (SVG)](../worklog/2026-10-20-t10/figures/rq3-scale-local.svg) · [Redis (SVG)](../worklog/2026-10-20-t10/figures/rq3-scale-redis.svg).

## RQ4 — atomicity/concurrency từ T06

T06 kiểm tra các invariant với Redis thật: FW và TB gần hết quota còn đúng hai lượt cho 16 request đồng thời; control không nguyên tử dùng barrier buộc 16 reader cùng thấy counter 0 với quota 1, tạo overshoot 15. Test được ghi nhận là chạy trên working tree dựa trên source revision `26b5decb835dbb136eb2d45b361920a414434f6b`; khi chạy, patch test chưa commit. Phần mô tả trong worklog ghi SHA-256 `b51ef6d5c7c63dac5ae84e729911d4f7fc34cc761384c85674a56cff4d4ca46f`, nhưng artifact manifest [SHA256SUMS](../worklog/2026-10-19-atomicity/artifacts/SHA256SUMS) ghi `28bd8a66a8ec39350954ce31b6caa390f35b895e0a9a1e7a89394ba227e3fc84`, trùng với SHA-256 blob tại commit hậu kỳ `3e938a20925feef05c3608c05675c5149580a837`. Manifest, command và focused log được giữ; không có source snapshot riêng trong artifacts để xác minh độc lập file đã chạy. Không có bằng chứng cho nguyên nhân chênh lệch giữa hai ghi nhận hash. Commit hậu kỳ là ancestor của T09 source `0291a80fb404fea0eafee8c3431acc3631bb423e`, nhưng không đổi revision ghi cho lần chạy T06. Đây là hai nguồn evidence riêng. T06 chỉ là bằng chứng trong test đã chạy, không đo HTTP performance hay tần suất race tự nhiên. Xem [T06 evidence](../worklog/2026-10-19-atomicity/README.md).

## RQ5 — bảo vệ backend và Redis outage

Trong mixed, no limiter có median 1.575 backend overload; Redis TB có 12. Trong burst, Redis TB có 16 overload median. Các limiter đồng thời tạo 429 hợp lệ theo policy; 5xx, timeout và canceled được giữ riêng trong [bảng RQ5](../worklog/2026-10-20-t10/T10_TABLES.md), không gộp outcome dự kiến thành lỗi đo.

Ở outage, availability được đo riêng trong các phase: fail-open là 1.00 trong thời gian Redis pause, fail-closed là 0.00; hai policy đều đạt 1.00 trước pause. Sau khi Redis hồi phục, bảng ghi availability, goodput/tails, backend outcomes, stable recovery và first success riêng. Stable recovery là median 4.000 ms cho fail-open (min–max 3.000–4.000) và 4.000 ms cho fail-closed; first success median lần lượt khoảng 87,7 ms và 108,6 ms. Stable recovery dùng window 1.000 ms, tối thiểu 5 legitimate samples, 3 cửa sổ sạch liên tiếp; ngưỡng p95 healthy khóa trước đo là 81.9048105 ms fail-open và 82.577208 ms fail-closed. Không đồng nhất first success với stable recovery và không thay bằng recovery calibration T07.

Hình: [backend overload mixed/burst (SVG)](../worklog/2026-10-20-t10/figures/rq5-mixed-backend.svg) · [availability chỉ trong pha Redis pause (SVG)](../worklog/2026-10-20-t10/figures/rq5-outage.svg) · [stable recovery (SVG)](../worklog/2026-10-20-t10/figures/rq5-recovery.svg).

## Lịch sử attempt và giới hạn kết luận

Ledger v1.1 ghi 120 attempt bắt đầu, 119 kết thúc, 98 ban đầu được chấp nhận, 21 bị loại và một attempt chưa kết thúc. Sau sửa checker offline cho Compose project label, import chọn 104 lượt và còn 34 thiếu. Ledger v1.2 ghi 36 attempt mới: 31 chấp nhận và 5 invalid vì `generator_drops`. Với p1-128, hai attempt đầu có generator drop, attempt 3 đạt; p1-129 có ba attempt v1.2 generator drop rồi một attempt v1.3 được cho phép riêng và đạt. Final selection lấy attempt đủ điều kiện sớm nhất theo validation, không theo performance. [Retry history](../worklog/2026-10-20-t10/retry-history.json) giữ lý do và archive-relative path của cả attempt bị loại; [traceability](../worklog/2026-10-20-t10/traceability.csv) nối từng planned run ID với accepted artifact và SHA-256.

Kết quả áp dụng cho prototype và workload trong protocol. Fixed Window correctness còn inconclusive; Redis network counters là tổng traffic; outage không lấy Redis resource samples; độ chính xác UTC và độ bền restart/resume chưa xác minh; backend mô phỏng hạn chế suy luận scaling. Tác động flash-sale vẫn là giả định kinh doanh, không phải kết quả đo. Phát triển tiếp theo nên trình bày rõ các giới hạn này trong báo cáo, không mở rộng baseline thành gateway, HA production hay backend production.
