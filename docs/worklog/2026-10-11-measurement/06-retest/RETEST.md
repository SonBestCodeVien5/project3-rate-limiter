# Kiểm thử lại, pilot và tiếp quản

## Kiểm thử phần mềm

`GOCACHE=/tmp/project3-go-cache PYTHONDONTWRITEBYTECODE=1 bash scripts/verify.sh` PASS trên bản cuối: gofmt, vet, Go race tests, build, shell/cleanup, 3 topology tests, 16 analyzer tests và Compose validation. Xem [verify-final.log](verify-final.log). Vòng này không đặt REDIS_TEST_ADDR nên các integration unit tests Redis cũ được skip; các case pilot Redis thật chạy qua Compose. Core limiter không đổi so với vòng bootstrap đã test Redis thật.

Sau hiệu chỉnh tải chỉ thay tham số runner `MIXED_RPS`: shell syntax, kiểm tra input 0 bị từ chối với exit2 và pilot ba mode thực tế đã chạy đạt. Không chạy lại toàn bộ test Go cho thay đổi shell này.

## Gián đoạn và cách tiếp tục

- Subagent dừng do giới hạn sử dụng sau 4 case hoàn tất; case concurrent-redis mới có cấu hình/build, chưa có trace. Giữ nguyên `artifacts/measurement-pilot`.
- Khi user yêu cầu làm nốt, phiên chính xác nhận runner cũ không còn và lab chỉ còn container đã dừng. Lượt tiếp quản đầu bị script từ chối đúng vì project còn tồn tại; [log](resume-pilot.log).
- Dọn đúng project `project3-research-lab`, chạy 7 case còn lại vào `artifacts/measurement-resume-2`; [log](resume-pilot-2.log).
- Mixed-Redis 300 RPS có 3 schedule_backlog drops; rerun cùng cấu hình vào `measurement-rerun` có 2 drops. Giữ cả hai, đánh dấu không đạt offered load; không chạy tìm một kết quả đẹp.
- Hiệu chỉnh **toàn bộ ba mode mixed** sang `MIXED_RPS=120 BACKEND_CAPACITY=4`, service50ms, legitimate20 RPS. Cả ba 720/720 request không drop/transport error. Đây là cấu hình pilot mới, không so thẳng với capacity10/300RPS.

## Bảng quan sát đầy đủ

Không có transport error trong 15 lượt hoàn tất; 2 lượt có generator drops. Tổng 12.020 lịch request, 12.015 thực gửi. Không tính 2.000 request outage bootstrap được phân tích lại vào số request mới. Có 11 case khác nhau, một rerun và ba lượt hiệu chỉnh. Mọi trace/summary và delta backend arrivals khớp; không thấy vi phạm policy theo scope instance/shared trên các quyết định quan sát được. FW vẫn `inconclusive` về độ phủ toàn cửa sổ dù các nhóm trace tươi đủ bằng chứng đã được kiểm tra.

| Nhóm / case | Gửi / dự kiến | Drops | 2xx | 429 | 5xx | Backend arrivals | Legit goodput/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pilot / burst-fw-repeat-1 | 300/300 | 0 | 149 | 151 | 0 | 149 | 10.00 |
| pilot / burst-tb-repeat-1 | 300/300 | 0 | 159 | 141 | 0 | 159 | 10.00 |
| pilot / concurrent-local-repeat-1 | 100/100 | 0 | 10 | 60 | 30 | 40 | 0.00 |
| pilot / normal-repeat-1 | 60/60 | 0 | 60 | 0 | 0 | 60 | 10.00 |
| resume-2 / concurrent-redis-repeat-1 | 100/100 | 0 | 10 | 80 | 10 | 20 | 0.00 |
| resume-2 / mixed-local-repeat-1 | 1800/1800 | 0 | 308 | 1400 | 92 | 400 | 18.82 |
| resume-2 / mixed-none-repeat-1 | 1800/1800 | 0 | 1126 | 0 | 674 | 1800 | 7.94 |
| resume-2 / mixed-redis-repeat-1 | 1797/1800 | 3 | 211 | 1542 | 44 | 255 | 19.15 |
| resume-2 / scale-1-repeat-1 | 600/600 | 0 | 260 | 340 | 0 | 260 | 19.99 |
| resume-2 / scale-2-repeat-1 | 600/600 | 0 | 243 | 357 | 0 | 243 | 19.86 |
| resume-2 / scale-4-repeat-1 | 600/600 | 0 | 249 | 351 | 0 | 249 | 19.86 |
| rerun / mixed-redis-repeat-1 | 1798/1800 | 2 | 215 | 1538 | 45 | 260 | 19.15 |
| calibration / mixed-local-repeat-1 | 720/720 | 0 | 259 | 327 | 134 | 393 | 14.66 |
| calibration / mixed-none-repeat-1 | 720/720 | 0 | 407 | 0 | 313 | 720 | 8.11 |
| calibration / mixed-redis-repeat-1 | 720/720 | 0 | 190 | 466 | 64 | 254 | 17.04 |

