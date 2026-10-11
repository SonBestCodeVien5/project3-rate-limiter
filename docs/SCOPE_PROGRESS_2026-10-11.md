# Phạm vi, tiến độ và chiến lược học — 11/10/2026

## Ý kiến và căn cứ

Giữ phạm vi Project 3 hiện tại. Dựng code nhanh chưa phải bằng chứng đề tài quá nhỏ. Theo [Roadmap nguồn](context/sources/00_Project3_Roadmap.md) > [Proposal](context/sources/01_Project3_Proposal.md) > [Research Context](context/sources/10_Supplementary_Research_Context.md) > [Positioning](context/sources/11_Positioning_Against_Existing_Solutions.md), đầu ra chính là prototype và bằng chứng trả lời RQ1–RQ5, không phải một sản phẩm gateway nhiều chức năng. Mốc lịch 11 tuần là lịch đề xuất, không phải 11 phần việc ngang nhau.

Không có rubric chấm điểm chính thức trong repo; không đưa ra phần trăm khả năng đạt điểm hay bảo đảm giảng viên sẽ đánh giá đủ. Cần dùng đề cương/ma trận bằng chứng khi trao đổi với giảng viên, không dùng tốc độ AI sinh code để suy ra chuẩn đồ án.

## Ước lượng trước vòng công cụ đo thứ hai

Đây là thước quản trị do agent đề xuất, không phải trọng số nguồn/trường. Chỉ ghi hoàn thành khi có deliverable/bằng chứng; không dùng số dòng code hay số tuần đã đi qua.

| Nhóm deliverable | Trọng số đề xuất | Mức hoàn thành ước lượng sau bootstrap | Phần đã có / còn thiếu |
| --- | ---: | ---: | --- |
| Bài toán, scope, RQ và yêu cầu | 10% | 90% | Framing đã có; thiếu lịch/rubric chính thức |
| Prototype và kiểm chứng kỹ thuật | 25% | 85% | FW/TB local/Redis, concurrency, API/backend, outage; thiếu một số công cụ đo |
| Phương pháp và công cụ thí nghiệm | 20% | 40% | Có trace/runner mixed; thiếu profile/scaling/analyzer và protocol khóa |
| Dữ liệu chính thức và đánh giá RQ1–RQ5 | 25% | 10% | Smoke 7 case; chưa benchmark lặp/đánh giá chính thức |
| Báo cáo/biểu đồ cuối kỳ | 10% | 15% | Có context/ADR/worklog; chưa bản báo cáo kết quả |
| Demo, tự giải thích và bảo vệ | 10% | Chưa có bằng chứng hoàn tất | Không suy code chạy thành người học đã nắm; tạm chưa cộng vào tổng |

Tổng theo thước này khoảng 42%, nên giao tiếp bằng khoảng **40–45% toàn đồ án** thay vì độ chính xác giả. Prototype riêng khoảng **80–85%**. Chỉ cập nhật tỷ lệ sau vòng tiếp theo nếu công cụ thực sự được test/review và có evidence; không cộng trước cho công việc agent đang làm.

## Vì sao chưa mở rộng scope

- Tính đúng: shared state chưa tự bảo đảm atomicity; test pass trên vài chuỗi chưa thay oracle cho toàn trace.
- Phép đo: offered load, drops, clock, retry, backend capacity, warm-up, cùng quota dài hạn nhưng burst khác nhau đều có thể làm kết luận sai.
- RQ3 cần scaling thật trên cùng backend; RQ5 cần legitimate goodput, quota violation và recovery, không chỉ thấy server sống lại.
- Báo cáo cần liên hệ business impact với dữ liệu và giới hạn, không chỉ mô tả implementation.

Ưu tiên chiều sâu trong phạm vi: workload burst gần biên cửa sổ, nhiều lượt lặp, quota đúng theo client/window, độ nhạy với backend capacity/Redis latency khi cần kiểm chứng giả thuyết. Đây là các thí nghiệm phục vụ RQ hiện có, không thêm một nền tảng mới.

Chỉ cân nhắc mở rộng sau khi: protocol đã khóa, đủ bằng chứng cả 5 RQ, báo cáo/demo bản đầu đã chạy được và người học giải thích được các quyết định. Khi đó chọn tối đa một mở rộng có câu hỏi và phép đo riêng (ví dụ Sliding Window), có lợi cho báo cáo và được giảng viên đồng ý. Không thêm dashboard/gateway/Redis Cluster vì còn quota AI hoặc vì code nhanh.

