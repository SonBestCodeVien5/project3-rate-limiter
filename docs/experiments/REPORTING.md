# Xuất dữ liệu báo cáo RQ1–RQ5

Đây là công cụ trình bày artifacts đo thật, không khóa protocol và không tự kết luận mode/thuật toán thắng. Dùng sau analyzer theo [ANALYSIS.md](ANALYSIS.md). Không thay đổi artifacts gốc, không chạy Docker hoặc tải HTTP. Matplotlib chưa được cài trên môi trường hiện tại; công cụ chỉ xuất CSV/Markdown, không thêm dependency.

Tạo manifest JSON có các lượt được chọn **tường minh**, đường dẫn tương đối tính từ thư mục manifest. `group` là nhãn RQ/nhóm phép đo; `cell` là một cấu hình duy nhất, gồm cùng mode/thuật toán, tải, policy, backend, topology, revision và images. Các cấu hình khác nhau cần cell khác nhau, kể cả khi thuộc cùng RQ. Không tự tìm run theo glob và không đếm cùng đường dẫn hai lần.

```json
{
  "clock_tolerance_ms": 5,
  "cells": [
    {"id": "rq1-fw-redis-normal", "expected_repetitions": 3}
  ],
  "runs": [
    {"group": "RQ1", "cell": "rq1-fw-redis-normal", "repetition": "1", "path": "artifacts/block-1/custom-repeat-1"},
    {"group": "RQ1", "cell": "rq1-fw-redis-normal", "repetition": "2", "path": "artifacts/block-2/custom-repeat-1"},
    {"group": "RQ1", "cell": "rq1-fw-redis-normal", "repetition": "3", "path": "artifacts/block-3/custom-repeat-1"}
  ]
}
```

Các đường dẫn trên chỉ minh họa schema; không phải run đã đo. `clock_tolerance_ms: 5` cũng chỉ là ví dụ, phải hiệu chỉnh/khóa trước khi dùng bộ đo chính thức. Công cụ không tự điều chỉnh ngưỡng sau khi nhìn kết quả.

```bash
python3 scripts/report-study.py path/to/manifest.json --output artifacts/report-new
python3 -m unittest discover -s scripts -p test_report_study.py
```

Thư mục output phải chưa tồn tại. Kết quả gồm `runs.csv` giữ mọi lượt kể cả invalid, `cells.csv` chứa trạng thái đầy đủ và median/min/max khi đủ điều kiện, `report.md` tóm tắt số liệu/chất lượng và bản sao manifest. Các giá trị không có mẫu hoặc thiếu evidence để trống; không biến p95 không có mẫu thành 0. Percentile là **chỉ số riêng từng lượt**: `legitimate_p95_ms_run_median` nghĩa là median của các p95 từng lượt, tuyệt đối không phải p95 của trace gộp.

Mỗi lượt đọc summary/analysis/metadata/policy, Compose resolve, IDs/platform images, base digests, nginx config, revision/dirty tree, và trace. Các file revision/status nằm ở thư mục cha case như runner hiện tại. Fingerprint bỏ run_id và namespace, giữ workload/key distribution version, các nhãn mode/algorithm/fail policy, policy số, backend/topology/runtime/images. Matching chỉ áp dụng **bên trong cell**; công cụ không xác nhận rằng hai cell khác cấu hình là một phép so sánh có kiểm soát.

Thiếu/malformed evidence, policy/analyzer/revision/run_id không khớp, dirty tree, counters thiếu, canceled, drops, duplicate trace IDs, raw/summary không khớp hoặc clock nghi ngờ làm lượt invalid cho aggregation. Nếu cell thiếu số lượt yêu cầu, nhãn lặp trùng, cấu hình khác hoặc có lượt invalid thì cell giữ trạng thái/lý do và **không xuất thống kê tổng hợp**. Đây là kiểm tra bảo thủ; công cụ không tự loại rồi thay thế một lượt hoặc chọn subset đẹp hơn.

Kiểm tra clock tính `abs((sent_at − scheduled_at) theo wall clock − schedule_lag_ms theo monotonic)` cho từng request đã gửi và ghi độ lệch lớn nhất. Vượt ngưỡng là `client_clock_discontinuity_suspected`, không phải bằng chứng chắc chắn NTP step; nó không kiểm tra server clock hoặc chứng minh clock luôn ổn. Unknown decisions, transport/timeouts/5xx và limiter errors được gắn cờ riêng. Overload và lỗi trong outage có thể là outcome chủ ý: không tự loại toàn lượt chỉ vì chúng xuất hiện. Người viết báo cáo phải quyết định phép so nào bị giới hạn theo protocol đã khóa.

Tooling validity, oracle correctness và kết luận nghiên cứu là ba việc riêng. FW inconclusive vì partial windows không tự làm lượt invalid; observed violations cũng giữ nguyên để báo lỗi thật. CSV ghi oracle, số observed violations, lower-bound envelope lớn nhất, Redis CPU cores/memory, availability hợp lệ từng pha outage và stable recovery/status nếu analyzer cung cấp. Không cộng các lower bound rồi gọi là tổng overshoot, không gọi oracle inconclusive là pass, và không thay recovery thiếu mẫu bằng thời gian request thành công đầu tiên.

