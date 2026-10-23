# Công việc còn lại và trạng thái Project 3

**Hiện trạng 23/10/2026:** T09/T10 đã hoàn tất. T11 đã tích hợp bản nháp; định dạng cuối/rubric còn chờ. T12 demo/source đã kiểm tra; T13 chưa có PowerPoint. P2-01 hoàn tất; P2-02 là gói kế tiếp nhưng chưa được yêu cầu. Phiên hiện tại chỉ cho phép tài liệu: không có quyền chạy tải, stack, smoke runtime hay Redis outage.

## Việc đang chờ

| Việc | Trạng thái | Điều kiện tiếp theo |
| --- | --- | --- |
| T11 báo cáo | Bản nháp có kết quả RQ1–RQ5; chưa phải bản nộp cuối | Nhận rubric/feedback, hoàn tất nguồn và định dạng |
| T13 slide/bảo vệ | Có nội dung slide; Canva trả HTTP 429, chưa có deck hoặc buổi diễn tập | Tạo deck theo template khi Canva/giải pháp dựng dùng được; kiểm tra format và diễn tập |
| H01 kiến thức | Người học chưa xác nhận tự kiểm tra | Tự trả lời câu hỏi trong [lộ trình học/bảo vệ](PROJECT_ROADMAP.md) |
| H02 hành chính | Ngày chính thức, rubric và yêu cầu hình thức còn chờ | Xác nhận với giảng viên; không suy đoán hoặc tự gửi liên hệ |
| P2 | P2-01 xong; P2-02 chưa bắt đầu | Xem [sổ P2](monitoring/PHASE2_PLAN.md); cần yêu cầu mới cho G1. G2–G4 chưa được cấp |

T09/T10 không có lượt đo nào đang mở. Đừng chạy lại hoặc ghép telemetry P2 vào bằng chứng nghiên cứu. Cổng và protocol đo ở [readiness](experiments/PROTOCOL_READINESS.md); chỉ mở [checkpoint](context/SESSION_CHECKPOINT.md) khi cần revision, artifact hoặc kiểm tra của phiên trước.

## Baseline và bằng chứng theo task

Giữ phạm vi: Fixed Window/Token Bucket; local/Redis shared state; concurrency và scaling; mixed legitimate/abusive traffic để đo backend protection; một Redis outage ngắn với fail-open/fail-closed. Sliding Window và dashboard là tùy chọn. Nguồn ưu tiên Roadmap > Proposal > Research Context > Positioning; protocol kỹ thuật không phải rubric của trường.

