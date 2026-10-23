# Đặc tả thí nghiệm Project 3 — phạm vi cơ sở cập nhật

**Vai trò tài liệu:** đây là đặc tả thiết kế ban đầu ngày 13/10/2026, không phải protocol đã khóa. Các mục **Mở** là ghi chép lịch sử; quyết định đã chọn ở [thiết kế prototype](../IMPLEMENTATION.md), protocol đo ở [PROTOCOL_READINESS.md](PROTOCOL_READINESS.md). T09 đã hoàn tất và T10 đã phân tích offline; xem [kết quả T10](../analysis/T10_RESULTS.md), [task baseline](../REMAINING_WORK_PLAN.md) và [hồ sơ triển khai](../worklog/2026-10-11-bootstrap/README.md) để phân biệt kiểm tra/smoke với dữ liệu nghiên cứu.

Đã có [Console tùy chỉnh](../CONSOLE.md) và [ma trận 84 lượt thực chạy](../worklog/2026-10-12-console-matrix/README.md) ngày 12/10: một lượt 3 giây cho mỗi tổ hợp, không chủ động gây outage. Các artifact nhất quán, nhưng có phát hiện từ oracle, lỗi Redis và request bị generator bỏ; không dùng bộ này như benchmark chính thức. Ma trận rộng phục vụ kiểm tra cấu hình; nghiên cứu chọn phép so sánh phù hợp với từng RQ.

**Nguồn:** [Roadmap](../context/sources/00_Project3_Roadmap.md) → [Proposal](../context/sources/01_Project3_Proposal.md) → [Research Context](../context/sources/10_Supplementary_Research_Context.md).  

**Nhãn:** **Phạm vi** = phạm vi cơ sở trong tài liệu dự án; **Thiết kế đề xuất** = phương pháp cần khóa trước lượt đo; **Mở** = chưa quyết định.

**Bối cảnh đã chọn:** API bán hàng trong flash sale, dùng để giải thích tác động doanh nghiệp. Đây là kịch bản giả định; prototype chỉ mô phỏng API/traffic cần cho thí nghiệm, không xây hệ thống bán hàng.

## Mục tiêu và câu hỏi

**Phạm vi:** đo quota chung, chi phí hiệu năng và mức bảo vệ backend khi chuyển từ local state sang Redis state được chia sẻ. Phạm vi cập nhật bổ sung workload hỗn hợp và Redis outage ngắn. So sánh:

| Câu hỏi từ Proposal | Biến so sánh | Kết quả cần đo |
| --- | --- | --- |
| RQ1: Thuật toán ảnh hưởng thế nào? | Fixed Window ↔ Token Bucket | Burst, độ trễ, thông lượng, allow/reject |
| RQ2: Shared state thay đổi điều gì? | Local ↔ Redis, giữ các biến khác cố định | Quota toàn hệ thống, độ trễ, thông lượng, Redis resource |
| RQ3: Tăng quy mô thay đổi điều gì? | Số API instance | thông lượng, độ trễ, correctness |
| RQ4: Atomicity giúp gì? | Redis non-atomic ↔ Redis atomic dưới tải concurrent | Race condition và quyết định sai/overshoot |
| RQ5: Quá tải hoặc Redis không khả dụng ảnh hưởng gì? | Không limiter ↔ local ↔ Redis shared trên tải hỗn hợp; fail-open ↔ fail-closed khi ngắt Redis | Goodput/p95/p99 của client hợp lệ, backend arrivals, 429/timeout/5xx, vi phạm quota và recovery |

**Phạm vi:** prototype có load balancer, API instance, limiter, Redis và backend mô phỏng có năng lực giới hạn; không cần gateway hoàn chỉnh hay database nghiệp vụ. **Mở:** Roadmap và Proposal đặt limiter ở vị trí khác nhau; chốt vị trí trước khi thiết kế code.

## Policy và phép so sánh

