# Demo Project3 — khoảng 6 phút

Đây là kịch bản demo prototype/pilot. Chưa có kết luận benchmark chính thức; xem [trạng thái sẵn sàng](experiments/PROTOCOL_READINESS.md). Dùng cùng revision và artifact đã kiểm chứng, chuẩn bị trước để không phụ thuộc tải trực tiếp trong buổi trình bày.

| Thời gian | Nội dung / thao tác |
| --- | --- |
| 0:00–0:45 | Flash sale giả định: traffic tăng, backend có năng lực giới hạn, người mua hợp lệ bị ảnh hưởng. Nêu rằng prototype mô phỏng API, không xây hệ thống bán hàng. |
| 0:45–1:30 | Vẽ luồng client → LB → API limiter → backend dùng chung; mỗi API có local state riêng, còn Redis cung cấp shared state cho các API và Lua bảo đảm atomicity. Quota tính theo key; FW và TB có cách xử lý burst khác nhau. |
| 1:30–3:00 | Mở Console, chọn lượt chạy đã lưu và bảng so sánh none/local/Redis có cùng cấu hình. Chỉ ra goodput/p95/p99 của client hợp lệ, 429, 5xx và số request backend nhận/quá tải; nêu rõ đây là số liệu pilot. Nếu giao diện từ chối ghép lượt, giải thích nguyên nhân và mở artifact thay vì ép chấp nhận. |
| 3:00–4:00 | Mở policy/Compose đã resolve, summary/analysis và trace. Chuyển lượt để cho thấy KPI không chỉ lấy repeat1. Trạng thái oracle `inconclusive` nghĩa là chưa đủ bằng chứng kết luận; runner hoàn tất không đồng nghĩa tính đúng đã đạt. |
| 4:00–5:00 | Trình bày hai sửa lỗi lịch sử: local TB từ chối do sai số float ở biên refill và deadline socket Redis cũ. Bài kiểm tra và bằng chứng gốc được giữ nguyên. Các bước nhảy clock và việc dừng gate là quan sát lịch sử, không phải trạng thái hiện tại. |
| 5:00–6:00 | Nêu điều đã kiểm chứng và các giới hạn còn lại. T09 đã hoàn tất; T10 chưa bắt đầu, chưa có kết luận RQ1–RQ5 và không được chạy thêm tải. Chỉ sau khi người dùng yêu cầu tiếp tục mới xem các cổng T10 trong [kế hoạch việc còn lại](REMAINING_WORK_PLAN.md); không tự chạy benchmark hoặc kết luận về khả năng mở rộng/HA ở production. |

Phương án dự phòng ngoại tuyến: [biểu đồ pilot](worklog/2026-10-13-evaluation/figures/calibration.png), [CSV](worklog/2026-10-13-evaluation/report/runs.csv), archive dữ liệu thô và ảnh UI lưu trong worklog. Không cần internet; nếu Docker lỗi, mở các artifact để giải thích cấu hình, kết quả và giới hạn.

Tự kiểm tra trước bảo vệ: vì sao nhiều instance local làm quota tăng gấp bội? Vì sao không dùng quota FW để đo overshoot của TB? Lua có atomicity bảo đảm điều gì? 429 khác 503/timeout thế nào? Goodput của client hợp lệ dùng mẫu số nào? Vì sao bước nhảy clock làm oracle/phân pha thiếu tin cậy dù độ trễ đo bằng monotonic vẫn thấp? First success khác stable recovery thế nào? Biểu đồ nào hiện chỉ là pilot?
