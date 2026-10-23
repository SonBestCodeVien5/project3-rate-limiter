# Lộ trình học Project 3 và chuẩn bị bảo vệ

> Đây là lộ trình học theo chủ đề, không phải trạng thái task hay lịch chính thức. Nguồn Roadmap gợi ý 10–11 tuần; mốc nộp tạm hiện là giữa tháng 12/2026, còn ngày chính thức và rubric chưa có. Xem [kế hoạch việc còn lại](REMAINING_WORK_PLAN.md) để biết task, [readiness](experiments/PROTOCOL_READINESS.md) để biết cổng đo, và [sổ P2](monitoring/PHASE2_PLAN.md) cho nhánh monitoring.

## Bài toán cần giải thích

Giảng viên đã đồng ý hướng đề tài và yêu cầu thể hiện góc nhìn doanh nghiệp. Sản phẩm cần nộp gồm báo cáo, source, slides và demo. Mốc lập kế hoạch tạm là giữa tháng 12/2026; ngày chính thức và rubric chưa được xác nhận. T11 đã tích hợp bản nháp, còn định dạng/rubric; T13 chưa có deck hoặc rehearsal. H01/H02 còn chờ xác nhận của người học/giảng viên.

Trong kịch bản flash sale giả định, nhiều API instance có thể nhận request của cùng client. Bộ đếm local riêng lẻ làm quota bị cộng dồn; thao tác Redis không atomic cũng có thể vượt quota khi requests concurrent. Traffic vượt kiểm soát có thể làm API/backend chậm hoặc lỗi, ảnh hưởng người mua hợp lệ và tạo rủi ro giao dịch; chưa có sự cố, doanh thu hay SLO của doanh nghiệp thật được đo.

Project đo Fixed Window và Token Bucket; local và Redis shared state; burst, concurrency, scaling; và mixed workload gồm client hợp lệ cùng client tạo traffic bất thường. So sánh none/local/Redis trên cùng workload/backend để đánh giá quota correctness, goodput và latency của client hợp lệ, backend arrivals, 429/timeout/5xx và Redis resources. Một Redis outage ngắn kiểm tra fail-open/fail-closed và recovery; đây không phải kiểm thử production HA.

Mạch báo cáo: **bài toán doanh nghiệp → pain point → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → hướng phát triển**. Tác động kinh doanh là giả định, chưa có doanh thu hay SLO doanh nghiệp được đo. Sliding Window, dashboard và tính năng gateway là mở rộng tùy chọn; không thay bằng chứng RQ1–RQ5.

## Học theo thứ tự

| Chặng | Học và tự làm | Có thể giải thích khi hoàn tất |
| --- | --- | --- |
| 1. Request và quota | Vẽ client → load balancer → API instance → limiter → backend; phân biệt reject với lỗi backend. | Vì sao cùng client gửi qua hai instance local có thể dùng gấp đôi quota? |
| 2. FW và TB | Tính tay chuỗi request ở ranh giới Fixed Window; với Token Bucket tính token ban đầu, refill và burst. | Vì sao `B=Q` và `r=Q/W` không làm hai thuật toán có cùng burst semantics? |
| 3. Shared state và concurrency | Vẽ local state/Redis state; xem Redis key/TTL, Lua atomic operation và read–decide–write không atomic. | Điều gì xảy ra khi request cùng key đồng thời gần hết quota? Atomic operation khắc phục phần nào? |
| 4. Đo và outage | So sánh none/local/Redis trên cùng normal, burst và mixed workload; phân biệt offered load, sent/completed, allow/reject/error và legitimate goodput; đọc p50/p95/p99, backend arrivals, resource metrics; phân biệt wall clock và monotonic khi đo; giải thích fail-open/fail-closed. | Làm sao biết backend được bảo vệ mà client hợp lệ vẫn được phục vụ? Một lần pause Redis chứng minh được gì và chưa chứng minh được gì? |
| 5. Kết quả và bảo vệ | Đối chiếu protocol, cấu hình, revision và từng run; trình bày kết quả cùng giới hạn. | Kết luận nào có dữ liệu hỗ trợ, cái gì `inconclusive`, và cần đo thêm gì? |

Không cần học sâu Kubernetes, service mesh, cloud production hay authentication platform để hoàn tất phạm vi này. Tài liệu bổ trợ cho giai đoạn thuật toán là [Redis INCR](https://redis.io/docs/latest/commands/incr/) và [Redis Lua scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/).

<a id="kiến-thức-nền-và-cách-tự-kiểm-tra-để-hoàn-tất-tuần-1"></a>
## Bài tự kiểm tra nền tảng

Giải thích bằng lời và vẽ sơ đồ; chưa cần framework hoặc code.

1. Vẽ một HTTP request qua load balancer và API; chỉ ra limiter quyết định allow/reject ở đâu.
2. Với quota 10 request/phút/client và hai API instance đếm local, giải thích vì sao hệ thống có thể nhận 20 request/phút. Nếu dùng quota chung, request thứ 11 ra sao?
3. Nêu khác nhau giữa quota, client key, window và burst; tính một ví dụ Fixed Window và một ví dụ Token Bucket.
4. Phân loại request bị limiter từ chối với request được cho qua nhưng backend lỗi. Vì sao phải ghi riêng hai kết quả?

**Điều kiện tự xác nhận:** trả lời được bốn câu và nói trong 1–2 phút chuỗi flash sale → traffic tăng → local quota lệch → client hợp lệ bị ảnh hưởng → cần quota chung → cần đo correctness và backend protection. AI không tự xác nhận thay người học.

## Cổng chất lượng của nghiên cứu

Trước khi chốt kiến trúc, xác định policy, allow/reject oracle, backend workload và hành vi Redis lỗi. Trước phép đo chính thức, protocol phải khóa; generator đạt offered load; state được reset; cấu hình và raw evidence lưu được; outage tái lập được. Trước khi kết luận, nối kết quả với đúng run/configuration, giữ cả lượt không hợp lệ có lý do và không chọn riêng kết quả thuận lợi. `Inconclusive` không phải pass; pilot không phải benchmark chính thức. Chi tiết protocol và điều kiện hiện hành ở [readiness](experiments/PROTOCOL_READINESS.md).

## Hồ sơ và câu hỏi khi bảo vệ

Chuẩn bị prototype/lệnh tái tạo, sơ đồ, policy/ma trận đo, raw data và bảng/hình, báo cáo, slides và demo có fallback. Dùng [bản nháp báo cáo](REPORT_DRAFT.md), [hướng dẫn đọc T10](analysis/T10_RESULTS.md#cách-đọc-bảng-và-hình) và [kịch bản demo/bảo vệ](DEMO_SCRIPT.md). Trình bày `n=3`, median (min–max) không phải confidence interval; p95/p99 tính theo từng lượt rồi tổng hợp, không phải percentile trace gộp. T11 đã tích hợp bản nháp; định dạng/rubric còn chờ. T13 chưa có deck và chưa diễn tập. Xác nhận ngày chính thức và feedback với giảng viên.

Tập trả lời bằng số liệu/hình cụ thể: Vì sao local quota có thể bị vượt? FW và TB khác nhau ra sao ở burst? Redis shared state đã đủ đảm bảo atomicity chưa? Khi tăng API instance, bottleneck chuyển đi đâu? Mixed traffic ảnh hưởng legitimate goodput và backend thế nào? Fail-open/fail-closed đổi availability và quota ra sao? Kết luận nào dữ liệu hiện tại chưa chứng minh được?
