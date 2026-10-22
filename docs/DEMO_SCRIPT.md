# Demo Project3 — khoảng 6 phút

Đây là kịch bản demo prototype kèm kết quả T10 đã phân tích offline từ benchmark chính thức; saved-run UI dùng ba lượt pilot ngày 13/10. Không trình bày pilot UI như kết quả benchmark chính thức. Xem [kết quả T10](analysis/T10_RESULTS.md), [trạng thái sẵn sàng](experiments/PROTOCOL_READINESS.md) và [trạng thái công việc](REMAINING_WORK_PLAN.md). Chuẩn bị trước để không phụ thuộc tải trực tiếp trong buổi trình bày.

| Thời gian | Nội dung / thao tác |
| --- | --- |
| 0:00–0:45 | Flash sale giả định: traffic tăng, backend có năng lực giới hạn, người mua hợp lệ bị ảnh hưởng. Nêu rằng prototype mô phỏng API, không xây hệ thống bán hàng. |
| 0:45–1:30 | Vẽ luồng client → LB → API limiter → backend dùng chung; mỗi API có local state riêng, còn Redis cung cấp shared state cho các API và Lua bảo đảm atomicity. Quota tính theo key; FW và TB có cách xử lý burst khác nhau. |
| 1:30–3:00 | Mở Console, chọn bộ ba saved-run pilot none/local/Redis cùng cấu hình từ 13/10. Chỉ ra goodput/p95/p99 của client hợp lệ, 429, 5xx và request backend nhận/quá tải; nói rõ bảng UI này chỉ kiểm tra artifact/runtime pilot. Mở [bảng/kết quả T10](analysis/T10_RESULTS.md) và các hình/bảng đã lưu để trình bày kết quả benchmark chính thức. Nếu giao diện từ chối ghép lượt, giải thích nguyên nhân và mở artifact thay vì ép chấp nhận. |
| 3:00–4:00 | Mở policy/Compose đã resolve, summary/analysis và trace. Chuyển lượt để cho thấy KPI không chỉ lấy repeat1. Trạng thái oracle `inconclusive` nghĩa là chưa đủ bằng chứng kết luận; runner hoàn tất không đồng nghĩa tính đúng đã đạt. |
| 4:00–5:00 | Trình bày hai sửa lỗi lịch sử: local TB từ chối do sai số float ở biên refill và deadline socket Redis cũ. Bài kiểm tra và bằng chứng gốc được giữ nguyên. Các bước nhảy clock và việc dừng gate là quan sát lịch sử, không phải trạng thái hiện tại. |
| 5:00–6:00 | Nêu rằng T09 và phân tích offline T10 đã hoàn tất; giới hạn, oracle Fixed Window `inconclusive`, network counter Redis là tổng traffic, không có resource sampling khi outage, và các điều chưa xác minh vẫn được ghi trong kết quả. Không suy ra HA/production từ prototype mô phỏng. |

Phương án dự phòng ngoại tuyến: [kết quả T10](analysis/T10_RESULTS.md), [bảng T10](worklog/2026-10-20-t10/T10_TABLES.md), [hình đã sinh](worklog/2026-10-20-t10/figures/) và [traceability/checksum](worklog/2026-10-20-t10/README.md). Hình pilot ngày 13/10 và [CSV pilot](worklog/2026-10-13-evaluation/report/runs.csv) chỉ dùng để minh họa UI/integration, có nhãn pilot. Không cần internet; nếu Docker lỗi, mở các artifact để giải thích cấu hình, kết quả và giới hạn.

## Xem saved runs đã lưu

Ba saved runs pilot đã được restore với original IDs trong [gói T12](DEMO_PACKAGE.md): `20261013T022629-bd56e4d4e3a5` (none), `20261013T022713-1011975d376e` (local, clock/fidelity flags được giữ nguyên), và `20261013T022742-f79870fc9be7` (Redis). Chúng chỉ kiểm tra luồng UI/content pilot. Không bấm **Chạy benchmark** trong buổi trình bày.

Source package phải được kiểm tra riêng. Revision T10 `0291a80fb404fea0eafee8c3431acc3631bb423e` là revision dùng cho phép đo; nó khác revision của bộ mã Console hiện tại. Không gộp source revision đo và demo revision hoặc nói UI pilot là giao diện được chạy ở revision đo.

Tự kiểm tra trước bảo vệ: vì sao nhiều instance local làm quota tăng gấp bội? Vì sao không dùng quota FW để đo overshoot của TB? Lua có atomicity bảo đảm điều gì? 429 khác 503/timeout thế nào? Goodput của client hợp lệ dùng mẫu số nào? Vì sao bước nhảy clock làm oracle/phân pha thiếu tin cậy dù độ trễ đo bằng monotonic vẫn thấp? First success khác stable recovery thế nào? Biểu đồ nào hiện chỉ là pilot?
