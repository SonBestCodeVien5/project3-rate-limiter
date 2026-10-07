# Lộ trình Project 3: từ bắt đầu đến bảo vệ

**Trạng thái:** kế hoạch đề xuất để thảo luận, chưa phải lịch chính thức. [Roadmap gốc](context/sources/00_Project3_Roadmap.md) định hướng Project 3 trong khoảng **10–11 tuần**, nhưng chưa nêu ngày nộp hoặc ngày bảo vệ. Dùng bảng dưới theo **tuần tương đối**; khi có lịch của trường và giảng viên hướng dẫn, đặt ngày thật và điều chỉnh. [Proposal](context/sources/01_Project3_Proposal.md) xác định câu hỏi nghiên cứu, còn [đặc tả thí nghiệm](experiments/EXPERIMENT_SPEC.md) hiện là bản nháp.

## Đích cuối cùng

Project cần giải thích được chuỗi: **traffic bất thường → nguy cơ quá tải backend nhiều instance → nhu cầu quota chung → limiter dùng Redis → thí nghiệm → kết quả và trade-off**. Sản phẩm để bảo vệ gồm prototype chạy được, mã/cấu hình tạo lại thí nghiệm, dữ liệu và biểu đồ, báo cáo, slide và khả năng giải thích các quyết định. Đây là nền tảng nghiên cứu, không phải API Gateway production.

**Phần bắt buộc từ tài liệu:** API instances, load balancer, Redis shared state, Fixed Window, Token Bucket, tải bình thường/burst/concurrent, so sánh local và shared state, scaling, correctness/overshoot, latency, throughput, Redis CPU/memory. Nghiên cứu atomicity là trọng tâm của Roadmap. **Phần có thể cắt nếu thiếu thời gian:** Sliding Window, monitoring nâng cao, nhiều mức tải phụ và các chức năng gateway.

## Lộ trình 11 tuần đề xuất

