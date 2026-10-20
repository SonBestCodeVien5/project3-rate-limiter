# Tuần 1 — bài toán doanh nghiệp đã chốt

**Bối cảnh được chọn:** doanh nghiệp vận hành API bán hàng trực tuyến trong đợt **flash sale**. Đây là kịch bản nghiên cứu minh họa, không phải một sự cố đã được xác minh tại một công ty. Giảng viên đã đồng ý hướng đề tài và yêu cầu thể hiện rõ vấn đề doanh nghiệp; [Proposal trên Drive](https://docs.google.com/document/d/1Z1N6JJPsmAolE4UiOvVVONA-g32LCQosSt7WlyvSwdE/edit) đã được bổ sung theo yêu cầu này. [Roadmap gốc](https://docs.google.com/document/d/1oVNMU3KTJ-dWL-3GRDb5tc9JJ75uzxaDmPf0P2yjeWA/edit) vẫn là nguồn ưu tiên cao nhất.

## Mô tả vấn đề

**Doanh nghiệp.** Một đơn vị bán hàng trực tuyến phục vụ người mua qua API. Hệ thống phía sau chạy nhiều tiến trình API sau bộ cân bằng tải để xử lý lượng truy cập lớn. Khi mở flash sale, yêu cầu từ người mua và các chương trình tự động có thể tăng mạnh trong thời gian ngắn.

**Điểm nghẽn.** Nếu mỗi tiến trình API giữ bộ đếm giới hạn lưu lượng riêng, nó không biết một client đã gửi bao nhiêu yêu cầu tới các tiến trình API còn lại. Bộ cân bằng tải có thể phân phối yêu cầu của cùng client qua nhiều tiến trình, khiến tổng số yêu cầu được chấp nhận vượt hạn mức chung mà doanh nghiệp mong muốn. Ngay cả khi chuyển trạng thái sang Redis, thao tác đọc–quyết định–ghi nếu không được thực hiện nguyên tử vẫn có thể cho phép vượt hạn mức khi nhiều yêu cầu đến đồng thời.

**Tác động nghiệp vụ.** Lưu lượng vượt kiểm soát có thể làm API và database chậm hoặc lỗi. Người mua hợp lệ bị ảnh hưởng, tạo rủi ro mất giao dịch và giảm độ tin cậy của dịch vụ. Chưa có log, doanh thu hoặc SLO của một doanh nghiệp cụ thể, nên báo cáo phải trình bày đây là **rủi ro trong kịch bản giả định**, không phải thiệt hại đã đo được.

**Yêu cầu kỹ thuật.** Doanh nghiệp cần một hạn mức chung theo client trên nhiều tiến trình API, quyết định cho phép hay từ chối trước khi xử lý ở backend, giữ đúng hạn mức khi yêu cầu đến đồng thời, hạn chế chi phí về độ trễ/thông lượng và duy trì khả năng phục vụ client hợp lệ khi client khác tạo tải bất thường. Khi Redis không khả dụng, prototype cần có hành vi cho qua hoặc từ chối được xác định rõ để đo sự đánh đổi giữa hạn mức và khả năng phục vụ.

**Giải pháp và đánh giá.** Project 3 xây prototype nhỏ với bộ cân bằng tải, nhiều tiến trình API, Redis dùng chung trạng thái và bộ giới hạn lưu lượng. So sánh Fixed Window với Token Bucket, trạng thái cục bộ với Redis, một tiến trình với nhiều tiến trình, thao tác không nguyên tử với thao tác nguyên tử trong bài thử đồng thời. Chạy tải bình thường, đột biến, đồng thời, mở rộng quy mô và mẫu tải hỗn hợp gồm client hợp lệ cùng client tạo tải đột biến. So sánh không giới hạn, giới hạn cục bộ và Redis dùng chung trên cùng tải/backend; đo số yêu cầu hợp lệ được xử lý thành công mỗi giây, p95/p99 độ trễ của client hợp lệ, yêu cầu tới backend, phản hồi 429, timeout/5xx, cùng với tính đúng, mức vượt hạn mức, thông lượng và CPU/bộ nhớ Redis. Thử ngắt Redis ngắn để so sánh chính sách cho qua/từ chối theo khả năng phục vụ, vi phạm hạn mức và thời gian phục hồi. Kết quả cần đánh giá mức bảo vệ backend và chi phí/đánh đổi, không chỉ xác nhận bộ giới hạn chạy được.

**Ranh giới.** Chỉ mô phỏng API/lưu lượng cần cho thí nghiệm; không xây chức năng đơn hàng, thanh toán, Redis Cluster, hệ thống sẵn sàng cao cho môi trường vận hành thực tế hay API Gateway hoàn chỉnh. Nền tảng quản lý lưu lượng rộng hơn là hướng phát triển cho đồ án tốt nghiệp.

## Kết quả tuần 1 và thông tin hành chính

- **Đã chốt:** đề tài distributed rate limiting, bối cảnh flash sale, baseline đánh giá mới và năm câu hỏi nghiên cứu trong Proposal, luồng lập luận doanh nghiệp → vấn đề → tác động → yêu cầu → giải pháp → thí nghiệm → đánh giá.
- **Sản phẩm được yêu cầu:** báo cáo, mã nguồn, slide và demo.
- **Thời hạn:** dự kiến trong 2–3 tuần cuối tháng 12/2026. Ngày nộp/bảo vệ và rubric chi tiết chưa được công bố hoặc cung cấp; cập nhật [lộ trình](PROJECT_ROADMAP.md) khi có.
- **Kiến thức nền còn phải học trong tuần 1:** đường đi của một HTTP request qua load balancer và API instances; quota theo client và local state; khác biệt giữa reject hợp lệ của limiter và lỗi backend. Câu hỏi tự kiểm tra và điều kiện hoàn tất nằm trong [lộ trình](PROJECT_ROADMAP.md#kiến-thức-nền-và-cách-tự-kiểm-tra-để-hoàn-tất-tuần-1).

**Hồ sơ và định hướng tuần 1 đã hoàn tất; tuần 1 tổng thể vẫn đang làm** cho đến khi qua phần tự kiểm tra kiến thức nền. Thông tin hành chính chưa có ngày chính thức được theo dõi riêng.
