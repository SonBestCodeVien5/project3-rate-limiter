# Trạng thái triển khai — 13/10/2026

Theo yêu cầu tự động hóa, prototype kỹ thuật và vòng công cụ đo đã được triển khai sớm hơn lịch tuần đề xuất. Không đánh dấu thay người học hoặc biến smoke thành kết luận nghiên cứu.

| Hạng mục | Trạng thái | Bằng chứng / việc tiếp theo |
| --- | --- | --- |
| Framing doanh nghiệp | Đã có từ trước | WEEK1_BUSINESS_CASE, nguồn Roadmap/Proposal |
| Tự kiểm tra kiến thức | Chưa xác nhận | Người học tự trả lời các câu hỏi trong PROJECT_ROADMAP |
| Policy FW/TB và time semantics | Đã chọn cho prototype | IMPLEMENTATION, bảng ca test tính tay |
| Local FW/TB | Đã triển khai/test | Mutex, key độc lập, biên/refill, envelope, concurrency/race |
| Redis atomic FW/TB | Đã triển khai/test với Redis thật | Lua, Redis TIME, TTL, shared quota; non-atomic control chỉ trong test |
| API + backend + LB | Đã triển khai | Nginx, mặc định 2 API; renderer 1/2/4 API, backend dùng chung giới hạn capacity |
| Fail-open/fail-closed | Đã triển khai/test | Phân biệt 429/503/502 và timestamp fallback |
| Bộ tạo tải và raw data | Đã triển khai/test | Normal/mixed/burst theo pha/concurrent batch, JSONL/config/summary, drops/lag riêng |
| Mixed traffic/outage runners | Đã triển khai | 5 case mixed smoke, 2 fail policies; kết quả thực chạy trong RETEST |
| Scaling và analyzer | Đã triển khai/test | Render 1/2/4 API; replay/cận dưới quota theo trace, phân pha outage/recovery có điều kiện |
| Console local và custom pilot | Đã triển khai và chạy tích hợp | [Console](CONSOLE.md), [84 lượt thực chạy](worklog/2026-10-12-console-matrix/README.md); 1/2/4 API, 4 profile, FW/TB và policy/backend cấu hình được |
| Artifact/correctness của ma trận mới | Artifact đối chiếu đạt; correctness còn findings | 84 complete; 2 observed_violations, 40 inconclusive; 19 Redis errors, 5 drops; cần điều tra |
| RQ1–RQ5 chính thức | Chưa hoàn tất | Cần pilot khóa protocol, nhiều lượt lặp và phân tích độc lập |

## Việc tiếp theo sau vòng công cụ đo

1. Hiệu chỉnh và khóa protocol: warm-up/cold-start, quota, tải, thời lượng, số lượt lặp và tiêu chí loại lượt lỗi. Burst theo pha đã có; burst sát biên server cần thiết kế và xác minh riêng.
2. Ma trận tùy chỉnh 84 tổ hợp đã chạy ở topology 1/2/4; chọn các phép so sánh có kiểm soát và số lượt lặp cho RQ3. Một lượt 3 giây mỗi tổ hợp chưa chứng minh scalability.
3. Điều tra hai `token_bucket_decision_mismatch` local Token Bucket và Redis I/O timeouts của ma trận mới. Dùng analyzer để kiểm tra các trace; hoàn thiện quota violation dưới fail-open khi state/response không xác định, độ đồng bộ clock và mức quan sát cần để xác nhận cửa sổ đầy đủ. Không đổi `inconclusive` thành pass khi thiếu evidence.
4. Chạy benchmark chính thức lặp đủ số lần, phân tích biến thiên và bottleneck, xuất biểu đồ/tables tái lập. Chọn tiêu chí recovery trước khi đo, không chọn sau khi thấy kết quả đẹp.
5. Học lại theo commit/test, viết báo cáo/slide, diễn tập demo và tự giải thích; cập nhật ngày/rubric với giảng viên.

Xem [hồ sơ vòng đo](worklog/2026-10-11-measurement/README.md), [protocol ứng viên](experiments/PILOT_PROTOCOL.md), [hợp đồng analyzer](experiments/ANALYSIS.md) và [ước lượng tiến độ/phạm vi](SCOPE_PROGRESS_2026-10-11.md). Các việc còn lại có phụ thuộc phương pháp nghiên cứu; code/test hoàn thành không đồng nghĩa RQ1–RQ5 hoặc việc học đã hoàn tất. Console local hiện là công cụ demo tùy chọn; Redis Cluster, gateway hoặc nghiệp vụ bán hàng nằm ngoài phạm vi.
