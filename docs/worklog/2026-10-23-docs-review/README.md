# Rà soát trạng thái và đường đọc tài liệu — 23/10/2026

## Phạm vi và căn cứ

Người dùng yêu cầu rà tài liệu và các điểm chỉ dẫn khác trong repo, đồng bộ với P2-01 đã có, đồng thời tổ chức lại đường đọc nếu cần. Revision đầu phiên: `17e10cd`; implementation P2-01: `0bea7b2`. Phiên này chỉ sửa tài liệu/chỉ dẫn, không tiếp tục P2-02 hoặc chạy ứng dụng.

Root điều phối ba gói Luna có ownership tách biệt: hướng dẫn người đọc, tài liệu kỹ thuật và context cho agent. Root kiểm kê repo, tích hợp các finding cụ thể, kiểm tra liên kết toàn repo và staged diff, ghi bàn giao và commit. Không worker nào commit hoặc tạo agent khác.

## Kiểm kê và mức rà soát

Kiểm kê **106 Markdown files đã tracked đầu phiên**; không hiểu con số này là đã kiểm định lại mọi dữ liệu nghiên cứu:

| Nhóm | Số file đầu phiên | Cách xử lý |
| --- | ---: | --- |
| Tài liệu hiện hành cho người đọc | 24 | Rà mục đích, trạng thái, điểm tiếp tục và navigation; sửa nơi sai hoặc khó tìm |
| Chỉ dẫn/context cho agent | 4 | Kiểm tra routing; rút brief, cập nhật AGENTS/checkpoint; skill sync không cần đổi |
| Chỉ mục và ghi chú nguồn | 5 | Giữ nguyên; đọc chỉ mục/Roadmap theo quy định, không reconnect hoặc sync Drive |
| Protocol đã khóa | 4 | Giữ nguyên nội dung và đường dẫn |
| Markdown bằng chứng/nhật ký có ngày | 63 | Kiểm kê, kiểm tra liên kết; không đọc lại toàn bộ raw evidence, chạy lại analysis hoặc sửa hồ sơ cũ |
| Hướng dẫn/đề xuất lịch sử ngoài worklog | 6 | Thêm nhãn lịch sử và link hiện hành; giữ nguyên thân tài liệu gốc |

Các hướng dẫn hiện hành đã rà nhưng không cần đổi: `docs/REPORT_DRAFT.md`, `docs/analysis/T10_RESULTS.md`, `docs/experiments/ANALYSIS.md`, `docs/DEMO_PACKAGE.md`, `scripts/README.md`. Không tạo thay đổi chỉ để mọi file đều có dòng P2 mới.

Các điểm chỉ dẫn ngoài nhóm tài liệu thông thường được kiểm tra bằng inventory/search: `AGENTS.md`, `.agents/skills/sync-project-context/SKILL.md`, README ở root, đường dẫn runner/Console và tên project. Không có code/config cần đổi chỉ để đồng bộ trạng thái.

## Những chỗ gây nhầm đã xử lý

- `IMPLEMENTATION.md`, `PROJECT_ROADMAP.md`, `EXPERIMENT_SPEC.md`, `MEASUREMENT_GATE.md` còn nói T10 chưa bắt đầu; hướng dẫn đọc T10 còn nói T11 chưa được yêu cầu; `REPORTING.md` còn ghi T11 đang dừng. Đã đưa về kết quả T10 có sẵn và T11 tích hợp bản nháp, còn định dạng/rubric.
- README, reader index, remaining plan và runbook còn mô tả P2 chỉ có tài liệu. Đã phân biệt endpoint P2-01 đã triển khai với Compose/provisioning/scrape/runtime chưa có. Điểm tiếp theo vẫn P2-02.
- Mốc cuối tháng 12 trong business case không còn khớp mốc lập kế hoạch tạm do người dùng chọn ngày 19/10. Đã thống nhất **giữa tháng 12/2026**, vẫn ghi chưa có ngày nộp/bảo vệ chính thức.
- Sáu tài liệu lịch sử có thể mở trực tiếp từ search nhưng mang câu “hiện tại”, “tiếp theo” hoặc trỏ protocol v1. Thêm wrapper nêu rõ đó là phát biểu ở mốc lịch sử; không sửa nội dung ghi nhận bên dưới hoặc chuyển file evidence.
- Brief chứa nhiều lịch sử làm phiên sau phải nạp thừa context. Active brief còn **415 từ**, so với **1.665 từ** đầu phiên, giảm khoảng **75%**; phần lịch sử từ marker giai đoạn chuẩn bị P2 được giữ nguyên văn trong `docs/context/PROJECT_BRIEF_HISTORY.md` cùng thư mục để các relative links vẫn đúng.

## Tổ chức sau khi rà

- [Reader index](../../README.md) là điểm vào cho người học, với ba đường đọc: hiểu đề tài, học monitoring, chuẩn bị báo cáo/demo. Các bảng tra cứu, thuật ngữ và nhóm có thể bỏ qua nằm phía sau.
- [Remaining plan](../../REMAINING_WORK_PLAN.md) hiển thị việc còn lại trước; hồ sơ baseline dài và hướng dẫn T01–T10 đã hoàn tất nằm trong phần thu gọn. [Sổ P2](../../monitoring/PHASE2_PLAN.md) vẫn là nơi duy nhất quản lý chi tiết task P2.
- [Brief](../../context/PROJECT_BRIEF.md) chỉ giữ context hoạt động; [lịch sử brief](../../context/PROJECT_BRIEF_HISTORY.md) là tài liệu agent-only, không đọc mặc định. [Checkpoint](../../context/SESSION_CHECKPOINT.md) giữ revision/checks/điểm dừng.
- Không mass rename/move tài liệu, không tạo thêm status dashboard/file trạng thái song song, không cần skill mới. Giữ đường dẫn report, protocol và artifact hiện có.

## Kiểm tra và giới hạn

- Workers kiểm tra local links, whitespace, phần sửa và bảo toàn command blocks. Phần thân sáu tài liệu lịch sử và tail brief được kiểm tra bảo toàn nguyên văn so với revision đầu phiên.
- Root kiểm tra **794 liên kết nội bộ trên 108 Markdown files** sau khi thêm archive/biên bản, không có liên kết thiếu đích; kiểm tra staged diff trước mỗi commit, bảo toàn code/command blocks và phạm vi chỉ có Markdown. Không sửa source notes, protocol đã khóa, kết quả T10, code/config hoặc worklog cũ.
- Không chạy code suite, build, browser, Docker/service, Prometheus parser, load/outage, clock/resource observation, tái sinh analysis/figures, Drive sync hoặc push. Kiểm tra liên kết nội bộ không chứng minh URL ngoài repo còn truy cập được hay stack chạy được.

## Commit và điểm tiếp tục

`76486c6` sửa trạng thái trong hướng dẫn kỹ thuật; `acff27d` đơn giản hóa navigation và tách context lịch sử. Biên bản này, checkpoint và chỉnh nhãn checklist P2-01 được commit riêng như phần bàn giao.

P2-01 vẫn xong kỹ thuật với giới hạn parser/runtime đã ghi; **P2-02 chưa bắt đầu**. Chỉ triển khai khi người dùng tiếp tục phạm vi tương ứng. T09/T10 và mọi giới hạn giữ nguyên; T11 bản nháp chưa phải bản nộp, T13 chưa có deck, xác nhận kiến thức/rubric/ngày chính thức vẫn còn chờ.
