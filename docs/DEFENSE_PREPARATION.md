# Chuẩn bị bảo vệ Project 3

Đây là checklist dự thảo gắn với [nội dung slide](slides/project3-defense.md). Template HUST đã nhận; Canva import bị chặn HTTP 429 trước khi có design ID, nên deck chưa được tạo. Nội dung chờ đưa vào Canva khi thao tác khả dụng. Trạng thái task nằm trong [kế hoạch còn lại](REMAINING_WORK_PLAN.md); cổng đo ở [protocol readiness](experiments/PROTOCOL_READINESS.md). Chưa có buổi tập dượt thực tế và tài liệu này không đánh dấu đã sẵn sàng nộp/bảo vệ.

## Trước buổi tập dượt

- Mở [DEMO_SCRIPT.md](DEMO_SCRIPT.md) và [DEMO_PACKAGE.md](DEMO_PACKAGE.md); chuẩn bị fallback T10 ngoại tuyến. Saved-run UI dùng pilot, không gọi là formal.
- Mở trước [T10 results](analysis/T10_RESULTS.md), [bảng mixed](worklog/2026-10-20-t10/T10_TABLES.md) và các hình đã có; không tái sinh figure.
- Kiểm tra links tới protocol/manifest v1.2, phụ lục v1.3, traceability, provenance và T06 worklog.

## Khi trình bày

- Mạch kể: business problem → pain point → impact giả định → yêu cầu kỹ thuật → giải pháp → experiment → evaluation → future work.
- Tách rõ yêu cầu dự án, lựa chọn engineering của prototype và tùy chọn tương lai.
- Nhắc n=3, median (min–max), đơn vị; không diễn giải thành confidence interval hay significance.
- Giữ rõ các giới hạn: FW `inconclusive`; Redis network là tổng traffic; outage không resource sampling; backend mô phỏng; UTC accuracy/restart-resume chưa xác minh.
- Tách T06 revision/test hash/uncommitted patch caveat khỏi measurement revision `0291a80fb404fea0eafee8c3431acc3631bb423e`.

## Câu hỏi tự kiểm tra

Trả lời không nhìn ghi chú: tại sao local state có thể cộng quota qua nhiều API? Lua atomicity chứng minh điều gì và không chứng minh điều gì? 429 khác backend overload/503/timeout ra sao? Vì sao backend mô phỏng làm giới hạn kết luận scaling? Stable recovery khác first success thế nào? Saved-run UI nào là pilot?

Rubric, feedback giảng viên, ngày chính thức, nguồn tham khảo học thuật cuối cùng, H01 và tập dượt của người học còn pending. Chưa đánh dấu hoàn tất trước khi có căn cứ tương ứng.
