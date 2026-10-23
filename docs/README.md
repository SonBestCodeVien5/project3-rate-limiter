# Hướng dẫn đọc tài liệu Project 3

Không cần đọc toàn bộ `docs/`. Mốc hiện tại (23/10/2026): T09/T10 hoàn tất; T11 đã tích hợp bản nháp, còn định dạng cuối/rubric chờ; T12 đã kiểm tra gói demo; T13 chưa có deck. P2-01 đã thêm endpoint Prometheus; P2-02 đã hoàn tất overlay/provisioning và kiểm tra tĩnh G1, chưa kiểm chứng runtime. P2-03 là gói kế tiếp, cần yêu cầu mới bao phủ dashboard và G2. Chi tiết ở [kế hoạch baseline](REMAINING_WORK_PLAN.md), [sổ P2](monitoring/PHASE2_PLAN.md) và [cổng đo](experiments/PROTOCOL_READINESS.md).

## Chọn đường đọc

- **Đường đọc chính:** [lộ trình học và tự kiểm tra](PROJECT_ROADMAP.md) → [ngữ nghĩa triển khai](IMPLEMENTATION.md) → [kết quả trong bản nháp](REPORT_DRAFT.md) → [kịch bản trình bày](DEMO_SCRIPT.md).
- **Tài liệu tra theo nhu cầu:** [bối cảnh và tự kiểm tra](PROJECT_ROADMAP.md); [kết quả và cách đọc T10](analysis/T10_RESULTS.md); [nội dung slide](slides/project3-defense.md). Kịch bản demo chứa phần chuẩn bị kỹ thuật và câu hỏi bảo vệ.
- **Tra công cụ:** [Console](CONSOLE.md) hướng dẫn giao diện/saved runs; [scripts README](../scripts/README.md) hướng dẫn runner, kiểm tra và exporter.
- **Học monitoring:** bắt đầu ở [lộ trình học P2](monitoring/LEARNING_GUIDE.md); xem [sổ P2](monitoring/PHASE2_PLAN.md) để biết gói hiện hành, rồi tra phần liên quan trong [thiết kế](monitoring/DESIGN.md). Chỉ dùng [runbook](monitoring/RUNBOOK.md) cho hoạt động đã được cho phép.
- **Tiếp tục công việc:** [kế hoạch baseline](REMAINING_WORK_PLAN.md) quản lý T01–T13/H01–H02; [sổ P2](monitoring/PHASE2_PLAN.md) quản lý P2-00–P2-08. Trạng thái đo và protocol hiện hành ở [readiness](experiments/PROTOCOL_READINESS.md).

Yêu cầu gốc: [Roadmap nguồn](context/sources/00_Project3_Roadmap.md) > [Proposal](context/sources/01_Project3_Proposal.md) > tài liệu bổ trợ; [chỉ mục nguồn](context/SOURCE_INDEX.md) dẫn tới bản Drive có thẩm quyền. Roadmap repo là lịch học đề xuất, không phải hạn chính thức.

## Khi viết báo cáo

Giữ mạch **bài toán doanh nghiệp → pain point → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → hướng phát triển**. Flash sale là giả định, không phải thiệt hại đã đo. Tách yêu cầu nguồn, lựa chọn kỹ thuật và hướng mở rộng; phân biệt pilot với evidence chính thức và `inconclusive` với pass. Các kết luận RQ1–RQ5 cùng giới hạn nằm trong [T10 results](analysis/T10_RESULTS.md); truy nguyên số liệu qua protocol, revision và artifacts được dẫn ở đó.

## Thuật ngữ cần phân biệt

| Thuật ngữ | Nghĩa trong dự án |
| --- | --- |
| local/shared state | Trạng thái riêng từng API / trạng thái dùng chung qua Redis |
| atomicity | Thao tác quota không bị xen ngang thành chuỗi đọc–quyết định–ghi rời rạc |
| offered load / goodput | Tải đưa vào / tốc độ phục vụ thành công cho client hợp lệ |
| pilot / benchmark | Lượt thử sơ bộ / phép đo theo protocol đã khóa |
| measurement slot / run | Vị trí lượt đo dự kiến / lượt chạy thực tế |
| fail-open / fail-closed | Cho request đi tiếp / từ chối khi Redis không kiểm tra được quota |
| inconclusive | Chưa đủ bằng chứng kết luận; không được tính là pass |
| first success / stable recovery | Thành công đầu tiên / phục hồi đạt tiêu chí ổn định đã định |

## Có thể bỏ qua khi đọc lần đầu

- **Tài liệu lịch sử:** các guide lịch sử đã loại khỏi luồng đọc; dated worklogs và evidence vẫn được giữ để truy nguyên. Không cần đọc khi bắt đầu.
- **Nguồn yêu cầu:** [chỉ mục nguồn](context/SOURCE_INDEX.md) dẫn Roadmap trước, rồi các ghi chú rút gọn Roadmap/Proposal/Research Context/Positioning trong `context/sources/`. Drive là nguồn có thẩm quyền nếu cần nguyên văn, chi tiết thiếu hoặc freshness.
- **Chỉ dành cho agent:** [AGENTS.md](../AGENTS.md), [brief hiện hành](context/PROJECT_BRIEF.md), [brief history](context/PROJECT_BRIEF_HISTORY.md), [checkpoint](context/SESSION_CHECKPOINT.md) và `.agents/skills/`. Người học không cần đọc nhóm này.
- **Dữ liệu/archive:** protocol đã khóa, CSV/JSON, trace và checksum giữ nguyên để truy nguyên; đọc qua các hướng dẫn hiện hành, không sửa archive.
