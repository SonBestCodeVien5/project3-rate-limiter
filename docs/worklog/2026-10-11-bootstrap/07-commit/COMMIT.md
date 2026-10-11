# Commit nhỏ theo phần phụ thuộc

User yêu cầu không gộp một vòng workflow vào một commit. Các phần đã test/review được stage riêng theo chức năng; không tạo commit chứa bug đã biết chỉ để giả lập lịch sử sửa. Review và retest giữ lịch sử phát hiện thật ở thư mục tương ứng.

| Commit | Phạm vi |
| --- | --- |
| `8c7a2a2` | Phân tích repo và kế hoạch triển khai |
| `a1cec8b` | Module Go, policy, local FW/TB và tests |
| `a631389` | Redis Lua FW/TB, integration/correctness và non-atomic control |
| `8033b47` | HTTP API, backend giới hạn, fail policies, metrics và tests |
| `c2c8d66` | Load generator, raw data/metadata/summary và tests |
| `dacb841` | Docker/Compose/Nginx testbed |
| `b3f3be2` | Workflow verify/pilot/outage, cleanup tests và hướng dẫn |

Các commit tiếp theo tách hướng dẫn/trạng thái triển khai, hồ sơ review/test, và raw evidence. Dùng `git log --oneline 1bcb44e..HEAD` để lấy đầy đủ hash, tránh ghi chính hash của file đang được commit.

## Kiểm tra trước commit

- Working tree ban đầu sạch; không có thay đổi của người dùng bị ghi đè.
- Stage path cụ thể; `git diff --cached --check` trước từng commit.
- Race tests, Redis thật, build, Compose, 5 mixed smoke và 2 outage smoke đã PASS.
- Raw artifacts đang ở `artifacts/` (gitignored), bản archive/checksum chọn lọc được lưu trong worklog để theo báo cáo.
- Chỉ commit local trên nhánh hiện tại `main`; không push hoặc sửa nguồn Google Drive.

Các commit code đã hoàn tất; trạng thái cuối được kiểm tra bằng `git status --short` sau commit evidence. Giới hạn nghiên cứu còn lại ở `docs/IMPLEMENTATION_STATUS.md`, không đóng giả các cổng tự kiểm tra kiến thức hoặc protocol chính thức.