- **Thiết kế đề xuất:** mỗi request tốn 1 đơn vị; cùng `client_key` phải chia sẻ quota trên mọi instance. Request bị reject không chạy xử lý backend. Cấu hình policy tĩnh và có version trong mỗi lượt chạy.
- **Fixed Window:** tối đa `Q` request/key trong cửa sổ `W`. Chốt rõ ranh giới cửa sổ.
- **Token Bucket:** sức chứa `B`, tốc độ nạp `r` token/giây. Bắt đầu so sánh với `B = Q`, `r = Q/W` để có cùng tốc độ dài hạn; hai thuật toán vẫn cho phép burst khác nhau.
- **Thiết kế đề xuất:** ma trận cơ sở là `{Fixed Window, Token Bucket} × {local, Redis atomic} × {một, nhiều instance}`; chọn số instance qua pilot. Local nhiều instance là đối chứng cho việc không có shared state. Chỉ dùng Redis non-atomic trong bài concurrent để kiểm tra RQ4, không xem là cấu hình mục tiêu.
- **Oracle:** đối chiếu quyết định với policy độc lập cho từng thuật toán. Với concurrent requests, định nghĩa thứ tự quyết định hoặc bất biến có thể kiểm tra; không suy thứ tự chỉ từ timestamp phía client.
- **Mở:** giá trị `Q/W/B/r`, key, nguồn thời gian, thứ tự request concurrent, TTL, timeout, hành vi khi Redis lỗi và cơ chế atomic cụ thể. Atomicity là phần cốt lõi; Lua Script là một cơ chế có thể chọn. Sliding Window là phần mở rộng.

## Kịch bản

| Kịch bản | Mục đích |
| --- | --- |
| Normal | Đo độ trễ, thông lượng và tài nguyên khi tải dưới tốc độ cấp phát. |
| Burst | Đo hành vi allow/reject, độ trễ đỉnh và phục hồi; thử gần ranh giới Fixed Window. |
| Concurrent | Gửi nhiều request cùng key khi quota gần hết để tìm race condition. |
| Scaling | Lặp cùng workload khi tăng API instance; ghi cả chi phí Redis. |
| Mixed overload | Client hợp lệ gửi tải ổn định, một client khác tạo burst; backend có năng lực xử lý giới hạn được xác định qua pilot. So không limiter, local và Redis shared trên cùng offered load, policy và backend. |
| Redis outage | Ngắt Redis trong khoảng định trước khi đang gửi tải; so fail-open và fail-closed rồi khôi phục. Ghi quyết định, lỗi, vi phạm quota, tính sẵn sàng và phục hồi. |

**Thiết kế đề xuất:** chỉ chạy các tổ hợp cần để trả lời RQ tương ứng, không nhân toàn bộ ma trận một cách máy móc. Tách dữ liệu trước/trong/sau Redis outage. Pilot phải chứng minh load generator đạt offered load và xác định được ngưỡng quá tải backend có kiểm soát. Các mức RPS/concurrency trong tài liệu nguồn là ví dụ, không phải tham số đã duyệt.

## Chỉ số và tính đúng

