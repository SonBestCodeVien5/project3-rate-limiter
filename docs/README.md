# Hướng dẫn đọc tài liệu Project 3

Đây là mục lục dành cho người học và người viết báo cáo. Phần giải thích trong các tài liệu hiện hành dùng tiếng Việt; tên thuật toán, lệnh, mã định danh và trường dữ liệu giữ nguyên để đối chiếu với mã nguồn. Không cần đọc toàn bộ thư mục `docs/` theo thứ tự tên tệp.

**Mốc đối chiếu 20/10/2026:** T09 đã thu thập đủ 138/138 lượt dự kiến, tổng hợp đủ 46/46 cấu hình thí nghiệm. T10 chưa bắt đầu, chưa có kết luận RQ1–RQ5; đang dừng trước T10. Đủ dữ liệu để tổng hợp không đồng nghĩa đã chứng minh tính đúng của quota. Trạng thái và điều kiện tiếp tục được theo dõi trong [kế hoạch công việc](REMAINING_WORK_PLAN.md) và [điều kiện đo](experiments/PROTOCOL_READINESS.md).

## Đọc lần đầu

1. [Bối cảnh doanh nghiệp](WEEK1_BUSINESS_CASE.md): vì sao cần đề tài, tác động giả định và ranh giới nghiên cứu.
2. [Roadmap nguồn](context/sources/00_Project3_Roadmap.md), rồi [đề xuất đề tài](context/sources/01_Project3_Proposal.md): yêu cầu và câu hỏi nghiên cứu. Các bản trong repo là ghi chú rút gọn; [chỉ mục nguồn](context/SOURCE_INDEX.md) dẫn tới bản gốc trên Drive.
3. [Lộ trình học và bảo vệ](PROJECT_ROADMAP.md): các mốc đề xuất và phần tự kiểm tra kiến thức; lịch này chưa phải hạn nộp chính thức.
4. [Công việc còn lại](REMAINING_WORK_PLAN.md): trạng thái T01–T13/H01–H02, phụ thuộc và điểm dừng hiện tại. Các khối lệnh giao việc bằng tiếng Anh ở đây dành cho agent, có thể bỏ qua khi đọc.

## Chọn theo việc đang làm

| Nhu cầu | Tài liệu nên đọc | Dùng để làm gì |
| --- | --- | --- |
| Hiểu hệ thống và thuật toán | [Thiết kế triển khai](IMPLEMENTATION.md) | Đường đi yêu cầu, quy tắc quota, thời gian, tính nguyên tử và giới hạn |
| Hiểu phương pháp thí nghiệm | [Đặc tả](experiments/EXPERIMENT_SPEC.md) → [điều kiện đo hiện tại](experiments/PROTOCOL_READINESS.md) | Phân biệt yêu cầu, thiết kế ban đầu và quy trình đã khóa |
| Hiểu số liệu có nghĩa gì | [Quy tắc phân tích](experiments/ANALYSIS.md) → [xuất số liệu báo cáo](experiments/REPORTING.md) | Cách kiểm chứng quota, mẫu số, tổng hợp lượt lặp và giới hạn diễn giải |
| Viết báo cáo | [Bản nháp báo cáo](REPORT_DRAFT.md) và bảng bên dưới | Viết phần đã có căn cứ; để kết luận chờ T10 |
| Chuẩn bị thuyết trình/demo | [Kịch bản demo](DEMO_SCRIPT.md) → [hướng dẫn Console](CONSOLE.md) | Trình tự trình bày và cách dùng dữ liệu đã lưu |
| Chạy hoặc sửa công cụ khi được yêu cầu | [README dự án](../README.md) → [hướng dẫn script](../scripts/README.md), [cổng kiểm tra chất lượng đo](experiments/MEASUREMENT_GATE.md) | Tra lệnh và điều kiện chạy; lệnh minh họa không cấp quyền chạy thí nghiệm |

## Dùng tài liệu để viết báo cáo

Viết theo mạch: vấn đề doanh nghiệp → khó khăn → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → hướng phát triển. Không chép toàn bộ nhật ký công việc thành chương báo cáo.

| Phần báo cáo | Nơi lấy nội dung | Điều cần giữ rõ |
| --- | --- | --- |
| Bài toán, khó khăn, tác động | [Bối cảnh doanh nghiệp](WEEK1_BUSINESS_CASE.md) | Flash sale là kịch bản giả định; chưa có thiệt hại doanh nghiệp được đo |
| Yêu cầu và câu hỏi nghiên cứu | [Roadmap nguồn](context/sources/00_Project3_Roadmap.md), [đề xuất](context/sources/01_Project3_Proposal.md) | Tách yêu cầu dự án khỏi lựa chọn kỹ thuật và hướng mở rộng |
| Thiết kế giải pháp | [Thiết kế triển khai](IMPLEMENTATION.md) | Nêu quyết định triển khai, khác biệt giữa các nguồn và giới hạn mô hình |
| Phương pháp và khả năng tái lập | [Điều kiện đo](experiments/PROTOCOL_READINESS.md), [quy tắc phân tích](experiments/ANALYSIS.md) | Dẫn đúng phiên bản quy trình/manifest đã khóa, revision và cấu hình thực chạy |
| Bảng, hình và đánh giá RQ1–RQ5 | [Hướng dẫn xuất số liệu](experiments/REPORTING.md), [bản nháp](REPORT_DRAFT.md) | Chờ T10 được tiếp tục; mỗi kết luận cần truy về lượt đo, bằng chứng và giới hạn |
| Phụ lục và truy nguyên | Các hồ sơ `worklog/` được dẫn trong [điều kiện đo](experiments/PROTOCOL_READINESS.md) | Giữ mã lượt đo, checksum và bằng chứng gốc; không dùng pilot thay kết quả chính thức |

