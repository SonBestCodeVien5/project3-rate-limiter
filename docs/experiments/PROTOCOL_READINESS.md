# Điều kiện chuyển sang đo chính thức — cập nhật 20/10/2026

**T09 đã hoàn tất; dừng trước T10.** Theo [phụ lục một vị trí lượt dự kiến v1.3](protocol-v1.3/protocol.md) đã cam kết trước, cấu hình còn thiếu `p1-129-scale-redis-fw-1api-250rps-r3` đã qua checker v1.2 cố định: gửi 7,500/7,500, không có request bị bỏ, 250 RPS, p95 schedule lag 1.15658 ms, clock residual 0.001790 ms và fingerprint khớp. Oracle tính đúng Fixed Window vẫn chưa đủ bằng chứng kết luận. Bản xuất dẫn xuất đã sửa có 138/138 vị trí lượt dự kiến dùng được và 46/46 cấu hình tổng hợp, gồm cả bốn cấu hình outage. Protocol/manifest v1.2 và bằng chứng trước đó không đổi. Mã nguồn đo `0291a80fb404fea0eafee8c3431acc3631bb423e`; SHA-256 manifest v1.2 `8fdee2bee729665327fd0d5e03b89a4fd4d10bfed4dc872a82bd5ddf649acb1e`; commit phụ lục v1.3 `e0f02867343fbea93d399b9a17229ed813867452`. Bộ quan sát trước tải 90 giây đạt (1,789 mẫu, không có bước nhảy trên 5 ms); các gate mã nguồn/image đã ghim đều đạt. Xem [bàn giao bằng chứng v1.3](../worklog/2026-10-20-t09-v1.3/README.md) và [SHA256SUMS](../worklog/2026-10-20-t09-v1.3/SHA256SUMS); SHA-256 archive `c947c8b9633b82c71e49ee473255c6db1a2431909d0a6342fa23fd798ecb150c`, giải nén/kiểm tra checksum/dọn dẹp đều đạt. Không chạy thêm tải; dừng trước T10. T10 chưa bắt đầu và chưa có kết luận RQ. Các giới hạn T08 về tổng lưu lượng Redis, độ chính xác UTC/độ bền sau restart-resume và backend mô phỏng vẫn còn.

**Trạng thái hiện tại (20/10/2026):** T09 đã hoàn tất; các hướng dẫn chạy pilot bên dưới chỉ là ghi nhận lịch sử. T10 chưa bắt đầu, chưa có kết luận RQ và không được chạy thêm tải. Xem [kế hoạch việc còn lại](../REMAINING_WORK_PLAN.md) để biết cổng tiếp theo sau khi người dùng yêu cầu tiếp tục.

**Cập nhật 19/10/2026 (ghi nhận lịch sử):** T01 ổn định trong phiên làm việc khi đó. Observer không ghi nhận bước nhảy trên 5 ms; bounded gate T03 hoàn tất sáu lượt normal/mixed, không có cờ chất lượng hay request bị generator bỏ. Xem [worklog T02/T03](../worklog/2026-10-19-measurement-gate/README.md). Oracle Fixed Window chưa đủ bằng chứng kết luận vì chỉ quan sát một phần window. T04 hiệu chỉnh normal/burst, T05 hiệu chỉnh scaling, T06 kiểm thử tính nguyên tử, T07 hiệu chỉnh recovery capacity10 và kiểm tra smoke của exporter cũng đã hoàn tất. Các lần hiệu chỉnh không thay benchmark chính thức; T08 khóa protocol v1 như ghi bên dưới.

**Trạng thái T08/T09:** Kiểm chứng giới hạn của T08 và các giới hạn về tổng lưu lượng Redis được ghi trong [worklog T08](../worklog/2026-10-19-t08-network/README.md). Bằng chứng smoke T09 nằm trong [worklog smoke](../worklog/2026-10-20-t09-smoke/README.md); provenance chính thức v1.2 và v1.3 được dẫn ở trên. Chưa có kết luận RQ. Giới hạn về độ chính xác UTC, độ bền clock sau restart/resume và backend mô phỏng vẫn còn.

## Bằng chứng lịch sử đã kiểm chứng

- [Hiệu chỉnh HTTP](../worklog/2026-10-13-calibration/README.md): 14 lượt, 7.880 request gửi=đã lên lịch, không có request bị bỏ; bốn trace Token Bucket local không ghi nhận vi phạm. Các lượt có clock bất ổn vẫn được lưu và đánh dấu.
- Normal 20 RPS/5 key thấp hơn quota 20 mỗi key mỗi giây; backend capacity 4/service 50 ms xử lý thành công toàn bộ request hợp lệ trong các lượt này.
- Với mixed tổng 120/hợp lệ 20 RPS và cùng backend, không limiter tạo quá tải. Đây là cấu hình hiệu chỉnh hữu ích, nhưng chưa đủ dữ liệu chính thức để kết luận độ biến thiên hoặc mode nào tốt hơn.
- [Deadline Redis](../worklog/2026-10-13-redis-drops/README.md): stale cache trong dependency đã được tái hiện; client được sửa để dùng deadline theo context, giữ giới hạn request/dial/pool 100 ms và không tăng timeout hay đổi quota. Sáu kịch bản net.Pipe đạt; tích hợp Redis Lua/concurrency thật cũng đạt sau sửa.
- [Gate sau sửa](../worklog/2026-10-13-postfix/README.md): hai lượt normal 30 giây có 600/600 thành công, không có lỗi hay request bị bỏ, nhưng clock residual là 2,606/2,629 giây; gate dừng đúng tiêu chí sau khi cùng vấn đề xuất hiện hai lần.
- [Observer độc lập](../worklog/2026-10-13-clock/README.md): realtime nhảy hai lần khoảng 2,6 giây trong 90 giây, còn monotonic đều. Quan sát thực hiện trên WSL2/tsc; chưa xác định tác nhân điều chỉnh clock.