| Tuần | Làm gì | Học vừa đủ để làm | Quyết định và sản phẩm cần có |
| --- | --- | --- | --- |
| **1 — Định nghĩa bài toán** | Xác nhận lịch/rubric của trường và yêu cầu giảng viên; đọc Roadmap, Proposal, đặc tả nháp; viết 1 trang mô tả vấn đề doanh nghiệp, tác động và câu hỏi nghiên cứu. | Luồng HTTP request, API instance, load balancer, quota là gì; phân biệt bài toán kinh doanh với giải pháp kỹ thuật. | **Chốt phạm vi:** Project 3 nghiên cứu limiter, không xây gateway. Có bản mô tả đề tài và danh sách đầu ra phải nộp. |
| **2 — Nắm thuật toán và quy tắc đúng/sai** | Tự mô phỏng bằng bảng một chuỗi request cho Fixed Window và Token Bucket; thử request tại ranh giới cửa sổ và burst. Hoàn thiện phần policy của [đặc tả](experiments/EXPERIMENT_SPEC.md). | Counter, window, token refill, burst; đồng hồ và thứ tự request; vì sao Token Bucket không thể đo overshoot bằng quota của Fixed Window. | **Chốt policy thử nghiệm:** client key, `Q/W`, `B/r`, thời điểm tính, điều kiện allow/reject và oracle đối chiếu. |
| **3 — Thiết kế thí nghiệm và kiến trúc** | Vẽ luồng request và state; xác định các biến độc lập, biến giữ cố định, ma trận chạy và dữ liệu phải ghi. Chọn tech stack sau khi biết cần đo gì. | Local vs shared state, Redis key/TTL, atomic command và Lua Script, race condition, cách một thí nghiệm kiểm soát biến. | **Chốt thiết kế:** vị trí limiter, cơ chế atomic/đối chứng, xử lý Redis lỗi, backend/framework, cách chạy nhiều instance và công cụ tạo tải. Ghi lý do ngắn cho từng quyết định. |
| **4 — Dựng baseline đo được** | Tạo API test nhỏ, chạy nhiều instance qua load balancer, tạo tải và thu log/metrics cơ bản; đo đường đi **chưa bật limiter**. Kiểm tra load generator đạt tải đặt ra. | Latency end-to-end, throughput, p50/p95/p99, offered load vs completed load, bottleneck của máy tạo tải. | Có lệnh chạy lại baseline, bản ghi cấu hình môi trường và dữ liệu đầu tiên. Không dùng baseline lỗi để so sánh các limiter. |
| **5 — Fixed Window** | Triển khai cùng một policy ở local state và Redis shared state; kiểm tra quota, ranh giới cửa sổ, key độc lập và nhiều instance. | Counter, expiry/TTL, thao tác Redis atomic, quota toàn hệ thống. | Có kết quả kiểm tra đúng/sai và một bảng local–Redis ban đầu. Redis atomic phải giữ policy đã định trong bài test concurrent nhỏ. |
| **6 — Token Bucket** | Triển khai local và Redis; kiểm tra bucket ban đầu, refill, burst, thời gian trôi và reset state. Dùng cùng endpoint, key và đường đi đo như Fixed Window. | Token refill theo thời gian, sai số số học/thời gian, cách so sánh hai thuật toán có burst semantics khác nhau. | Cả hai thuật toán chạy được; có oracle hoặc bộ ca kiểm tra độc lập cho từng thuật toán. |
| **7 — Concurrent correctness** | Tạo request cùng key khi quota gần hết; so Redis atomic với biến thể không atomic **chỉ dùng làm đối chứng thí nghiệm**. Ghi quyết định, instance và lỗi. | Race condition, read–modify–write, tính atomic, vì sao Redis shared state tự nó chưa bảo đảm correctness. | Có bằng chứng trả lời RQ4; kiểm tra không nhầm timeout/Redis error với reject hợp lệ. **Đóng phạm vi tính năng cốt lõi** sau tuần này. |
| **8 — Pilot và khóa quy trình đo** | Chạy thử normal, burst và scaling; tìm mức tải đủ phân biệt các cấu hình mà load generator vẫn ổn định. Sửa cách đo nếu dữ liệu thiếu hoặc nhiễu. | Warm-up, reset state, lặp thí nghiệm, phân phối latency, cách phát hiện bottleneck và sai lệch đồng hồ. | Chốt RPS/concurrency, thời lượng, số lần lặp, số instance và định dạng dữ liệu. Ghi toàn bộ vào đặc tả; **khóa protocol** trước các lượt chính thức. |
| **9 — Chạy thí nghiệm chính thức** | Chạy ma trận cần thiết cho RQ1–RQ4, ưu tiên 1/2/4 instance nếu môi trường chịu được; lưu raw data, cấu hình và kết quả từng lượt. Chạy lại lượt lỗi có lý do rõ. | Cách đọc p95/p99, overshoot, allowed/rejected throughput, Redis CPU/memory; so sánh khi chỉ một biến đổi. | Bộ dữ liệu tái chạy được. Mỗi biểu đồ dự kiến đều truy về `run_id` và cấu hình. **Khóa dữ liệu** sau khi kiểm tra đầy đủ. |
| **10 — Phân tích và viết báo cáo** | Tính chỉ số, tạo bảng/biểu đồ, trả lời từng RQ; giải thích kết quả bất ngờ và giới hạn thí nghiệm. Hoàn thiện báo cáo, để thời gian sửa theo phản hồi giảng viên. | Trade-off correctness–latency–throughput, cách viết phương pháp và giới hạn, phân biệt giả thuyết với kết luận có dữ liệu. | Báo cáo hoàn chỉnh và có thể tái tạo các hình từ dữ liệu. Nếu thiếu thời gian, cắt mở rộng trước khi cắt bằng chứng cho RQ. |
| **11 — Chuẩn bị và bảo vệ** | Nộp đúng định dạng/hạn; làm slide, demo ngắn và phương án dự phòng khi demo lỗi; tập trình bày có bấm giờ, tập hỏi đáp. Đóng băng code và kết quả theo hạn nộp. | Giải thích kiến trúc, thuật toán, atomicity, cách đo, hạn chế và đóng góp của dự án bằng ngôn ngữ ngắn gọn. | Có bộ nộp cuối, slide, bản demo và danh sách câu hỏi tự kiểm tra. Bảo vệ xong, lưu phản hồi và những hướng mở rộng cho đồ án tốt nghiệp. |

Nếu chỉ có **10 tuần**, gộp phần kiến thức nền của tuần 2 vào tuần 1–3 và giữ nguyên thời gian cho thí nghiệm, phân tích, bảo vệ. Nếu ngày bảo vệ ở sau tuần 11, dùng phần dư để sửa báo cáo và tập trình bày; không tự động mở rộng tính năng. Dành một khoảng dự phòng cho lỗi môi trường và các lần chạy lại.

