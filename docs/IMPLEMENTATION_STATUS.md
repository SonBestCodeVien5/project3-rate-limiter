# Trạng thái triển khai — 11/10/2026

Theo yêu cầu tự động hóa, prototype kỹ thuật được triển khai sớm hơn lịch tuần đề xuất. Không đánh dấu thay người học hoặc biến smoke thành kết luận nghiên cứu.

| Hạng mục | Trạng thái | Bằng chứng / việc tiếp theo |
| --- | --- | --- |
| Framing doanh nghiệp | Đã có từ trước | WEEK1_BUSINESS_CASE, nguồn Roadmap/Proposal |
| Tự kiểm tra kiến thức | Chưa xác nhận | Người học tự trả lời các câu hỏi trong PROJECT_ROADMAP |
| Policy FW/TB và time semantics | Đã chọn cho prototype | IMPLEMENTATION, bảng ca test tính tay |
| Local FW/TB | Đã triển khai/test | Mutex, key độc lập, biên/refill, envelope, concurrency/race |
| Redis atomic FW/TB | Đã triển khai/test với Redis thật | Lua, Redis TIME, TTL, shared quota; non-atomic control chỉ trong test |
| API + backend + LB | Đã triển khai | 2 API, Nginx, backend dùng chung giới hạn capacity |
| Fail-open/fail-closed | Đã triển khai/test | Phân biệt 429/503/502 và timestamp fallback |
| Bộ tạo tải và raw data | Đã triển khai/test | Open-loop đều theo lịch, JSONL/config/summary, drops/lag riêng |
| Mixed traffic/outage runners | Đã triển khai | 5 case mixed smoke, 2 fail policies; kết quả thực chạy trong RETEST |
| RQ1–RQ5 chính thức | Chưa hoàn tất | Cần pilot khóa protocol, nhiều lượt lặp và phân tích độc lập |

## Phần tự động hóa tiếp theo sau prototype

1. Khóa workload/protocol: warm-up, reset, số client, quota, burst theo pha/biên, tải và số lượt lặp; cần đánh giá generator đạt offered load.
2. Mở ma trận scaling 1/2/n API qua cấu hình, giữ backend không đổi; Compose hiện dựng cố định 2 API. Kiểm chứng local nhiều instance hiện có bằng unit test và smoke 2 API.
3. Tạo analyzer trace: FW theo key/window server, TB theo oracle/thứ tự hoặc invariant phù hợp; phân tích pre/during/post outage, quota violation và recovery theo tiêu chí đã khóa.
4. Đo normal, burst, concurrent, scaling lặp đủ số lần, phân tích Redis CPU/memory/network và sai lệch; không gọi snapshots CPU counter là phần trăm CPU.
5. Viết báo cáo/slide dựa trên dữ liệu đã khóa, nêu giới hạn mô hình backend và identity tin cậy.

Các việc này là bước nghiên cứu tiếp theo có phụ thuộc protocol, không phải giả định đã đạt chỉ vì code chạy. Không thêm dashboard, Redis Cluster, gateway hoặc nghiệp vụ bán hàng.
