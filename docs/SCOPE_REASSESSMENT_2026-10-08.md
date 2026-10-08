# Baseline Project 3 sau khi đánh giá lại — 08/10/2026

**Trạng thái:** baseline triển khai đã được cập nhật trong Roadmap/Proposal trên Drive và tài liệu repo; kiến trúc, policy, stack, mức tải và ngưỡng đạt vẫn cần chốt qua thiết kế/pilot. Đây là chuẩn nội bộ của Project 3, không phải rubric chính thức của HUST. Cơ sở: [Roadmap](context/sources/00_Project3_Roadmap.md) > [Proposal](context/sources/01_Project3_Proposal.md) > [Research Context](context/sources/10_Supplementary_Research_Context.md), [đặc tả thí nghiệm](experiments/EXPERIMENT_SPEC.md), và [cuộc nghiên cứu mới](https://chatgpt.com/share/6ac7b012-74b4-83ec-b23b-5d65e067a7a2).

## Kết luận

Giữ đề tài **distributed rate limiting cho API nhiều instance**. Proposal cập nhật giữ RQ1–RQ4 và thêm RQ5 về bảo vệ client hợp lệ khi overload và trade-off khi Redis unavailable. Độ sâu cần thể hiện qua quota đúng dưới concurrent load, so sánh có kiểm soát, tác động trực tiếp lên backend và một fault injection nhỏ. Không lấy số màn hình, số endpoint hoặc số thành phần hạ tầng làm thước đo phạm vi.

Thay đổi quan trọng nhất của baseline là **thí nghiệm bảo vệ backend**: một client tạo tải bất thường trong khi các client hợp lệ gửi tải ổn định, với backend có năng lực xử lý giới hạn. So sánh không limiter, local limiter và Redis shared limiter trên cùng workload; đo số request hợp lệ hoàn tất, p95/p99 của request hợp lệ, timeout/5xx và tải đến backend. Từ đó kiểm tra được mạch vấn đề doanh nghiệp → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá.

## Đối chiếu với nghiên cứu mới

| Ý trong cuộc nghiên cứu | Đánh giá theo nguồn dự án | Trạng thái sau cập nhật |
| --- | --- | --- |
| Tăng chiều sâu về atomic correctness | Đã có trong Roadmap và RQ4 của Proposal; Proposal cập nhật làm rõ atomicity là lõi. | **Baseline:** kiểm chứng atomicity; chốt cơ chế khi thiết kế. Một biến thể cố ý không atomic chỉ làm đối chứng concurrent. Không đồng nhất atomicity với yêu cầu phải dùng Lua ở mọi thuật toán. |
| Đo hiệu quả bảo vệ backend và client hợp lệ | Roadmap/Proposal cập nhật đưa workload hỗn hợp vào phạm vi. | **Baseline:** so không limiter, local, Redis shared; đo legitimate goodput, p95/p99, backend arrivals, 429/timeout/5xx. |
| Fail-open/fail-closed khi Redis lỗi | Roadmap/Proposal cập nhật đưa Redis outage ngắn vào phạm vi và RQ5. | **Baseline có giới hạn:** ngắt Redis có kiểm soát, ghi availability, quota violation và recovery. Không xây Redis Cluster hoặc chịu lỗi production. |
| Quota theo tier/endpoint, dashboard | Vẫn không cần cho câu hỏi nghiên cứu. | **Tùy chọn:** cấu hình policy tĩnh, có version trong dữ liệu thí nghiệm, là đủ để tái lập. |
| Đổi tên thành “có khả năng chịu lỗi” | Một thí nghiệm ngắt Redis không chứng minh khả năng chịu lỗi toàn hệ thống. | **Giữ tên hiện tại** cho đến khi có kết quả và thống nhất với giảng viên. |

Nguồn HUST công khai mô tả IT3940 là học phần 3 tín chỉ, tìm hiểu vấn đề cụ thể, đề xuất giải pháp và kiểm chứng tính tiền khả thi bằng thử nghiệm hoặc lý thuyết, rồi báo cáo và thuyết trình. [Tài liệu chương trình 2017, trang PDF 39](https://soict.hust.edu.vn/wp-content/uploads/Bachelor-Talent-program-1.pdf) không phải rubric của kỳ 2026. Các repo công khai như [IT3940 Knowledge Distillation](https://github.com/vohuutridung/IT3940), [IT3943 CNF/NFVI Testbed](https://github.com/hunganh1310/cnf-testbed) và [Hybrid GraphRAG](https://github.com/thanhbach0904/Project3-20251) minh họa cách trình bày phương án và phép kiểm chứng; chúng là mẫu thuận tiện, không đại diện cho chuẩn chấm điểm hay phân bố điểm của HUST.

## Phạm vi thí nghiệm nên khóa trước khi code

1. **Policy và oracle:** giữ Fixed Window và Token Bucket; định nghĩa key, quota, nguồn thời gian, trạng thái ban đầu và ranh giới thời gian. So quyết định với oracle riêng từng thuật toán. Không gọi số request Token Bucket vượt `Q` trong cửa sổ Fixed Window là overshoot.
2. **Correctness:** chạy 1 và nhiều instance; local so với Redis shared; riêng concurrent dùng cùng key và quota gần cạn để so bản atomic với bản đối chứng không atomic. Redis có lệnh atomic cho thao tác đơn, còn chuỗi đọc–quyết định–ghi có thể cần Lua/Functions hoặc cơ chế tương đương. [Redis rate limiter](https://redis.io/docs/latest/develop/use-cases/rate-limiter/) và [Redis scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/) mô tả các cơ chế này.
3. **Backend protection:** workload hỗn hợp gồm client hợp lệ và client tạo burst; backend giới hạn năng lực có kiểm soát. Giữ tổng tải, tỷ lệ client, quota và thời lượng giống nhau giữa các cấu hình. Ghi offered load, backend arrivals, goodput của client hợp lệ, p95/p99 riêng cho client hợp lệ, timeout, 5xx và reject 429. Không gộp 429 với lỗi dịch vụ.
4. **Performance và scaling:** giữ các chỉ số trong Roadmap: correctness/overshoot, p50/p95/p99, requests/giây, Redis CPU/memory; ghi số instance, cấu hình máy, warm-up, reset state, run ID và các lượt lặp. Pilot trước để kiểm tra load generator đạt tải đặt ra và xác định ngưỡng quá tải của backend, thay vì vô tình đo giới hạn của máy tạo tải.
5. **Redis outage:** triển khai cả fail-open và fail-closed như hai cấu hình so sánh, ngắt Redis trong khoảng định trước và đo quota violation, availability/recovery. Đây là phép thử giới hạn; không suy từ fault injection này ra độ sẵn sàng production.

**Thứ tự ưu tiên khi thiếu thời gian:** policy/oracle → prototype và baseline → correctness/atomicity → backend protection → Redis outage nhỏ → benchmark lặp lại và báo cáo RQ1–RQ5 → tier/endpoint hoặc dashboard. Sliding Window, gateway đầy đủ, service mesh và Kubernetes production vẫn ngoài lõi Project 3. Giảm số mức tải phụ trước khi cắt bằng chứng cho một RQ.

## Điểm cần thống nhất khi lập kế hoạch

- Roadmap vẽ lớp traffic control phía trước API instances, còn Proposal mô tả limiter gắn với API instances. Vị trí triển khai phải được chốt và ghi lý do trước khi code; không coi một sơ đồ ví dụ là quyết định đã duyệt.
- Roadmap nhấn mạnh Lua trong nghiên cứu atomicity; Proposal cập nhật coi atomicity là lõi và so thêm Redis Functions là mở rộng. Mục tiêu phải đạt là quyết định quota đúng dưới concurrency; cơ chế cụ thể cần được chốt theo policy và thuật toán.
- Ngày nộp/bảo vệ chính thức và rubric kỳ 2026 chưa có trong repo. Vì vậy nhận định “underscope” là đánh giá rủi ro, không phải kết luận theo chuẩn chấm của HUST.