**Nhịp theo dõi đề xuất:** cuối mỗi tuần ghi ngắn ba mục: đã hoàn thành gì, bằng chứng nằm ở đâu, quyết định/vướng mắc nào cần xử lý tuần tới. Mang bản này trao đổi với giảng viên hướng dẫn khi có buổi gặp. Nếu trễ tiến độ, ưu tiên giữ bốn RQ và thời gian đo/viết; cắt phần mở rộng trước.

## Những cổng cần qua trước khi chuyển giai đoạn

1. **Trước khi chọn stack/code:** đã chốt policy, cách đo đúng/sai, vị trí limiter và thí nghiệm nào trả lời RQ nào. Tech stack là phương tiện để chạy và đo các cấu hình đó.
2. **Trước khi chạy số liệu chính thức:** có script/lệnh tạo lại môi trường, reset state, cấu hình tải, logs và cách tính metrics; chạy pilot thấy generator và Redis không tạo nhiễu không kiểm soát.
3. **Trước khi viết kết luận:** các lượt chạy có cấu hình và raw data, không chọn riêng một kết quả đẹp; phân biệt hành vi đúng của Token Bucket với overshoot của Fixed Window.
4. **Trước khi nộp:** báo cáo, biểu đồ, slide và demo dùng cùng phiên bản code/dữ liệu; câu trả lời cho RQ1–RQ4 có bằng chứng và giới hạn rõ.

## Học theo thứ tự, không học tràn lan

| Chủ đề | Cần hiểu đến mức nào |
| --- | --- |
| HTTP, API, load balancer | Vẽ được một request đi qua các thành phần; biết allow/reject xảy ra trước phần xử lý backend. |
| Fixed Window, Token Bucket | Tính tay kết quả cho một chuỗi request; giải thích ranh giới window và burst/refill. |
| Redis shared state và atomicity | Giải thích vì sao local quota bị nhân lên ở nhiều instance và vì sao read–modify–write có race condition. |
| Concurrency và thời gian | Hiểu request đồng thời có thể xen kẽ; xác định timestamp và thứ tự dùng để kiểm tra correctness. |
| Load testing và metrics | Phân biệt tải gửi vào, request hoàn tất, allow/reject/error; đọc p50/p95/p99 và resource usage. |
| Phương pháp thí nghiệm | Biết giữ biến khác cố định, warm-up, reset state, lặp lượt, lưu cấu hình và nêu giới hạn kết luận. |
| Viết và bảo vệ | Trả lời được: vấn đề là gì, vì sao giải pháp hợp lý, đã so sánh công bằng chưa, kết quả nói gì và chưa nói gì. |

Không cần học sâu Kubernetes, service mesh, cloud infrastructure hoặc xây authentication platform để hoàn thành Project 3.

**Nguồn học bổ trợ khi đến tuần 3–7:** [Redis `INCR` và ví dụ rate limiter](https://redis.io/docs/latest/commands/incr/) cho counter, expiry và tình huống race; [Redis Lua scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/) cho tính atomic của một script. Đây là tài liệu kỹ thuật bổ trợ; quyết định phạm vi vẫn theo tài liệu Project 3 trên Drive.

## Bộ hồ sơ cần có lúc bảo vệ

- **Mã và cách chạy:** prototype, cấu hình môi trường, hướng dẫn chạy một lượt test và tạo lại kết quả.
- **Phương pháp:** policy/thuật toán, sơ đồ kiến trúc, ma trận thí nghiệm, định nghĩa metrics và các quyết định có lý do.
- **Bằng chứng:** raw data, bảng/biểu đồ, tóm tắt theo RQ1–RQ4, giới hạn và kết quả không như dự đoán.
- **Báo cáo:** bối cảnh doanh nghiệp → tác động → yêu cầu → giải pháp → thí nghiệm → đánh giá → hướng phát triển.
- **Bảo vệ:** slide ngắn theo cùng mạch, demo có phương án dự phòng và phần trả lời câu hỏi.

Trước buổi bảo vệ, tập trả lời bằng **số liệu hoặc hình cụ thể**: Vì sao nhiều instance với local state có thể vượt quota chung? Fixed Window và Token Bucket khác nhau ở burst thế nào? Redis shared state đã đủ để tránh race chưa? Atomic operation đổi kết quả ra sao? Khi thêm instance, bottleneck chuyển tới đâu? Kết luận nào dữ liệu hiện tại chưa chứng minh được?

**Việc cần làm ngay:** xác nhận ngày nộp/ngày bảo vệ và rubric; sau đó cùng chốt policy trong [đặc tả thí nghiệm](experiments/EXPERIMENT_SPEC.md). Chưa cần chọn framework ở bước đầu.