| ID | Phụ thuộc | Công việc và trạng thái | Bằng chứng, giới hạn hoặc bước tiếp theo |
| --- | --- | --- | --- |
| T01 | — | Môi trường clock ổn định — **đạt trong phiên** | Observer sau remediation không ghi nhận step >5 ms; UTC accuracy và restart/resume durability chưa xác minh. [Gate T02/T03](worklog/2026-10-19-measurement-gate/README.md). |
| T02 | Song song T01 | Observer/runner/checker lifecycle — **hoàn tất** | Revision, output và checksum trong [gate worklog](worklog/2026-10-19-measurement-gate/README.md). |
| T03 | T01–T02 | Gate normal/mixed — **pilot gate đạt giới hạn** | FW oracle `inconclusive`, không phải correctness pass hay formal benchmark. Cùng [gate worklog](worklog/2026-10-19-measurement-gate/README.md). |
| T04 | T03 | Hiệu chỉnh normal/burst FW/TB và none — **hoàn tất có giới hạn** | FW inconclusive, một lượt không kết luận hiệu năng. [Worklog](worklog/2026-10-19-calibration-next/README.md). |
| T05 | T03 | Hiệu chỉnh scaling 1/2/4 — **hoàn tất có giới hạn** | Backend chung giới hạn suy luận; chưa chứng minh mode/API scaling nào tốt hơn. [Worklog](worklog/2026-10-19-calibration-next/T05-README.md). |
| T06 | T03 | Atomicity/concurrency — **hoàn tất bằng tests** | Lua quota và non-atomic forced-race control; không suy tần suất race tự nhiên/performance HTTP. Test-source hash và uncommitted-patch caveat tại [T06 worklog](worklog/2026-10-19-atomicity/README.md) và [T10 results](analysis/T10_RESULTS.md). |
| T07 | T03 | Redis outage runner/recovery — **bounded calibration hoàn tất** | Stable recovery 4s theo tiêu chí đã khóa; first success riêng, FW inconclusive. Không suy thành HA production. [Worklog](worklog/2026-10-19-outage-recovery/README.md). |
| T08 | T04–T07 | Protocol/manifest — **khóa protocol v1** | T09 dùng [v1.2](experiments/protocol-v1.2/protocol.md) và [manifest](experiments/protocol-v1.2/manifest.json); [v1.3 addendum](experiments/protocol-v1.3/protocol.md) chỉ bổ sung slot thiếu được cho phép. [T08 worklog](worklog/2026-10-19-t08-network/README.md). |
| T09 | T08 | Formal measurement — **hoàn tất** | 138/138 slot, 46/46 cấu hình; một lượt v1.3 bổ sung slot thiếu. Measurement source: `0291a80fb404fea0eafee8c3431acc3631bb423e`. [T09 evidence/checksums](worklog/2026-10-20-t09-v1.3/README.md). Không chạy thêm tải. |
| T10 | T09 | Offline RQ1–RQ5 analysis — **hoàn tất** | 138 lượt/46 cấu hình, 11 hình. FW correctness inconclusive; Redis network counter là tổng traffic; outage không có resource sampling; backend mô phỏng; UTC accuracy/restart-resume và generalization chưa xác minh. [Kết quả](analysis/T10_RESULTS.md); [tái lập/checksum](worklog/2026-10-20-t10/README.md). |
| T11 | T10 | Tích hợp kết quả vào báo cáo — **bản nháp hoàn tất** | Có bảng/hình chọn lọc, caption và traceability; rubric/feedback, nguồn bổ sung và format cuối còn chờ. Không xác nhận sẵn sàng nộp. [Bản nháp](REPORT_DRAFT.md). |
| T12 | T09–T10 | Demo/source — **gói kỹ thuật hoàn tất** | Clean checkout, ba saved pilot IDs/hash, UI compare và fallback T10. Demo source khác measurement source; xem [gói](DEMO_SCRIPT.md) và [worklog/checksum](worklog/2026-10-22-t12/README.md). |
| T13 | T10–T12 | Slide, diễn tập, bộ nộp — **đang chờ** | [Nội dung nháp](slides/project3-defense.md), [checklist](DEMO_SCRIPT.md); template HUST đã nhận, Canva import trả HTTP 429 trước design ID. Chưa có deck, rehearsal hoặc final tag. |
| H01 | Song song | Người học tự kiểm tra kiến thức — **chờ người học** | Tự giải thích thuật toán, quota local/shared, atomicity, metrics và giới hạn; AI không tự đánh dấu đã hiểu. |
| H02 | Người học/giảng viên | Ngày/rubric/yêu cầu hình thức — **chờ xác nhận** | Mốc giữa tháng 12/2026 chỉ là tạm tính; xác nhận ngày chính thức và rubric với giảng viên. |

## Khi tiếp tục

- Gói kỹ thuật P2 tiếp theo là **P2-02** (Compose overlay, Prometheus/Grafana, provisioning); cần yêu cầu mới bao phủ G1. Đọc [sổ P2](monitoring/PHASE2_PLAN.md) và đúng phần [design](monitoring/DESIGN.md), [runbook](monitoring/RUNBOOK.md) hoặc [learning guide](monitoring/LEARNING_GUIDE.md). Không tự bắt đầu sau điểm dừng.
- Các hướng dẫn cũ cho T01–T10 không cần lặp lại. Nếu có finding mới, bắt đầu từ worklog được dẫn trong bảng và readiness; giữ raw evidence, manifest, checksum, revision và mọi lượt không hợp lệ.
- Báo cáo giữ mạch bài toán doanh nghiệp → pain point → impact → yêu cầu → solution → experiment → evaluation → future work; tách giả định khỏi kết quả, pilot khỏi formal evidence, và `inconclusive` khỏi pass.

Lệnh chạy, setup demo và hướng dẫn runner nằm ở [DEMO_SCRIPT](DEMO_SCRIPT.md), [scripts README](../scripts/README.md) và [runbook P2](monitoring/RUNBOOK.md). Những ví dụ đó không cấp quyền chạy. Quy tắc phiên/commit ở [AGENTS.md](../AGENTS.md).