Batch concurrent: local hai instance nhận 40 cho quota mỗi instance20, global observed overshoot20; Redis nhận20 cho quota shared20. Đây là hành vi đối chứng local, không phải lỗi mutex. p99 send lag khoảng 26ms/21ms, nên không khẳng định 100 request đến server cùng một thời điểm. Nhóm scaling1/2/4 giữ backend capacity10/service50ms và tải100RPS; một lượt ngắn không đủ đánh giá throughput scalability.

## Phân tích lại outage bootstrap

Dùng bản sao raw cũ trong `artifacts/measurement-outage-analysis`; policy trích từ `compose-resolved.yaml` gốc và đặt state_reset=false một cách thận trọng. Không sửa artifacts nguồn. Chọn threshold p95=100ms, window1s, min5 legitimate/window, 2 cửa sổ sạch **chỉ để kiểm tra analyzer**, không khóa protocol sau khi thấy kết quả.

Trong pha giữa pause_completed và unpause_requested: fail-open có legitimate availability40/40; fail-closed0/40. Cả hai ghi nhận stable recovery theo tiêu chí thăm dò ở mốc xác nhận3000ms sau unpause; đây là thời điểm đủ chuỗi cửa sổ quan sát, không bằng thời điểm Redis vừa hồi phục. Không kết luận quota correctness trong outage vì state/response có thể không xác định và clock khác nguồn.

## Evidence và giới hạn

- [pilot-summary.json](pilot-summary.json), [artifact-check.log](artifact-check.log), [check-artifacts.py](check-artifacts.py) giữ mọi lượt, gồm hai lượt không đạt tải.
- [Archive](evidence/measurement-artifacts.tar.gz) chứa trace/config/summary/analysis/resource/logs, cả case gián đoạn; bỏ binary. [Manifest](evidence/manifest.json) ghi source SHA256 và SHA256 archive. Các analysis đầu ở 4 case đầu được giữ `analysis.*.initial`; phân tích lại bằng analyzer cuối không sửa raw.
- Metadata giữ nguyên git revision/dirty state tại thời điểm chạy. Source cuối được commit theo phần và hash; không sửa metadata thành trạng thái sạch giả.
- Runner đã dọn container lab sau hoàn tất. Warning Docker plugins thiếu binary ngoài repo không ảnh hưởng các lệnh thành công.
- Còn thiếu protocol khóa, warm-up hoặc lý do cold-start chính thức, repetitions đủ để đánh giá biến thiên, burst xác minh gần biên server, ma trận thuật toán/state/scaling đầy đủ, quota violation khi fail-open, biểu đồ và báo cáo cuối.

Giải nén archive từ repo root vào workspace mới, rồi chạy `python3 docs/worklog/2026-10-11-measurement/06-retest/check-artifacts.py` để đối chiếu. Script này kiểm tra cấu trúc/counters của bộ pilot cụ thể; `load_fidelity=invalid_offered_load` vẫn có thể đi cùng artifact consistency PASS và phải giữ nguyên nhãn khi dùng số liệu.
