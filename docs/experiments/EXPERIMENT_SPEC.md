# Đặc tả thí nghiệm Project 3 — bản nháp

**Trạng thái:** để thảo luận; chưa chốt kiến trúc, tech stack hay tham số tải.  
**Nguồn:** [Roadmap](../context/sources/00_Project3_Roadmap.md) → [Proposal](../context/sources/01_Project3_Proposal.md) → [Research Context](../context/sources/10_Supplementary_Research_Context.md).  
**Nhãn:** **Yêu cầu** = từ tài liệu dự án; **Đề xuất** = cần duyệt; **Mở** = chưa quyết định.

## Mục tiêu và câu hỏi

**Yêu cầu:** đo cách một limiter bảo vệ backend nhiều instance khi chuyển từ local state sang Redis shared state. So sánh:

| Câu hỏi từ Proposal | Biến so sánh | Kết quả cần đo |
| --- | --- | --- |
| RQ1: Thuật toán ảnh hưởng thế nào? | Fixed Window ↔ Token Bucket | Burst, latency, throughput, allow/reject |
| RQ2: Shared state đổi điều gì? | Local ↔ Redis, giữ các biến khác cố định | Quota toàn hệ thống, latency, throughput, Redis resource |
| RQ3: Scaling đổi điều gì? | Số API instances | Throughput, latency, correctness |
| RQ4: Atomicity giúp gì? | Redis không atomic ↔ atomic dưới tải concurrent | Race condition và quyết định sai/overshoot |

**Yêu cầu:** prototype có load balancer, API instances, limiter và Redis; không cần gateway hoàn chỉnh hay database nghiệp vụ. **Mở:** Roadmap và Proposal đặt limiter ở vị trí khác nhau; chốt vị trí trước khi thiết kế code.

## Policy và phép so sánh

- **Đề xuất:** mỗi request tốn 1 đơn vị; cùng `client_key` phải chia sẻ quota trên mọi instance. Request bị reject không chạy xử lý backend.
- **Fixed Window:** tối đa `Q` request/key trong cửa sổ `W`. Chốt rõ ranh giới cửa sổ.
- **Token Bucket:** sức chứa `B`, tốc độ nạp `r` token/giây. Bắt đầu so sánh với `B = Q`, `r = Q/W` để có cùng tốc độ dài hạn; hai thuật toán vẫn cho phép burst khác nhau.
- **Đề xuất:** ma trận cơ sở là `{Fixed Window, Token Bucket} × {local, Redis atomic} × {1, 2, 4 instances}`. Local nhiều instance là đối chứng cho state không chia sẻ. Chỉ dùng Redis không atomic trong bài concurrent để kiểm tra RQ4, không xem là cấu hình mục tiêu.
- **Mở:** giá trị `Q/W/B/r`, key, nguồn thời gian, thứ tự request concurrent, xử lý khi Redis lỗi và cơ chế atomic cụ thể. Roadmap đặt Lua Script trong trọng tâm atomicity; Proposal xếp Lua Script là mở rộng. Sliding Window cũng là mở rộng.

## Kịch bản

| Kịch bản | Mục đích |
| --- | --- |
| Normal | Đo latency, throughput và tài nguyên khi tải dưới tốc độ cấp phát. |
| Burst | Đo hành vi allow/reject, peak latency và phục hồi; thử gần ranh giới Fixed Window. |
| Concurrent | Gửi nhiều request cùng key khi quota gần hết để tìm race condition. |
| Scaling | Lặp cùng workload khi tăng API instances; ghi cả chi phí Redis. |

**Đề xuất:** chỉ chạy các tổ hợp cần để trả lời RQ tương ứng, không nhân toàn bộ ma trận một cách máy móc. Các mức RPS/concurrency trong tài liệu nguồn là ví dụ, không phải tham số đã duyệt.

## Chỉ số và tính đúng

- **Fixed Window:** trên từng key và cửa sổ hoàn tất, `overshoot_count = max(0, allowed_count - Q)`, `overshoot_rate = overshoot_count / Q`. Đối chiếu allow/reject với policy oracle.
- **Token Bucket:** đối chiếu quyết định với oracle cùng `B`, `r`, trạng thái ban đầu và quy tắc thời gian. Việc nhận hơn `Q` request trong một cửa sổ Fixed Window có thể hợp lệ đối với Token Bucket; báo cáo quyết định sai và burst được nhận, không gọi đó là overshoot.
- **Latency:** p50/p95/p99 end-to-end, tách request được allow và reject.
- **Throughput:** offered load, completed/allowed/rejected/error requests mỗi giây. Không gộp reject nhanh vào năng lực xử lý backend.
- **Resource:** Redis CPU/memory; ghi network overhead hoặc bottleneck API/load generator nếu đo được đáng tin cậy.

Mỗi lượt chạy cần lưu cấu hình, `run_id`, request ID, key, instance, thời điểm, quyết định, latency và lỗi. Giữ endpoint và môi trường giống nhau khi đổi một biến; reset state, ghi warm-up và trạng thái ban đầu; lặp nhiều lượt và báo cáo độ dao động. Tách timeout/lỗi hệ thống khỏi reject hợp lệ.

## Quyết định tiếp theo

1. Chốt `client_key`, `Q/W/B/r`, nguồn thời gian và oracle.
2. Chốt vị trí limiter và cách làm atomic đối chứng.
3. Chạy pilot để chọn mức tải, số lần lặp và cách đo tài nguyên.
4. Sau đó chọn tech stack và triển khai.

Kết quả mong muốn là dữ liệu tái chạy được để trả lời RQ1–RQ4 và giải thích trade-off correctness–performance; chưa đặt trước kết luận thuật toán nào tốt hơn.
