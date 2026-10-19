# Điều kiện chuyển sang đo chính thức — 13/10/2026

**Chưa khóa protocol, chưa chạy benchmark chính thức. Phiên đã dừng sau T05 theo yêu cầu người dùng; T07 để phiên sau.** Không tự động tiếp tục thí nghiệm trước khi người dùng yêu cầu. Đây là kết luận về môi trường thí nghiệm, không thay yêu cầu Roadmap/Proposal hoặc lịch do giảng viên duyệt. [Protocol ứng viên](PROTOCOL_CANDIDATE.md) vẫn là bản đề xuất.

**Cập nhật 19/10/2026:** T01 ổn định trong phiên hiện tại. Observer mới không ghi nhận step >5 ms; sau đó bounded gate T03 hoàn tất cả sáu lượt normal/mixed, không có quality flag hay generator drop. Xem [T02/T03 worklog](../worklog/2026-10-19-measurement-gate/README.md). Oracle Fixed Window vẫn inconclusive do window chỉ quan sát một phần. T04 normal/burst và T05 scaling calibration đã hoàn tất, T06 tests atomicity đã đạt; T07 recovery calibration còn thiếu. Gate/calibration không khóa protocol hoặc thay benchmark chính thức.

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
| Clock ổn trong môi trường đo | Ổn định trong phiên hiện tại: observer mới 90 giây không có step >5 ms; trace residual ở từng lượt cũng đạt. Độ chính xác UTC tuyệt đối và độ bền sau restart/resume chưa xác minh; chạy lại observer nếu không rõ tính liên tục của phiên. |
| Gate normal/mixed30s,3 lượt | **Pilot gate có giới hạn đã đạt:** 3 normal + 3 mixed, không quality flag/drop. Oracle FW inconclusive; chưa chứng minh correctness. |
| Burst/refill và biên FW | **T04 calibration đạt:** 10 normal/burst cells, mỗi cell 1 lượt 30 giây, zero drop/quality flag; [evidence](../worklog/2026-10-19-calibration-next/README.md). FW vẫn inconclusive ở partial windows; không có đồng bộ sát biên, nên không kết luận burst tại biên hoặc hiệu năng chính thức từ một lượt. |
| Scaling1/2/4 và tải dưới/gần/trên ngưỡng | **T05 calibration đạt:** 27 valid cells, 43.200 sent; một drop được thay cùng cấu hình và ba interruptions được giữ. 0 429/limiter errors trong valid runs, quota headroom; backend giới hạn khoảng 190 success/s ở 250 RPS. [Evidence](../worklog/2026-10-19-calibration-next/T05-README.md); không kết luận API scaling hoặc mode thắng từ các lượt đơn. |
| Concurrent gần cạn / atomicity control | **T06 hoàn tất:** tests Redis thật shared quota và gần cạn cho FW/TB đạt; đối chứng non-atomic ép race. [Evidence](../worklog/2026-10-19-atomicity/README.md) ghi harness, checksum và giới hạn; không suy tần suất race tự nhiên hoặc hiệu năng HTTP. |
| Outage/recovery | **T07 chưa đạt:** preliminary capacity4 baseline overload, recovery inconclusive và recorded dirty observer status. Fix cleanup/schema/healthy gate đạt 4 mocked tests; còn live matched capacity10 cases + exporter smoke. [Evidence và bước tiếp](../worklog/2026-10-19-outage/README.md). First success không thay stable recovery. |
| Network counters | [Chuẩn bị](../worklog/2026-10-19-network/README.md) qua 20 tests offline; chưa live-validate. Tổng byte gồm sampler/admin, không phải limiter bytes/request hay wire overhead. |
| Protocol/manifest khóa | Chưa thực hiện vì các điều kiện trên. Chốt Q/W/B/r, tải, cold-start/warm-up, repetitions, validity/exclusion, thứ tự chạy và recovery sau calibration hợp lệ. |

Clock jump không chỉ ảnh hưởng deadline Redis: server dùng wall time cho quota; trace dùng timestamps để phân pha và replay. Socket mitigation không biến môi trường này thành clock ổn định. Không tăng ngưỡng5ms sau khi thấy bước nhảy2,6s, không chọn riêng lượt đẹp hoặc đổi `inconclusive` thành pass.

## Thứ tự tiếp tục

1. Giữ nguyên giới hạn clock và chạy lại observer trước phép đo live nếu không rõ tính liên tục của phiên; không sửa timestamp để che step.
2. Chỉ sau khi người dùng tiếp tục: hoàn tất T07 capacity10 recovery + exporter smoke, rồi live-validate network counters; giữ mọi lượt lỗi cùng quality flag.
3. Khóa protocol có version và manifest **trước** benchmark chính thức.
4. Chạy manifest tuần tự, giữ raw/config/counter/image/checksum và lượt lỗi; sau đó tạo bảng/hình tái lập và kết luận RQ có giới hạn rõ.

UI so sánh, CSV và [biểu đồ pilot](../worklog/2026-10-13-evaluation/README.md) có thể hoàn thiện độc lập. Chúng là công cụ trình bày và kiểm tra evidence, không thay điều kiện đo hoặc chứng minh correctness/scalability production.
