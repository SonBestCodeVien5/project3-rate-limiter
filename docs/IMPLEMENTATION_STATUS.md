# Trạng thái triển khai — 13/10/2026

> **Con trỏ trạng thái hiện tại (20/10/2026):** Tài liệu này ghi tình trạng triển khai ngày 13/10 và các vòng kỹ thuật thời điểm đó; đây không phải trạng thái đo lường hiện tại. T09 đã thu thập đủ dữ liệu (138/138 vị trí chạy dự kiến dùng được, 46/46 cấu hình đã tổng hợp); gói archive/checksum cuối đã bàn giao. T10 chưa bắt đầu và chưa có kết luận RQ1–RQ5. Không chạy thêm tải; dừng trước T10. Xem [kế hoạch phần việc còn lại](REMAINING_WORK_PLAN.md) và [checkpoint](context/SESSION_CHECKPOINT.md).

**Vòng tự động tiếp theo:** [calibration 14 lượt](worklog/2026-10-13-calibration/README.md) có 7.880 sent=scheduled / 0 drops và xác nhận runtime local TB sau sửa. [Deadline Redis](worklog/2026-10-13-redis-drops/README.md) đã tái hiện/sửa, giữ deadline 100 ms; sáu net.Pipe scenarios và Redis Lua/concurrency integration thật đạt. [Gate sau sửa](worklog/2026-10-13-postfix/README.md) dừng sau hai 30 s normal vì clock nhảy, dù 600/600 success / 0 Redis errors mỗi lượt. [Observer độc lập](worklog/2026-10-13-clock/README.md) xác nhận realtime nhảy khoảng 2,6 s trên WSL2. [Console comparison](worklog/2026-10-13-console-content/README.md) đạt trên dữ liệu thật, guard workload/layers và mobile; [biểu đồ/report pilot](worklog/2026-10-13-evaluation/README.md), [demo script](DEMO_SCRIPT.md) đã có. [Protocol chưa khóa](experiments/PROTOCOL_READINESS.md); benchmark chính thức/RQ1–RQ5 vẫn chưa hoàn tất. Các đoạn dưới giữ lịch sử các vòng trước.

Theo yêu cầu tự động hóa, prototype kỹ thuật và vòng công cụ đo đã được triển khai sớm hơn lịch tuần đề xuất. Không đánh dấu thay người học hoặc biến smoke thành kết luận nghiên cứu.

**Vòng hoàn thiện 13/10:** [điều tra Token Bucket](worklog/2026-10-13-token-bucket/README.md) xác nhận và sửa sai số float tại biên refill local, kèm regression; chưa pilot lại HTTP. Console đã thêm chọn lượt lặp, trạng thái oracle và lỗi limiter tổng mọi API. Có [protocol ứng viên](experiments/PROTOCOL_CANDIDATE.md) để xem xét, chưa duyệt/chưa khóa. Kết quả ma trận lịch sử bên dưới vẫn giữ nguyên; Redis timeouts, generator drops và benchmark chính thức còn mở.

Kiểm chứng vòng hoàn thiện: `bash scripts/verify.sh` đạt (vet, race tests gồm HTTP localhost, build, runner/cleanup, 3 topology tests, 17 analyzer tests); `node internal/console/index_test.js` đạt 3 tests. Subagent kiểm tra giao diện desktop/mobile bằng fixture; không phải benchmark Docker mới. Checksum archive gốc không đổi.

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
| Artifact/correctness của ma trận mới | Giữ nguyên findings lịch sử; có sửa lỗi/pilot mới | TB float và Redis deadline đã xử lý; ma trận84 không viết lại. Clock host, generator scheduling và bộ đo chính thức còn mở |
| RQ1–RQ5 chính thức | Chưa hoàn tất | Cần pilot khóa protocol, nhiều lượt lặp và phân tích độc lập |

## Việc tiếp theo sau vòng công cụ đo

1. Hiệu chỉnh và khóa protocol: warm-up/cold-start, quota, tải, thời lượng, số lượt lặp và tiêu chí loại lượt lỗi. Burst theo pha đã có; burst sát biên server cần thiết kế và xác minh riêng.
2. Ma trận tùy chỉnh 84 tổ hợp đã chạy ở topology 1/2/4; chọn các phép so sánh có kiểm soát và số lượt lặp cho RQ3. Một lượt 3 giây mỗi tổ hợp chưa chứng minh scalability.
3. LocalTB float và deadline Redis dùng cache thời gian cũ đã có sửa lỗi/test/evidence mới; tiếp theo ổn định clock môi trường và hiệu chỉnh generator/sampler khi cần. Hoàn thiện quota violation dưới fail-open khi state/response không xác định và mức quan sát cho cửa sổ đầy đủ. Không đổi `inconclusive` thành pass khi thiếu evidence.
4. Chạy benchmark chính thức lặp đủ số lần, phân tích biến thiên và bottleneck, xuất biểu đồ/tables tái lập. Chọn tiêu chí recovery trước khi đo, không chọn sau khi thấy kết quả đẹp.
5. Học lại theo commit/test, viết báo cáo/slide, diễn tập demo và tự giải thích; cập nhật ngày/rubric với giảng viên.

Xem [hồ sơ vòng đo](worklog/2026-10-11-measurement/README.md), [protocol ứng viên](experiments/PILOT_PROTOCOL.md), [hợp đồng analyzer](experiments/ANALYSIS.md) và [ước lượng tiến độ/phạm vi](SCOPE_PROGRESS_2026-10-11.md). Các việc còn lại có phụ thuộc phương pháp nghiên cứu; code/test hoàn thành không đồng nghĩa RQ1–RQ5 hoặc việc học đã hoàn tất. Console local hiện là công cụ demo tùy chọn; Redis Cluster, gateway hoặc nghiệp vụ bán hàng nằm ngoài phạm vi.
