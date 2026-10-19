# Điều kiện chuyển sang đo chính thức — cập nhật 19/10/2026

**T08 đã hoàn tất: network sampler được live-validate và protocol v1 đã khóa. T09 benchmark chưa được phép chạy và chưa chạy.** Chờ người dùng yêu cầu tiếp tục trước bất kỳ tải formal nào. Đây là kế hoạch đo kỹ thuật, không thay yêu cầu Roadmap/Proposal hoặc lịch do giảng viên duyệt. Bản ứng viên vẫn là lịch sử; dùng [protocol v1](protocol-v1/protocol.md) và [manifest](protocol-v1/manifest.json) làm phiên bản khóa.

**Cập nhật 19/10/2026:** T01 ổn định trong phiên hiện tại. Observer mới không ghi nhận step >5 ms; sau đó bounded gate T03 hoàn tất cả sáu lượt normal/mixed, không có quality flag hay generator drop. Xem [T02/T03 worklog](../worklog/2026-10-19-measurement-gate/README.md). Oracle Fixed Window vẫn inconclusive do window chỉ quan sát một phần. T04 normal/burst và T05 scaling calibration đã hoàn tất, T06 tests atomicity đã đạt; T07 capacity10 recovery calibration và exporter smoke cũng đã hoàn tất. Calibration không thay benchmark chính thức; protocol v1 lock T08 is recorded below.

**Trạng thái T08:** user-authorized bounded validation passed on clean source `b090d2b7391db873a0a2bbe602321ed1f5a55691`; initial lifecycle and launcher/no-sampler attempts remain preserved and excluded. Protocol lock commit `157770f`, evidence commit `2d333c9`, sampler fix/test commit `b090d2b`. The v1 manifest covers 46 cells and 138 planned slots and leaves execution unauthorized. See [T08 worklog](../worklog/2026-10-19-t08-network/README.md). Redis network counters are total traffic including sampler/admin/health checks/workload, not limiter-only bytes/request; cadence and paired overhead limits are documented. No formal benchmark or final RQ conclusion follows. If a future user resumption begins a load session and continuity is uncertain, collect a fresh clock observer first.

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
| Outage/recovery | **T07 calibration đạt:** 4 clean-revision capacity10 cases × 30s, zero drops, healthy gates đạt, stable recovery 4s theo 1s/min5/3 windows; exporter smoke 4/4 usable với null-resource fix riêng. [Evidence](../worklog/2026-10-19-outage-recovery/README.md). FW correctness vẫn inconclusive; first success riêng; một lượt mỗi policy/phase không thay benchmark chính thức. |
| Network counters | **T08 live validation passed within limits**; [worklog](../worklog/2026-10-19-t08-network/README.md). TERM completion and byte deltas/units checked; matched API pair preserved request fidelity. Total Redis traffic includes sampler/admin/health-check/workload; one pair does not calibrate overhead correction or latency/CPU attribution. |
| Protocol/manifest khóa | **Locked:** [v1 protocol](protocol-v1/protocol.md), [46-cell manifest](protocol-v1/manifest.json), source `b090d2b7391db873a0a2bbe602321ed1f5a55691`. Execution remains unauthorized pending explicit user resumption. |

Clock jump không chỉ ảnh hưởng deadline Redis: server dùng wall time cho quota; trace dùng timestamps để phân pha và replay. Socket mitigation không biến môi trường này thành clock ổn định. Không tăng ngưỡng5ms sau khi thấy bước nhảy2,6s, không chọn riêng lượt đẹp hoặc đổi `inconclusive` thành pass.

## Thứ tự tiếp tục

1. Wait for explicit user resumption before T09; readiness documentation does not authorize a workload.
2. If continuity is uncertain in the resumed measurement session, run a fresh clock observer before load; do not alter thresholds or timestamps.
3. Execute only the locked v1 manifest sequentially, retaining raw/config/counter/image/checksum and invalid attempts under its bounded replacement/stop rules.
4. After authorized data collection, create reproducible tables/figures and assess RQs with the protocol's stated limits.

UI so sánh, CSV và [biểu đồ pilot](../worklog/2026-10-13-evaluation/README.md) có thể hoàn thiện độc lập. Chúng là công cụ trình bày và kiểm tra evidence, không thay điều kiện đo hoặc chứng minh correctness/scalability production.