## Thuật ngữ dùng thống nhất

Tên Fixed Window (FW), Token Bucket (TB), Redis, API, HTTP và Console giữ nguyên. Các từ sau được giải thích bằng tiếng Việt khi xuất hiện trong văn bản; tên trường trong dữ liệu vẫn giữ nguyên.

| Thuật ngữ | Cách hiểu trong tài liệu |
| --- | --- |
| rate limiter, quota | Bộ giới hạn lưu lượng; hạn mức yêu cầu được chấp nhận |
| client, request, backend | Bên gửi yêu cầu; yêu cầu; thành phần xử lý phía sau bộ giới hạn |
| API instance | Một tiến trình API đang chạy; nhiều instance có thể nằm trên cùng một máy |
| local/shared state | Trạng thái cục bộ ở từng API / trạng thái dùng chung qua Redis |
| atomicity | Tính nguyên tử của thao tác đọc–quyết định–ghi |
| policy | Bộ quy tắc và tham số áp dụng cho quyết định quota |
| workload, burst | Mẫu tải; đợt yêu cầu dồn dập trong thời gian ngắn |
| baseline, pilot, calibration | Mốc đối chứng hoặc phạm vi tối thiểu tùy ngữ cảnh; lượt thử sơ bộ; hiệu chỉnh phép đo |
| cell, run, slot | Một cấu hình thí nghiệm; một lượt thực chạy; một vị trí lượt đo dự kiến trong kế hoạch |
| goodput | Tốc độ yêu cầu hợp lệ được phục vụ thành công, theo mẫu số/thời gian đã định |
| latency, throughput, p95/p99 | Độ trễ; thông lượng; phân vị 95/99 của độ trễ trong tập mẫu đã xác định |
| oracle, inconclusive | Bộ quy tắc kiểm chứng tính đúng; chưa đủ bằng chứng kết luận, không phải đạt |
| overshoot | Số yêu cầu được chấp nhận vượt hạn mức; có thể chỉ đo được cận dưới |
| fail-open / fail-closed | Cho đi tiếp / từ chối khi không kiểm tra được quota do lỗi Redis |
| outage, recovery | Khoảng gián đoạn Redis; phục hồi theo tiêu chí đã khóa, khác với thành công đầu tiên |
| artifact, manifest, revision | Tệp bằng chứng; danh sách/cấu hình phép đo; phiên bản mã nguồn Git |
| trace | Dấu vết từng yêu cầu và quyết định, dùng để kiểm tra lại số đo |

## Chỉ tra khi cần

Các tài liệu dưới đây không nằm trong lộ trình đọc thường xuyên và được phép giữ tiếng Anh. Giữ nguyên đường dẫn hiện có để các liên kết và bằng chứng vẫn truy nguyên được.

- **Hướng dẫn và bộ nhớ cho agent:** [AGENTS.md](../AGENTS.md), [tóm tắt phiên](context/PROJECT_BRIEF.md), [checkpoint](context/SESSION_CHECKPOINT.md), `.agents/skills/`. Người học dùng kế hoạch công việc thay cho việc đọc toàn bộ checkpoint.
- **Nguồn yêu cầu rút gọn:** [chỉ mục nguồn](context/SOURCE_INDEX.md) và `context/sources/`. Không dịch lại chỉ để đồng bộ ngôn ngữ; bản Drive là nguồn có thẩm quyền cho nguyên văn và chi tiết thiếu.
- **Hồ sơ lịch sử:** [đánh giá phạm vi 08/10](SCOPE_REASSESSMENT_2026-10-08.md), [tiến độ 11/10](SCOPE_PROGRESS_2026-10-11.md), [kế hoạch Console cũ](DEMO_CONSOLE_PLAN.md), [trạng thái triển khai 13/10](IMPLEMENTATION_STATUS.md), [quy trình pilot cũ](experiments/PILOT_PROTOCOL.md), [bản quy trình ứng viên](experiments/PROTOCOL_CANDIDATE.md), cùng các nhật ký có ngày trong `worklog/`. Trạng thái trong đó chỉ đúng tại mốc đã ghi.
- **Quy trình đã khóa và dữ liệu cho máy:** `experiments/protocol-v*/`, JSON/JSONL/CSV, checksum, log và kho bằng chứng. Không dịch hay sửa tại chỗ các tệp này; muốn giải thích cho báo cáo thì viết trong tài liệu hiện hành và dẫn về bản gốc.
