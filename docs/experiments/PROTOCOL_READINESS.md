# Điều kiện chuyển sang đo chính thức — 13/10/2026

**Chưa khóa protocol, chưa chạy benchmark chính thức.** Người dùng đã cho phép tự động tiếp tục sau pilot, nhưng điều kiện đo chưa đạt. Đây là kết luận về môi trường thí nghiệm, không thay yêu cầu Roadmap/Proposal hoặc lịch do giảng viên duyệt. [Protocol ứng viên](PROTOCOL_CANDIDATE.md) vẫn là bản đề xuất.

**Cập nhật 19/10/2026:** đã tiếp tục kiểm tra chỉ đọc; [observer mới](../worklog/2026-10-19-clock/README.md) vẫn ghi nhận ba bước nhảy realtime khoảng 2,93–2,96 giây trong 90 giây. T01 chưa đạt, không chạy T03. [Helper portable](MEASUREMENT_GATE.md) đã có và qua self-check, chưa được xác nhận bằng live gate. Các điều kiện bên dưới vẫn giữ nguyên.

## Điều đã kiểm chứng

- [Calibration HTTP](../worklog/2026-10-13-calibration/README.md): 14 lượt, 7.880 sent=scheduled, 0 drops; bốn local Token Bucket trace không có violation quan sát được. Các lượt clock không ổn vẫn được giữ và đánh dấu.
- Normal 20 RPS/5 key nằm dưới quota20/key/s; backend capacity 4 / service 50 ms xử lý thành công toàn bộ request hợp lệ trong những lượt này.
- Mixed tổng120/20 RPS hợp lệ với cùng backend tạo overload khi không limiter. Đây là cấu hình hiệu chỉnh hữu ích; chưa đủ dữ liệu chính thức để kết luận độ biến thiên hoặc mode thắng.
- [Deadline Redis](../worklog/2026-10-13-redis-drops/README.md): đã tái hiện stale cache trong dependency; sửa client dùng deadline context, giữ request/dial/pool 100 ms, không tăng timeout hoặc đổi quota. Sáu net.Pipe scenarios đạt; Redis Lua/concurrency integration thật đạt sau sửa.
- [Gate sau sửa](../worklog/2026-10-13-postfix/README.md): hai normal 30 s có 600/600 success, 0 errors/drops nhưng clock residual2,606/2,629s; dừng đúng tiêu chí sau hai lần gặp cùng blocker.
- [Observer độc lập](../worklog/2026-10-13-clock/README.md): realtime nhảy hai lần khoảng 2,6 s trong90 s, monotonic vẫn đều. Quan sát trên WSL2/tsc; chưa xác định tác nhân điều chỉnh clock.

## Còn thiếu trước bộ chính thức

| Điều kiện | Trạng thái / cách hoàn tất |
| --- | --- |
| Clock ổn trong môi trường đo | Không đạt. Dùng máy/môi trường có clock ổn định, kiểm tra wall–monotonic độc lập và trên mọi trace. Không sửa timestamp để che bước nhảy. |
| Gate normal/mixed30s,3 lượt | Chưa đạt; chỉ hai normal được chạy trước dừng. Lặp đầy đủ sau xử lý môi trường, giữ tất cả lượt lỗi và tiêu chí đã đặt. |
| Burst/refill và biên FW | Local TB đã có pilot; cần phép so FW/TB/local/Redis đủ lượt và thiết kế riêng nếu kết luận burst sát biên. |
| Scaling1/2/4 và tải dưới/gần/trên ngưỡng | Chưa hiệu chỉnh sweep. Cần quota headroom, generator ổn và xác định bottleneck; không dùng tăng429 để chứng minh throughput scaling. |
| Concurrent gần cạn / atomicity control | Có tests Redis thật và đối chứng non-atomic; phải ghi rõ harness, bất biến và giới hạn trước chọn bằng chứng RQ4 cuối. |
| Outage/recovery | Chưa hiệu chỉnh trong vòng này. Chọn thời lượng, baseline khỏe và threshold recovery trước đo; không lấy first success thay stable recovery. |
| Protocol/manifest khóa | Chưa thực hiện vì các điều kiện trên. Chốt Q/W/B/r, tải, cold-start/warm-up, repetitions, validity/exclusion, thứ tự chạy và recovery sau calibration hợp lệ. |

Clock jump không chỉ ảnh hưởng deadline Redis: server dùng wall time cho quota; trace dùng timestamps để phân pha và replay. Socket mitigation không biến môi trường này thành clock ổn định. Không tăng ngưỡng5ms sau khi thấy bước nhảy2,6s, không chọn riêng lượt đẹp hoặc đổi `inconclusive` thành pass.

## Thứ tự tiếp tục

1. Xác định và ổn định clock môi trường đo hoặc chuyển sang môi trường ổn định; không thay thiết lập host trong vòng tự động hiện tại vì tác nhân chưa xác định.
2. Chạy lại gate với revision sạch, fresh state, cùng tải/timeout và tiêu chí; phát hiện clock discontinuity cả khi gửi và response drain.
3. Hiệu chỉnh các nhóm còn thiếu cho RQ1–RQ5, rồi lưu protocol version/manifest **trước** bộ chính thức.
4. Chạy tuần tự đủ lượt, giữ raw/config/counters/images/checksums và mọi lượt bị loại; xuất bảng/biểu đồ tái lập, viết kết luận theo từng RQ với giới hạn.

UI so sánh, CSV và [biểu đồ pilot](../worklog/2026-10-13-evaluation/README.md) có thể hoàn thiện độc lập. Chúng là công cụ trình bày và kiểm tra evidence, không thay điều kiện đo hoặc chứng minh correctness/scalability production.
