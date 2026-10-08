# Đặc tả thí nghiệm Project 3 — baseline cập nhật

**Trạng thái:** phạm vi đánh giá đã cập nhật theo Roadmap/Proposal; policy, kiến trúc, tech stack, tham số tải và ngưỡng đạt vẫn cần chốt qua thiết kế/pilot.

**Nguồn:** [Roadmap](../context/sources/00_Project3_Roadmap.md) → [Proposal](../context/sources/01_Project3_Proposal.md) → [Research Context](../context/sources/10_Supplementary_Research_Context.md).  

**Nhãn:** **Phạm vi** = baseline trong tài liệu dự án; **Thiết kế đề xuất** = phương pháp cần khóa trước lượt đo; **Mở** = chưa quyết định.

**Bối cảnh đã chọn:** API bán hàng trong flash sale, dùng để giải thích tác động doanh nghiệp. Đây là kịch bản giả định; prototype chỉ mô phỏng API/traffic cần cho thí nghiệm, không xây hệ thống bán hàng.

## Mục tiêu và câu hỏi

**Phạm vi:** đo quota chung, chi phí hiệu năng và mức bảo vệ backend khi chuyển từ local state sang Redis shared state. Baseline mới bổ sung workload hỗn hợp và Redis outage ngắn. So sánh:

| Câu hỏi từ Proposal | Biến so sánh | Kết quả cần đo |
| --- | --- | --- |
| RQ1: Thuật toán ảnh hưởng thế nào? | Fixed Window ↔ Token Bucket | Burst, latency, throughput, allow/reject |
| RQ2: Shared state đổi điều gì? | Local ↔ Redis, giữ các biến khác cố định | Quota toàn hệ thống, latency, throughput, Redis resource |
| RQ3: Scaling đổi điều gì? | Số API instances | Throughput, latency, correctness |
| RQ4: Atomicity giúp gì? | Redis không atomic ↔ atomic dưới tải concurrent | Race condition và quyết định sai/overshoot |
| RQ5: Overload hoặc Redis unavailable ảnh hưởng gì? | Không limiter ↔ local ↔ Redis shared trên tải hỗn hợp; fail-open ↔ fail-closed khi ngắt Redis | Goodput/p95/p99 của client hợp lệ, backend arrivals, 429/timeout/5xx, quota violation và recovery |

**Phạm vi:** prototype có load balancer, API instances, limiter, Redis và backend mô phỏng có năng lực giới hạn; không cần gateway hoàn chỉnh hay database nghiệp vụ. **Mở:** Roadmap và Proposal đặt limiter ở vị trí khác nhau; chốt vị trí trước khi thiết kế code.

## Policy và phép so sánh

- **Thiết kế đề xuất:** mỗi request tốn 1 đơn vị; cùng `client_key` phải chia sẻ quota trên mọi instance. Request bị reject không chạy xử lý backend. Cấu hình policy tĩnh và có version trong mỗi lượt chạy.
- **Fixed Window:** tối đa `Q` request/key trong cửa sổ `W`. Chốt rõ ranh giới cửa sổ.
- **Token Bucket:** sức chứa `B`, tốc độ nạp `r` token/giây. Bắt đầu so sánh với `B = Q`, `r = Q/W` để có cùng tốc độ dài hạn; hai thuật toán vẫn cho phép burst khác nhau.
- **Thiết kế đề xuất:** ma trận cơ sở là `{Fixed Window, Token Bucket} × {local, Redis atomic} × {một, nhiều instance}`; chọn số instance qua pilot. Local nhiều instance là đối chứng cho state không chia sẻ. Chỉ dùng Redis không atomic trong bài concurrent để kiểm tra RQ4, không xem là cấu hình mục tiêu.
- **Oracle:** đối chiếu quyết định với policy độc lập cho từng thuật toán. Với concurrent requests, định nghĩa thứ tự quyết định hoặc bất biến có thể kiểm tra; không suy thứ tự chỉ từ timestamp phía client.
- **Mở:** giá trị `Q/W/B/r`, key, nguồn thời gian, thứ tự request concurrent, TTL, timeout, hành vi khi Redis lỗi và cơ chế atomic cụ thể. Atomicity là phần lõi; Lua Script là một cơ chế có thể chọn. Sliding Window là mở rộng.

## Kịch bản

