# Tuần 1 — bài toán doanh nghiệp đã chốt

**Bối cảnh được chọn:** doanh nghiệp vận hành API bán hàng trực tuyến trong đợt **flash sale**. Đây là kịch bản nghiên cứu minh họa, không phải một sự cố đã được xác minh tại một công ty. Giảng viên đã đồng ý hướng đề tài và yêu cầu thể hiện rõ vấn đề doanh nghiệp; [Proposal trên Drive](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) đã được bổ sung theo yêu cầu này. [Roadmap gốc](https://docs.google.com/document/d/1oVNMU3KTJ-dWL-3GRDb5tc9JJ75uzxaDmPf0P2yjeWA/edit) vẫn là nguồn ưu tiên cao nhất.

## Mô tả vấn đề

**Doanh nghiệp.** Một đơn vị bán hàng trực tuyến phục vụ người mua qua API. Hệ thống phía sau chạy nhiều API instance sau bộ cân bằng tải để xử lý lượng truy cập lớn. Khi mở flash sale, yêu cầu từ người mua và các chương trình tự động có thể tăng mạnh trong thời gian ngắn.

**Khó khăn nghiệp vụ.** Nếu mỗi API instance giữ bộ đếm rate limit riêng, nó không biết một client đã gửi bao nhiêu request tới các API instance còn lại. Load balancer có thể phân phối request của cùng client qua nhiều instance, khiến tổng request được chấp nhận vượt quota chung mà doanh nghiệp mong muốn. Ngay cả khi chuyển state sang Redis, chuỗi read–decide–write nếu không được thực hiện bằng atomic operation vẫn có thể cho phép vượt quota khi nhiều request đến đồng thời.

**Tác động nghiệp vụ.** Lưu lượng vượt kiểm soát có thể làm API và database chậm hoặc lỗi. Người mua hợp lệ bị ảnh hưởng, tạo rủi ro mất giao dịch và giảm độ tin cậy của dịch vụ. Chưa có log, doanh thu hoặc SLO của một doanh nghiệp cụ thể, nên báo cáo phải trình bày đây là **rủi ro trong kịch bản giả định**, không phải thiệt hại đã đo được.

**Yêu cầu kỹ thuật.** Doanh nghiệp cần một quota chung theo client trên nhiều API instance, quyết định allow/reject trước khi xử lý ở backend, giữ đúng quota với concurrent requests, hạn chế chi phí về độ trễ/thông lượng và duy trì khả năng phục vụ client hợp lệ khi client khác tạo tải bất thường. Khi Redis không khả dụng, prototype cần có hành vi fail-open/fail-closed được xác định rõ để đo sự đánh đổi giữa quota và availability.

**Giải pháp và đánh giá.** Project 3 xây prototype nhỏ với bộ cân bằng tải, nhiều API instance, Redis shared state và rate limiter. So sánh Fixed Window với Token Bucket, local state với shared state trên Redis, một API instance với nhiều instance, non-atomic operation với atomic operation trong bài thử concurrent. Chạy workload normal, burst, concurrent, scaling và mixed workload gồm client hợp lệ cùng client tạo tải đột biến. So sánh không limiter, local rate limiter và Redis shared rate limiter trên cùng workload/backend; đo số request hợp lệ được xử lý thành công mỗi giây (goodput), p95/p99 độ trễ của client hợp lệ, yêu cầu tới backend, phản hồi 429, timeout/5xx, cùng với tính đúng, quota violations/overshoot, thông lượng và CPU/bộ nhớ Redis. Thử ngắt Redis ngắn để so sánh fail-open/fail-closed theo availability, quota violations và thời gian phục hồi. Kết quả cần đánh giá mức bảo vệ backend và chi phí/đánh đổi, không chỉ xác nhận bộ giới hạn chạy được.

**Ranh giới.** Chỉ mô phỏng API/lưu lượng cần cho thí nghiệm; không xây chức năng đơn hàng, thanh toán, Redis Cluster, hệ thống sẵn sàng cao cho môi trường vận hành thực tế hay API Gateway hoàn chỉnh. Nền tảng quản lý lưu lượng rộng hơn là hướng phát triển cho đồ án tốt nghiệp.

## Kết quả tuần 1 và thông tin hành chính

- **Đã chốt:** đề tài distributed rate limiting, bối cảnh flash sale, baseline đánh giá mới và năm câu hỏi nghiên cứu trong Proposal, luồng lập luận doanh nghiệp → vấn đề → tác động → yêu cầu → giải pháp → thí nghiệm → đánh giá.
- **Sản phẩm được yêu cầu:** báo cáo, mã nguồn, slide và demo.
- **Thời hạn:** dự kiến trong 2–3 tuần cuối tháng 12/2026. Ngày nộp/bảo vệ và rubric chi tiết chưa được công bố hoặc cung cấp; cập nhật [lộ trình](PROJECT_ROADMAP.md) khi có.
- **Kiến thức nền còn phải học trong tuần 1:** đường đi của một HTTP request qua load balancer và API instances; quota theo client và local state; khác biệt giữa reject hợp lệ của rate limiter và lỗi backend. Câu hỏi tự kiểm tra và điều kiện hoàn tất nằm trong [lộ trình](PROJECT_ROADMAP.md#kiến-thức-nền-và-cách-tự-kiểm-tra-để-hoàn-tất-tuần-1).

**Hồ sơ và định hướng tuần 1 đã hoàn tất; tuần 1 tổng thể vẫn đang làm** cho đến khi qua phần tự kiểm tra kiến thức nền. Thông tin hành chính chưa có ngày chính thức được theo dõi riêng.