- **Fixed Window:** trên từng key và cửa sổ hoàn tất, `overshoot_count = max(0, allowed_count - Q)`, `overshoot_rate = overshoot_count / Q`. Đối chiếu allow/reject với policy oracle.
- **Token Bucket:** đối chiếu quyết định với oracle cùng `B`, `r`, trạng thái ban đầu và quy tắc thời gian. Việc nhận hơn `Q` request trong một cửa sổ Fixed Window có thể hợp lệ đối với Token Bucket; báo cáo quyết định sai và burst được nhận, không gọi đó là overshoot.
- **Độ trễ:** p50/p95/p99 đầu cuối, tách client hợp lệ/bất thường và allow/reject/error. Khi đánh giá bảo vệ backend, báo cáo riêng p95/p99 của các request hợp lệ thành công.
- **Thông lượng:** offered load và số request completed/allowed/rejected/error mỗi giây. `Legitimate goodput` là số request của client hợp lệ được backend xử lý thành công mỗi giây; không tính 429 là goodput.
- **Bảo vệ backend:** nguồn số đo là delta metrics trước/sau tại backend: arrivals (đã nhận), success (xử lý hoàn tất), `overload` (đã nhận nhưng không còn chỗ tiếp nhận, trả 503), canceled (context bị hủy sau khi tiếp nhận). Đối chiếu legitimate goodput và HTTP 429/timeout/5xx phía client; 5xx có thể do fail-closed hoặc lỗi truyền tải backend nên không dùng thay chỉ số `overload`. Xem [định nghĩa và số đo thực](../worklog/2026-10-12-console-matrix/README.md).
- **Redis outage:** availability của client hợp lệ = số request hợp lệ thành công / số request hợp lệ đã gửi trong khoảng lỗi; báo cáo vi phạm quota theo policy và thời gian từ lúc Redis trở lại đến khi quyết định/độ trễ ổn định theo cửa sổ quan sát chốt ở pilot. Fail-open có thể chủ động vượt quota; phân loại đây là trade-off của policy, không tự động gọi là race condition.
- **Resource:** Redis CPU/memory; ghi network overhead hoặc bottleneck API/load generator nếu đo được đáng tin cậy.

Mỗi lượt chạy cần lưu cấu hình, version code/policy, `run_id`, request ID, client class/key, instance, thời điểm, quyết định, mã phản hồi, độ trễ và lỗi; ghi actual offered load và thời điểm ngắt/khôi phục Redis. Giữ endpoint, backend workload và môi trường giống nhau khi đổi một biến; đặt lại trạng thái, ghi làm nóng và trạng thái ban đầu; lặp nhiều lượt và báo cáo độ dao động. Tách timeout/lỗi hệ thống khỏi reject hợp lệ.

## Quyết định tiếp theo

Prototype đã chọn client key, policy và quy tắc thời gian, vị trí limiter, Redis Lua, fail policy và stack; xem [thiết kế](../IMPLEMENTATION.md). Lượt smoke ban đầu đã chạy. Các mục dưới đây là câu hỏi trong bản thiết kế lịch sử, không phải trạng thái công việc hiện tại. Protocol nghiên cứu v1.2 cùng phụ lục v1.3 đã được dùng cho T09; T10 đã phân tích offline. Xem [kết quả T10](../analysis/T10_RESULTS.md) và [kế hoạch việc còn lại](../REMAINING_WORK_PLAN.md):

1. Analyzer độc lập đã có kiểm tra trace FW/TB và phân pha outage/recovery; xem [hợp đồng phân tích](ANALYSIS.md). Còn phải xác định mức quan sát cho cửa sổ đầy đủ và vi phạm quota khi fail-open có quyết định không rõ; không coi trạng thái `inconclusive` (chưa đủ bằng chứng kết luận) là pass.
2. Dùng các lượt calibration đã có để chốt ngưỡng backend, mức tải, làm nóng, số lần lặp, số API instance, cửa sổ Redis outage và cách đo tài nguyên.
3. Điều tra oracle mismatch ở hai lượt local Token Bucket và Redis I/O timeouts được giữ trong ma trận 84 lượt; không đổi trạng thái `observed_violations`/`inconclusive` thành đạt.
4. Kiểm chứng generator đạt offered load ở các mức đã chọn, rồi khóa protocol trước các lượt đo chính thức.

Kết quả mong muốn là dữ liệu tái chạy được để trả lời RQ1–RQ5 và giải thích trade-off correctness–performance–backend protection–availability; chưa đặt trước kết luận thuật toán hay fail policy nào tốt hơn. Redis Cluster, dashboard, tier/endpoint policy management và gateway đầy đủ nằm ngoài lõi.
