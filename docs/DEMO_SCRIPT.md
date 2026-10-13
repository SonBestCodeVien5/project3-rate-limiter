# Demo Project3 — khoảng 6 phút

Đây là kịch bản demo prototype/pilot. Chưa có kết luận benchmark chính thức; xem [readiness](experiments/PROTOCOL_READINESS.md). Dùng cùng revision và artifacts đã kiểm chứng, chuẩn bị trước để không phụ thuộc tải live trong buổi trình bày.

| Thời gian | Nội dung / thao tác |
| --- | --- |
| 0:00–0:45 | Flash sale giả định: traffic tăng, backend có năng lực giới hạn, người mua hợp lệ bị ảnh hưởng. Nêu rằng prototype mô phỏng API, không xây hệ thống bán hàng. |
| 0:45–1:30 | Vẽ client → LB → API limiter→backend chung; local state riêng từng API, Redis state chung và Lua atomic. Quota theo key; FW/TB có burst semantics khác nhau. |
| 1:30–3:00 | Mở Console, chọn saved run/lượt và bảng none/local/Redis cùng cấu hình. Chỉ ra goodput/p95/p99 hợp lệ,429,5xx và backend arrivals/overload; ghi rõ số liệu pilot. Nếu UI từ chối matching, trình bày nguyên nhân và mở artifact thay vì ép pass. |
| 3:00–4:00 | Mở policy/Compose resolved, summary/analysis và trace. Chuyển lượt để chứng minh KPI không chỉ lấy repeat1; oracle inconclusive nghĩa là chưa đủ bằng chứng, runner complete không phải correctness pass. |
| 4:00–5:00 | Trình bày hai sửa lỗi: local TB float reject tại biên refill và stale Redis socket deadline. Tests và evidence gốc giữ nguyên; chỉ ra clock host vẫn nhảy nên formal gate bị dừng. |
| 5:00–6:00 | Nêu điều đã kiểm chứng, giới hạn pilot và việc còn thiếu cho RQ1–RQ5. Hướng tiếp tục: clock ổn→calibration→protocol khóa→benchmark→đánh giá; không kết luận scalability/HA production. |

Fallback offline: [biểu đồ pilot](worklog/2026-10-13-evaluation/figures/calibration.png), [CSV](worklog/2026-10-13-evaluation/report/runs.csv), raw archive và ảnh UI lưu trong worklog. Không cần internet; nếu Docker lỗi, mở artifacts để giải thích cấu hình/outcomes và giới hạn.

Tự kiểm tra trước bảo vệ: vì sao local nhiều instance nhân quota? Vì sao TB không dùng quota FW để đo overshoot? Lua atomic bảo đảm gì?429 khác503/timeout thế nào? Goodput hợp lệ dùng mẫu số nào? Vì sao clock jump làm oracle/phân pha thiếu tin cậy dù latency monotonic vẫn thấp? First success khác stable recovery thế nào? Biểu đồ nào hiện chỉ là pilot?