## Dựng trước rồi học lại

Có thể dùng prototype như tài liệu học và tiết kiệm thời gian thiết lập môi trường. Điều kiện là để một giai đoạn học/kiểm chứng có đầu ra rõ, không trì hoãn đến sát bảo vệ. Khả năng giải thích của người học là deliverable riêng, chưa thể giao AI hoàn thành hộ.

Các bài thực hành ngắn có thể làm sau mỗi nhóm commit:

1. Vẽ đường đi một request và chỉ ra allow/reject trước backend; giải thích 429, 503, 502 khác nhau.
2. Tính tay một chuỗi FW/TB gồm request ở biên cửa sổ và refill; dự đoán trước khi chạy test.
3. Đổi từ 1 sang 2 API, dự đoán quota local/global; kiểm tra trace rồi giải thích chênh lệch.
4. Đọc Lua và minh họa vì sao GET–SET riêng có lost update; phân biệt atomicity với exactly-once khi mất response.
5. So một biểu đồ legitimate goodput với backend arrivals; nêu một nguyên nhân gây sai lệch và một điều kết quả chưa chứng minh.
6. Tự sửa một policy/test nhỏ, chạy lại, giải thích diff mà không phụ thuộc vào câu trả lời soạn sẵn.

Có thể dùng các commit nhỏ, worklog, raw data và test hiện tại để học theo thứ tự trên, không cần đọc toàn repo trong một lần.

## Dùng gói hiện có hợp lý

Ý kiến thực hành: ưu tiên phiên có công cụ/khả năng tốt cho thiết kế phép đo, debugging concurrency, integration và review kết luận. Dùng model nhỏ hoặc công cụ miễn phí cho phần tra cứu file đã chỉ định, giải thích từng hàm, luyện câu hỏi, dàn ý và sửa câu chữ. Phân tích repo lớn hay viết chương đánh giá có thể vẫn khó; phân biệt viết diễn đạt với kiểm tra khoa học.

Theo [tài liệu OpenAI được kiểm tra ngày 11/10/2026](https://learn.chatgpt.com/docs/pricing), mức sử dụng phụ thuộc model, context, reasoning và công cụ; tài liệu khuyên xem usage dashboard và cân nhắc model nhỏ/phạm vi hẹp. Free/Plus có mức truy cập và giới hạn khác nhau; không bảo đảm công việc dài với nhiều file sẽ chạy giống nhau khi đổi gói. Không lấy giá API suy ra số task còn lại của Plus.

Benchmark local, script phân tích và đọc Markdown/git diff có thể chạy không cần gọi model. Mục tiêu hữu ích của giai đoạn hiện tại là để lại lệnh tái lập, dữ liệu có cấu trúc và hồ sơ đủ rõ để việc học/viết tiếp sau này ít lệ thuộc vào một phiên AI đắt. Chưa có đo đạc usage thực tế của tài khoản, nên không hứa phần trăm token tiết kiệm chỉ dựa vào việc chọn subagent.

## Cập nhật sau vòng công cụ đo

Đã triển khai/test profiles normal/burst/concurrent, topology1/2/4, analyzer FW/TB/outage và chạy đủ 11 case pilot khác nhau; phát hiện và giữ hai lượt không đạt tải, hiệu chỉnh cả ba mode mixed. [Hồ sơ vòng đo](worklog/2026-10-11-measurement/README.md) ghi kết quả, lỗi và giới hạn.

Theo cùng thước quản trị, prototype khoảng **90%**, phương pháp/công cụ khoảng **65–70%**, dữ liệu nghiên cứu chính thức vẫn khoảng **10%** vì đây còn là pilot. Tổng deliverable khoảng **50% (ước lượng 45–55%)**: 10%×90% + 25%×90% + 20%×65–70% + 25%×10% + 10%×15%; chưa cộng hoàn tất nhóm demo/tự giải thích khi chưa có bằng chứng. Đây không phải phần trăm kiến thức của người học hoặc điểm dự kiến.

Khuyến nghị vẫn giữ scope. Giá trị của vòng này là phép đo có thể phát hiện mình chưa đạt offered load và không tự báo pass, thay vì có thêm một tính năng ngoài RQ. Dùng thời gian còn lại cho protocol, dữ liệu lặp, phân tích và học lại; chỉ xét mở rộng sau khi năm RQ, báo cáo/demo bản đầu và việc tự giải thích đã có bằng chứng.