| Kịch bản | Mục đích |
| --- | --- |
| Normal | Đo latency, throughput và tài nguyên khi tải dưới tốc độ cấp phát. |
| Burst | Đo hành vi allow/reject, peak latency và phục hồi; thử gần ranh giới Fixed Window. |
| Concurrent | Gửi nhiều request cùng key khi quota gần hết để tìm race condition. |
| Scaling | Lặp cùng workload khi tăng API instances; ghi cả chi phí Redis. |
| Mixed overload | Client hợp lệ gửi tải ổn định, một client khác tạo burst; backend có năng lực xử lý giới hạn được xác định qua pilot. So không limiter, local và Redis shared trên cùng offered load, policy và backend. |
| Redis outage | Ngắt Redis trong khoảng định trước khi đang gửi tải; so fail-open và fail-closed rồi khôi phục. Ghi quyết định, lỗi, quota violation, availability và recovery. |

**Thiết kế đề xuất:** chỉ chạy các tổ hợp cần để trả lời RQ tương ứng, không nhân toàn bộ ma trận một cách máy móc. Tách dữ liệu trước/trong/sau Redis outage. Pilot phải chứng minh load generator đạt offered load và xác định được ngưỡng quá tải backend có kiểm soát. Các mức RPS/concurrency trong tài liệu nguồn là ví dụ, không phải tham số đã duyệt.

## Chỉ số và tính đúng

- **Fixed Window:** trên từng key và cửa sổ hoàn tất, `overshoot_count = max(0, allowed_count - Q)`, `overshoot_rate = overshoot_count / Q`. Đối chiếu allow/reject với policy oracle.
- **Token Bucket:** đối chiếu quyết định với oracle cùng `B`, `r`, trạng thái ban đầu và quy tắc thời gian. Việc nhận hơn `Q` request trong một cửa sổ Fixed Window có thể hợp lệ đối với Token Bucket; báo cáo quyết định sai và burst được nhận, không gọi đó là overshoot.
- **Latency:** p50/p95/p99 end-to-end, tách client hợp lệ/bất thường và allow/reject/error. Với backend protection, báo cáo riêng p95/p99 của request hợp lệ thành công.
- **Throughput:** offered load, completed/allowed/rejected/error requests mỗi giây. `Legitimate goodput` là số request của client hợp lệ được backend xử lý thành công mỗi giây; không tính 429 là goodput.
- **Backend protection:** ghi số request đến backend, legitimate goodput, timeout và 5xx. Tách 429 do limiter từ chối khỏi lỗi dịch vụ.
- **Redis outage:** availability của client hợp lệ = số request hợp lệ thành công / số request hợp lệ đã gửi trong khoảng lỗi; báo cáo quota violation theo policy và thời gian từ lúc Redis trở lại đến khi quyết định/latency ổn định theo cửa sổ quan sát chốt ở pilot. Fail-open có thể chủ động vượt quota; phân loại đây là trade-off của policy, không tự động gọi là race condition.
- **Resource:** Redis CPU/memory; ghi network overhead hoặc bottleneck API/load generator nếu đo được đáng tin cậy.

Mỗi lượt chạy cần lưu cấu hình, version code/policy, `run_id`, request ID, client class/key, instance, thời điểm, quyết định, mã phản hồi, latency và lỗi; ghi offered load thực tế và thời điểm ngắt/khôi phục Redis. Giữ endpoint, backend workload và môi trường giống nhau khi đổi một biến; reset state, ghi warm-up và trạng thái ban đầu; lặp nhiều lượt và báo cáo độ dao động. Tách timeout/lỗi hệ thống khỏi reject hợp lệ.

## Quyết định tiếp theo

1. Chốt `client_key`, `Q/W/B/r`, nguồn thời gian và oracle.
2. Chốt vị trí limiter, cơ chế atomic/đối chứng và hành vi fail-open/fail-closed.
3. Chạy pilot để chọn ngưỡng backend, mức tải, số lần lặp, cửa sổ Redis outage và cách đo tài nguyên.
4. Sau đó chọn tech stack và triển khai.

Kết quả mong muốn là dữ liệu tái chạy được để trả lời RQ1–RQ5 và giải thích trade-off correctness–performance–backend protection–availability; chưa đặt trước kết luận thuật toán hay fail policy nào tốt hơn. Redis Cluster, dashboard, tier/endpoint policy management và gateway đầy đủ nằm ngoài lõi.