Báo cáo cuối vẫn cần đi theo vấn đề doanh nghiệp → pain point → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → phát triển tương lai. Liên kết từng RQ với manifest, counter/trace/oracle, biến thiên giữa các lượt và giới hạn đo. Giữ mọi lượt invalid và lý do; không quy goodput backend mô phỏng thành doanh thu thực tế. Ba lượt và min–max không tự chứng minh ý nghĩa thống kê hoặc khả năng mở rộng production.

## Biểu đồ calibration ngoại tuyến

`scripts/plot-calibration.py` đọc schema `runs.json` của [calibration 13/10](../worklog/2026-10-13-calibration/runs.json), không tự tìm artifacts và không chạy benchmark. Chọn chính xác mỗi `cell`/lượt bằng manifest riêng; danh sách chọn phải ghi đủ những lượt cần trình bày, kể cả lượt chất lượng kém. Mọi entry được giữ: thiếu lượt hoặc thiếu số liệu tạo gap, không âm thầm bỏ điểm.

```json
{
  "source": "runs.json",
  "entries": [
    {"cell": "mixed-none-repeat-1", "mode": "none"},
    {"cell": "mixed-local/custom-repeat-1", "mode": "local"},
    {"cell": "mixed-redis/custom-repeat-1", "mode": "redis"}
  ]
}
```

Tên cell trên minh họa cách chọn; đối chiếu đúng các tên trong file nguồn trước khi dùng. Source tính tương đối từ manifest. Chỉ hỗ trợ profile `mixed`, cùng mode thực tế với entry; nhãn trùng hoặc source có nhiều dòng cùng cell bị từ chối. Không hỗ trợ chọn pha vì schema calibration hiện không có số legitimate successes từng pha; không suy tỷ lệ thành công pha từ tỷ lệ toàn lượt.

```bash
# Chỉ stdlib, không import matplotlib hoặc tạo biểu đồ:
python3 scripts/plot-calibration.py plot-manifest.json --validate-only
python3 -m unittest discover -s scripts -p test_plot_calibration.py
# Chỉ chạy sau khi kết thúc measurements, bằng Python có matplotlib:
python3 scripts/plot-calibration.py plot-manifest.json --output artifacts/calibration-figures-new
```

Matplotlib là công cụ report ngoại tuyến tùy chọn; không thêm vào dependency runtime/repo và không cài trong lúc đo. Output mới gồm PNG, SVG độc lập và `points.json` gắn số điểm với cell, oracle, denominator và quality flags. Figure có tiêu đề **Pilot — not formal benchmark**, hai panel là legitimate 2xx/legitimate sent và backend overload counter delta. Denominator lấy tổng `sent` của các pha legitimate trong calibration; không dùng tổng HTTP sent hoặc scheduled làm denominator. Thiếu denominator, không có legitimate sent hay numerator bất khả thi được ghi thiếu, không gán bằng 0.

Mỗi điểm là một lượt riêng; không nối đường, fit trend, gộp percentile hoặc khẳng định nhân quả/ý nghĩa thống kê. Dấu × đỏ giữ số liệu của lượt có quality flag, gồm clock/errors; chỉ số thiếu có gap. Oracle inconclusive vẫn được giữ trong sidecar, không tự coi là invalid. Script tin quality flags/fidelity do calibration cung cấp, thêm flags khi có limiter errors/drops/transport/timeout hoặc thiếu metric; nó không tự đọc trace để chứng minh clock ổn và không xác minh matching policy/revision/images giữa mode. Những kiểm tra đó vẫn thuộc exporter và protocol; biểu đồ không chứng nhận một so sánh có kiểm soát. Không đổi `http_5xx` do backend overload chủ ý thành lỗi tooling một cách tự động.


## Image identity khi build cache tạo ID khác nhau

Runner mới giữ thêm `image-inspect.json` từ Docker trước load, không sửa `images.json`. Exporter/Console chỉ dùng inspect khi mỗi entry khớp đúng `.Id` với original ID trong images manifest. Khi có evidence hợp lệ, fingerprint dùng **toàn bộ** `RootFS.Layers` theo thứ tự, toàn bộ `Config`, OS/architecture/variant và platform. Image IDs khác nhau nhưng các trường này giống nhau được so theo nội dung; layer/config khác vẫn bị từ chối. Revision giống nhau không thay cho evidence image.

Run cũ thiếu file inspect tiếp tục dùng exact ID. Inspect malformed hoặc không khớp ID được ghi lỗi, giữ fallback exact ID nhưng không cho aggregation qua lỗi evidence. Không hồi tố chấp nhận IDs đã mất chỉ vì có revision hoặc vì inspect của một run khác. Matching giữa run có inspect và run không có inspect vẫn bảo thủ và có thể từ chối cả khi original IDs trùng; không bỏ evidence để làm cell khớp.
