# Hồ sơ triển khai 11/10/2026

Lượt làm theo yêu cầu tự động plan → code → test → review → recode/retest → commit. Mục tiêu là prototype đo được và bằng chứng tái lập, chưa phải bộ kết quả nghiên cứu cuối kỳ.

| Bước | Hồ sơ | Nội dung phục vụ báo cáo |
| --- | --- | --- |
| 01 Analysis | [REPO_ANALYSIS](01-analysis/REPO_ANALYSIS.md) | Trạng thái đầu vào, yêu cầu, khoảng trống, khác biệt nguồn |
| 02 Plan | [PLAN](02-plan/PLAN.md) | Quyết định triển khai và tiêu chí đạt |
| 03 Code | [IMPLEMENTATION](03-code/IMPLEMENTATION.md) | Kiến trúc, chính sách, tổ chức mã |
| 04 Test | [TEST_LOG](04-test/TEST_LOG.md) | Lần kiểm thử đầu và bằng chứng thô |
| 05 Review | [REVIEW](05-review/REVIEW.md) | Finding độc lập, mức độ và giới hạn |
| 06 Recode/retest | [RETEST](06-retest/RETEST.md) | Sửa finding, kiểm tra lại, smoke/pilot |
| 07 Commit | [COMMIT](07-commit/COMMIT.md) | Phạm vi commit và cách tìm phiên bản |

Khi viết báo cáo: vấn đề doanh nghiệp → pain point → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → phát triển tương lai. Trích đúng loại bằng chứng: unit test không phải benchmark; smoke không phải protocol đã khóa; lỗi quota cố ý trong đối chứng không phải hành vi của bản atomic.
