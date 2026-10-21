# Cách đọc báo cáo T10, bảng và biểu đồ

T10 đã phân tích dữ liệu T09 theo workload và topology mô phỏng. Hướng dẫn này giúp đọc kết quả đúng phạm vi; không thay thế protocol hay bằng chứng gốc.

Trạng thái hiện tại: T10 đã hoàn tất; không có lượt đo mới và T11 chưa được yêu cầu. Xem [kế hoạch phần việc còn lại](../REMAINING_WORK_PLAN.md) để biết trạng thái task và [readiness protocol](../experiments/PROTOCOL_READINESS.md) để biết các cổng đo.

## Lộ trình đọc

1. Bắt đầu ở [kết quả T10](T10_RESULTS.md) để hiểu câu hỏi, kết quả chính và giới hạn.
2. Mở [bảng T10](../worklog/2026-10-20-t10/T10_TABLES.md) khi cần con số chính xác cho từng cấu hình.
3. Dùng [traceability](../worklog/2026-10-20-t10/traceability.csv) để nối run ID tới artifact và hash; [provenance](../worklog/2026-10-20-t10/provenance.json) ghi revision và nguồn tạo kết quả. [Worklog T10](../worklog/2026-10-20-t10/README.md) giải thích cách tái lập offline và các tệp đi kèm.

## Cách hiểu con số

Protocol giữ ba lượt cho mỗi cấu hình. Số dạng `median (min–max)` là trung vị của ba lượt và khoảng từ nhỏ nhất tới lớn nhất; đây không phải confidence interval và không phải kiểm định ý nghĩa thống kê. Ví dụ `19.997 (19.997–19.997)` cho biết ba lượt có cùng giá trị hiển thị, nhưng tự nó không chứng minh khác biệt có ý nghĩa.

Goodput mỗi lượt bằng số legitimate request thành công chia cho `elapsed_seconds_including_drain`, tức thời gian đo có tính cả giai đoạn drain. p50/p95/p99 được tính riêng trong từng lượt rồi mới tóm tắt ba lượt; p95 trên hình là median của ba giá trị p95, không phải p95 tính từ trace gộp. Bảng và biểu đồ mô tả các cấu hình được so sánh có kiểm soát: workload, policy và topology được giữ như nhau, chỉ yếu tố nêu trong contrast thay đổi.

Độ trễ khách hợp lệ chỉ lấy từ response thành công của legitimate request. Goodput đo số thành công trên thời gian; reject theo quota không được tính là thành công. Backend overload là số request backend quá tải trong một lượt, được tổng hợp riêng và không phải tỷ lệ độ trễ. Số đếm cũng dùng median (min–max); vì có ba lượt và mỗi lượt có số đếm nguyên, median vẫn là số nguyên. Các đuôi `.000` trong bảng chỉ là định dạng hiển thị, không phải phần request lẻ.

Trong outage, availability nằm trong khoảng 0–1 và chỉ tính cho phase được nêu trong bảng/hình. `1` nghĩa là toàn bộ legitimate request trong phase đó thành công theo định nghĩa đo; `0` nghĩa là không request nào thành công. Stable recovery đo từ lúc unpause tới khi đạt các cửa sổ sạch liên tiếp, với cửa sổ 1000 ms, ít nhất 5 mẫu và 3 cửa sổ sạch; ngưỡng p95 healthy đã khóa trước đo. First success là phản hồi thành công đầu tiên sau unpause và được báo riêng, không phải thời gian hồi phục ổn định.

## Đọc 11 biểu đồ

Các PNG mở nhanh trong trình xem; SVG phù hợp phóng to và PDF để in. Mỗi hình có title, nhãn trục, legend và ghi chú median/min–max. Bắt đầu theo thứ tự dưới đây: so sánh outcome chính trước, rồi xem chi phí Redis.