## Cổng và giới hạn trong lịch sử đo

| Điều kiện | Trạng thái / cách hoàn tất |
| --- | --- |
| Clock trong môi trường đo | Ổn định trong phiên đã quan sát: observer 90 giây mới không ghi nhận bước nhảy >5 ms; độ lệch trace từng lượt cũng đạt. Độ chính xác UTC tuyệt đối và độ bền sau restart/resume chưa xác minh. Nếu không rõ phiên có liên tục hay không thì cần observer mới trước khi đo tiếp. |
| Gate normal/mixed, 30 giây × 3 | **Pilot gate giới hạn đã đạt:** 3 lượt normal + 3 mixed, không có cờ chất lượng hoặc request bị bỏ. Oracle FW chưa đủ bằng chứng kết luận; đây không phải bằng chứng tính đúng. |
| Burst/refill và biên FW | **T04 hiệu chỉnh đạt:** 10 cấu hình normal/burst, mỗi cấu hình một lượt 30 giây, không có request bị bỏ hay cờ chất lượng; [bằng chứng](../worklog/2026-10-19-calibration-next/README.md). FW vẫn chưa đủ bằng chứng kết luận ở các cửa sổ một phần. Không đồng bộ sát biên, nên một lượt không đủ để kết luận về burst tại biên hay hiệu năng chính thức. |
| Scaling 1/2/4 và tải dưới/gần/trên ngưỡng | **T05 hiệu chỉnh đạt:** 27 cấu hình hợp lệ, 43.200 request gửi; một lượt có request bị bỏ được thay bằng lượt cùng cấu hình, còn ba lần gián đoạn vẫn được giữ. Không có 429/lỗi limiter trong các lượt hợp lệ; quota còn dư. Backend giới hạn ở khoảng 190 thành công/giây khi tải 250 RPS. [Bằng chứng](../worklog/2026-10-19-calibration-next/T05-README.md); không kết luận về scaling API hay mode thắng dựa trên các lượt đơn. |
| Tải concurrent gần cạn/đối chứng tính nguyên tử | **T06 hoàn tất:** kiểm thử Redis thật về quota dùng chung và gần cạn cho FW/TB đạt; đối chứng không nguyên tử chủ động ép xảy ra race. [Bằng chứng](../worklog/2026-10-19-atomicity/README.md) ghi harness, checksum và giới hạn; không suy ra tần suất race tự nhiên hoặc hiệu năng HTTP. |
| Ngắt Redis/phục hồi | **T07 hiệu chỉnh đạt:** 4 ca capacity10 ở revision sạch × 30 giây, không có request bị bỏ, các gate khi Redis khỏe đạt; recovery ổn định sau 4 giây theo tiêu chí cửa sổ 1 giây/tối thiểu 5 mẫu/3 cửa sổ. Exporter smoke có 4/4 ca dùng được sau một sửa lỗi riêng để xử lý resource null. [Bằng chứng](../worklog/2026-10-19-outage-recovery/README.md). Oracle FW chưa đủ bằng chứng kết luận; thành công đầu tiên được báo riêng. Một lượt mỗi policy/pha không thay benchmark chính thức. |
| Bộ đếm mạng | **T08 kiểm chứng trực tiếp đạt trong giới hạn đã nêu**; xem [worklog](../worklog/2026-10-19-t08-network/README.md). Đã kiểm tra hoàn tất TERM và delta/đơn vị byte; cặp API khớp giữ đúng độ trung thực request. Tổng lưu lượng Redis gồm sampler/admin/health-check/mẫu tải. Một cặp không đủ để hiệu chỉnh phần chi phí phụ hoặc quy độ trễ/CPU cho từng nguồn. |
| Protocol/manifest đã khóa | **v1.2 và phụ lục một vị trí lượt dự kiến v1.3:** [protocol v1.2](protocol-v1.2/protocol.md), [manifest](protocol-v1.2/manifest.json), [phụ lục v1.3](protocol-v1.3/protocol.md). Ma trận/ngưỡng v1.2 không đổi. Lượt v1.3 được phép đã đạt; cả 138 vị trí lượt dự kiến được chấp nhận và 46 cấu hình được tổng hợp. Archive/checksum và dọn dẹp đã được kiểm chứng. |

Các bước nhảy clock lịch sử ảnh hưởng deadline Redis; server cũng dùng wall time cho quota, còn trace dùng timestamp để chia pha và phát lại quyết định. Sửa deadline socket không tự làm môi trường clock ổn định. Không tăng ngưỡng 5 ms sau khi thấy bước nhảy 2,6 giây, không chọn riêng lượt đẹp và không đổi trạng thái `inconclusive` thành đạt.

## Thứ tự tiếp tục

1. Chuỗi chạy T09 và bàn giao bằng chứng đã hoàn tất.
2. Không chạy thêm tải và dừng trước T10 theo phạm vi đã được phép.
3. T10 chưa bắt đầu; chưa có kết luận RQ.

Giao diện so sánh, CSV và [biểu đồ pilot](../worklog/2026-10-13-evaluation/README.md) có thể hoàn thiện độc lập. Đây là công cụ trình bày và kiểm tra bằng chứng; chúng không thay điều kiện đo hoặc chứng minh tính đúng/khả năng mở rộng ở production.
