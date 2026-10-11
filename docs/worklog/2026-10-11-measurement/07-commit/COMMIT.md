# Commit và bàn giao

Các thay đổi được chia theo phần phụ thuộc, không ép một workflow thành một commit. Working tree đầu vòng sạch; không push.

| Commit | Phần việc |
| --- | --- |
| `dd3ccb9` | Kế hoạch công cụ đo và đánh giá scope |
| `9b91702` | Generator normal/burst/concurrent, chống dồn lịch, tests |
| `27d1d62` | Analyzer FW/TB/outage, test evidence và hợp đồng phân tích |
| `873e0ec` | Renderer topology 1/2/4 cùng backend cố định và tests |
| `ac6ac12` | Runner ma trận pilot, protocol ứng viên và verify |
| `adc82b4` | Hiệu chỉnh tải mixed sau khi phát hiện schedule backlog |

Các commit tiếp theo tách docs trạng thái/scope, worklog kiểm chứng và archive raw evidence. Lấy danh sách đầy đủ bằng `git log --oneline c859fef..HEAD`; không ghi hash tự tham chiếu của commit chứa chính file này.

Subagent bị giới hạn sử dụng khi đang tích hợp; phiên chính tiếp quản, giữ lượt bị gián đoạn và không sửa raw data thành kết quả tốt. Metadata lưu revision/dirty status thật tại thời điểm chạy; source checksums của bộ công cụ cuối được lưu cùng archive. Benchmark chính thức và việc tự học vẫn chưa được đánh dấu hoàn thành.