| Thứ tự | Biểu đồ | Cách đọc |
| --- | --- | --- |
| 1 | [Mixed — backend overload (PNG)](../worklog/2026-10-20-t10/figures/rq5-mixed-backend.png) · [SVG](../worklog/2026-10-20-t10/figures/rq5-mixed-backend.svg) | Trục Y là số request backend quá tải trong lượt. Ít hơn nghĩa là ít overload hơn trong workload mixed; so cùng thuật toán giữa no limiter, local và Redis. |
| 2 | [Burst — goodput (PNG)](../worklog/2026-10-20-t10/figures/rq5-burst.png) · [SVG](../worklog/2026-10-20-t10/figures/rq5-burst.svg) | Request hợp lệ thành công mỗi giây trong workload burst. So mode dưới cùng FW hoặc TB; baseline no limiter được lặp làm mốc tham chiếu, không phải các implementation khác nhau. |
| 3 | [Outage — availability (PNG)](../worklog/2026-10-20-t10/figures/rq5-outage.png) · [SVG](../worklog/2026-10-20-t10/figures/rq5-outage.svg) | Mỗi chấm là một trong ba lượt ở phase Redis pause. Trục 0–1 biểu thị phần legitimate request thành công; không đại diện toàn lượt trước và sau outage. |
| 4 | [Recovery — stable recovery (PNG)](../worklog/2026-10-20-t10/figures/rq5-recovery.png) · [SVG](../worklog/2026-10-20-t10/figures/rq5-recovery.svg) | Thời gian từ unpause đến đạt tiêu chí hồi phục ổn định. Các điểm/cột gắn nhãn fail-open và fail-closed; xem bảng để biết first success riêng. |
| 5–7 | Scaling: [no limiter (PNG)](../worklog/2026-10-20-t10/figures/rq3-scale-none.png) · [local (PNG)](../worklog/2026-10-20-t10/figures/rq3-scale-local.png) · [Redis (PNG)](../worklog/2026-10-20-t10/figures/rq3-scale-redis.png) · [SVG no limiter](../worklog/2026-10-20-t10/figures/rq3-scale-none.svg), [local](../worklog/2026-10-20-t10/figures/rq3-scale-local.svg), [Redis](../worklog/2026-10-20-t10/figures/rq3-scale-redis.svg) | Mỗi hình cố định mode; màu/legend là 50, 180, 250 RPS còn trục X là 1, 2, 4 API. So cùng mức RPS khi số API đổi. Ở 250 RPS backend mô phỏng đã thành bottleneck; goodput gần 191/s không chứng minh scaling của API. Các đường nối điểm chỉ dẫn mắt giữa cấu hình phân loại, không phải diễn biến theo thời gian. |
| 8 | [Latency p95 (PNG)](../worklog/2026-10-20-t10/figures/rq1-latency.png) · [SVG](../worklog/2026-10-20-t10/figures/rq1-latency.svg) | Mỗi điểm là median của p95 từng lượt theo workload normal/mixed/burst; các đường là local/Redis kết hợp FW/TB. Đây không phải p95 của toàn bộ request gộp. |
| 9 | [Normal — goodput (PNG)](../worklog/2026-10-20-t10/figures/rq1-normal.png) · [SVG](../worklog/2026-10-20-t10/figures/rq1-normal.svg) | Goodput ở tải bình thường. Độ lệch nhỏ quanh 20 request/s nên đọc cùng trục và số bảng; baseline no limiter lặp lại giữa FW và TB để so sánh cùng mốc. |
| 10 | [Redis CPU (PNG)](../worklog/2026-10-20-t10/figures/rq2-redis-cpu.png) · [SVG](../worklog/2026-10-20-t10/figures/rq2-redis-cpu.svg) | CPU trung bình của tiến trình Redis, theo cores; trục có thể dùng ký hiệu e, xem ví dụ bên dưới. Đây là CPU trung bình quan sát được, không phải peak hay riêng chi phí Lua. |
| 11 | [Redis memory (PNG)](../worklog/2026-10-20-t10/figures/rq2-redis-memory.png) · [SVG](../worklog/2026-10-20-t10/figures/rq2-redis-memory.svg) | `used_memory` ở snapshot cuối lượt, đơn vị bytes. Không phải peak, RAM toàn máy hay bộ nhớ riêng của limiter. |

Các đường dọc thể hiện min–max của ba lượt, còn dấu ở giữa là median. Trục Y được tự động thu hẹp để nhìn rõ khác biệt nhỏ; vì vậy độ cao hình ảnh có thể phóng đại chênh lệch so với toàn miền giá trị. Hãy đọc số trên trục, thanh sai số và bảng cùng nhau.

## Hai ví dụ về ký hiệu trục

`e` là cách viết khoa học của số: `1e-2` bằng `0.01`, `1e-6` bằng `0.000001`, còn `1e+6` bằng `1,000,000`. Nếu trục CPU hiển thị khoảng `0.01` cores, đó là phần nhỏ của một core. Cách tính là tổng delta CPU system và user của Redis (đơn vị giây) chia cho thời gian giữa các mẫu (giây). Vì thế `0.011` core tương đương khoảng 1.1% công suất của một core; các giá trị mixed `0.031–0.032` core tương đương khoảng 3.1–3.2%, và burst `0.016` tương đương 1.6%. Một core nghĩa là công suất của một lõi chạy đầy trong trung bình khoảng đo; đây không phải số core được cấp phát hay tỷ lệ toàn máy. Trung bình cũng có thể che các đỉnh ngắn.

Nếu trục memory có mốc `1e6`, giá trị `1.285` ở mốc đó là `1.285 × 1,000,000 = 1,285,000` bytes, xấp xỉ `1.285 MB` theo đơn vị thập phân. Đây là snapshot `used_memory` cuối lượt của Redis; network counters là tổng traffic workload, sampler, healthcheck và admin, không cô lập riêng limiter. Pha outage không có resource samples, nên ô trống không có nghĩa là zero.

Biểu đồ goodput normal có offset cộng `1.999e1`: nghĩa là trục cộng `19.99` vào các nhãn nhỏ. Chẳng hạn nhãn `0.0076` biểu diễn `19.9976 request/s`. Offset cộng giúp nhìn phần sai khác nhỏ quanh 20; nó không phải phép nhân. Hãy kiểm tra dòng chú thích cạnh trục nếu thấy `+1.999e1` hoặc ký hiệu tương tự.

## Giữ đúng giới hạn khi diễn giải

FW oracle còn inconclusive: không diễn giải điều đó thành pass hay fail. Redis CPU/network là tổng quan sát của tiến trình/counter theo cách lấy mẫu đã ghi; outage thiếu resource samples. Workload dùng backend mô phỏng nên kết quả scaling không chứng minh năng lực production. Các biểu đồ giúp đọc nhanh, còn số chính xác và nguồn gốc nằm trong bảng, traceability và provenance.
