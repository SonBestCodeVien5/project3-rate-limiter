# Vòng 2 — công cụ đo, đánh giá scope và học lại

Điểm bắt đầu: `c859fef`. Tiếp tục theo yêu cầu user, dùng GPT-6 Sol medium cho workload, topology và analyzer; phiên chính thống nhất contract, review giả định đo và hoàn tất khi subagent hết giới hạn sử dụng. Không mở rộng đề tài thành gateway.

| Bước | Hồ sơ | Nội dung |
| --- | --- | --- |
| Plan | [PLAN](01-plan/PLAN.md) | Phạm vi, phân công, rủi ro và điều kiện đạt |
| Code | [Workload](03-code/WORKLOAD.md), [Topology](03-code/TOPOLOGY.md), [Analyzer](03-code/ANALYZER.md) | Profile tải, 1/2/4 API, phân tích trace/outage |
| Test | [Verify đầu](04-test/verify.log), [verify cuối](06-retest/verify-final.log) | Race tests, build/vet, shell và Python |
| Review | [REVIEW](05-review/REVIEW.md) | Finding và các giới hạn claim correctness |
| Recode/retest | [RETEST](06-retest/RETEST.md) | Pilot, gián đoạn, tiếp quản, lượt có drops và chạy lại |
| Commit | [COMMIT](07-commit/COMMIT.md) | Commit theo phần nhỏ, không push |

[Đánh giá tiến độ/phạm vi](../../SCOPE_PROGRESS_2026-10-11.md) tách phần mềm đã chạy khỏi dữ liệu chính thức và năng lực tự giải thích của người học. [Trạng thái triển khai](../../IMPLEMENTATION_STATUS.md) chỉ rõ phần còn lại trước khi bảo vệ. Không dùng số tuần hoặc tốc độ sinh code làm phần trăm đồ án.
