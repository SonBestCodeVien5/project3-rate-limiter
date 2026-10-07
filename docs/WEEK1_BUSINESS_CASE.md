# Tuần 1 — bài toán doanh nghiệp đã chốt

**Bối cảnh được chọn:** doanh nghiệp vận hành API bán hàng trực tuyến trong đợt **flash sale**. Đây là kịch bản nghiên cứu minh họa, không phải một sự cố đã được xác minh tại một công ty. Giảng viên đã đồng ý hướng đề tài và yêu cầu thể hiện rõ vấn đề doanh nghiệp; [Proposal trên Drive](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) đã được bổ sung theo yêu cầu này. [Roadmap gốc](https://docs.google.com/document/d/1oVNMU3KTJ-dWL-3GRDb5tc9JJ75uzxaDmPf0P2yjeWA/edit) vẫn là nguồn ưu tiên cao nhất.

## Mô tả vấn đề

**Doanh nghiệp.** Một đơn vị bán hàng trực tuyến phục vụ người mua qua API. Backend chạy nhiều API instance sau load balancer để xử lý lượng truy cập lớn. Khi mở flash sale, request từ người mua và client tự động có thể tăng mạnh trong thời gian ngắn.

**Pain point.** Nếu mỗi instance giữ bộ đếm rate limit riêng, chúng không biết một client đã gửi bao nhiêu request tới các instance còn lại. Load balancer có thể phân phối request của cùng client qua nhiều instance, làm tổng request được chấp nhận vượt quota chung mà doanh nghiệp mong muốn. Ngay cả khi chuyển state sang Redis, thao tác đọc–quyết định–ghi thiếu tính atomic vẫn có thể cho phép quá mức khi nhiều request đến đồng thời.

**Tác động nghiệp vụ.** Lưu lượng vượt kiểm soát có thể làm API và database chậm hoặc lỗi. Người mua hợp lệ bị ảnh hưởng, tạo rủi ro mất giao dịch và giảm độ tin cậy của dịch vụ. Chưa có log, doanh thu hoặc SLO của một doanh nghiệp cụ thể, nên báo cáo phải trình bày đây là **rủi ro trong kịch bản giả định**, không phải thiệt hại đã đo được.

**Yêu cầu kỹ thuật.** Doanh nghiệp cần một quota chung theo client trên nhiều instance, quyết định allow/reject trước xử lý backend, giữ correctness khi request đồng thời và hạn chế chi phí latency/throughput do lớp kiểm soát thêm vào.

**Giải pháp và đánh giá.** Project 3 xây prototype nhỏ với load balancer, API instances, Redis shared state và rate limiter. So Fixed Window với Token Bucket, local state với Redis, một với nhiều instance, thao tác không atomic với atomic trong bài concurrent. Chạy tải bình thường, burst, concurrent và scaling; đo allow/reject correctness, overshoot theo policy, p50/p95/p99 latency, requests/giây và Redis CPU/memory. Kết quả phải cho thấy lợi ích bảo vệ quota cùng chi phí hiệu năng, thay vì chỉ chứng minh limiter chạy được.

**Ranh giới.** Chỉ mô phỏng API/traffic cần cho thí nghiệm; không xây đơn hàng, thanh toán hay API Gateway hoàn chỉnh. Nền tảng traffic management rộng hơn là hướng phát triển cho đồ án tốt nghiệp.

## Kết quả tuần 1 và thông tin hành chính

- **Đã chốt:** đề tài distributed rate limiting, bối cảnh flash sale, phạm vi Project 3, bốn câu hỏi nghiên cứu trong Proposal, luồng lập luận doanh nghiệp → vấn đề → tác động → yêu cầu → giải pháp → đánh giá.
- **Sản phẩm được yêu cầu:** báo cáo, mã nguồn, slide và demo.
- **Thời hạn:** dự kiến trong 2–3 tuần cuối tháng 12/2026. Ngày nộp/bảo vệ và rubric chi tiết chưa được công bố hoặc cung cấp; cập nhật [lộ trình](PROJECT_ROADMAP.md) khi có.
- **Kiến thức nền còn phải học trong tuần 1:** đường đi của một HTTP request qua load balancer và API instances; quota theo client và local state; khác biệt giữa reject hợp lệ của limiter và lỗi backend. Câu hỏi tự kiểm tra và điều kiện hoàn tất nằm trong [lộ trình](PROJECT_ROADMAP.md#kiến-thức-nền-và-cách-tự-kiểm-tra-để-hoàn-tất-tuần-1).

**Hồ sơ và định hướng tuần 1 đã hoàn tất; tuần 1 tổng thể vẫn đang làm** cho đến khi qua phần tự kiểm tra kiến thức nền. Thông tin hành chính chưa có ngày chính thức được theo dõi riêng.
