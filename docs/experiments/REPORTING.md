# Xuất dữ liệu báo cáo RQ1–RQ5

**Trạng thái hiện tại (20/10/2026):** T09 đã hoàn tất; T10 chưa bắt đầu và chưa có kết luận RQ. Công cụ này chỉ tổng hợp tệp bằng chứng đã có; tài liệu không cho phép chạy thêm tải. Xem [kế hoạch việc còn lại](../REMAINING_WORK_PLAN.md).

Đây là công cụ trình bày các tệp bằng chứng đo thực tế; công cụ không thay đổi protocol và không tự kết luận mode/thuật toán nào tốt hơn. Dùng sau công cụ phân tích theo [ANALYSIS.md](ANALYSIS.md). Không thay đổi tệp bằng chứng gốc, không chạy Docker hoặc tải HTTP. Matplotlib chưa được cài trên môi trường hiện tại; công cụ chỉ xuất CSV/Markdown, không thêm thư viện phụ thuộc.

Tạo manifest JSON, trong đó các lượt được chọn **ghi rõ**, còn đường dẫn tính tương đối từ thư mục chứa manifest. `group` là nhãn RQ/nhóm phép đo; `cell` là một cấu hình duy nhất có cùng mode/thuật toán, mẫu tải, policy, backend, topology, revision và image. Mỗi cấu hình khác nhau cần `cell` riêng, kể cả khi thuộc cùng RQ. Công cụ không tự tìm lượt bằng glob và không đếm cùng đường dẫn hai lần.

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

Các đường dẫn chỉ minh họa schema, không phải lượt đã đo. `clock_tolerance_ms: 5` cũng chỉ là ví dụ; cần hiệu chỉnh và khóa trước khi dùng bộ đo chính thức. Công cụ không tự điều chỉnh ngưỡng sau khi thấy kết quả.

```bash
python3 scripts/report-study.py path/to/manifest.json --output artifacts/report-new
python3 -m unittest discover -s scripts -p test_report_study.py
```

Thư mục output phải chưa tồn tại. Kết quả gồm `runs.csv` giữ mọi lượt, kể cả lượt không hợp lệ; `cells.csv` chứa trạng thái đầy đủ và median/min/max khi đủ điều kiện; `report.md` tóm tắt số liệu/chất lượng cùng bản sao manifest. Giá trị không có mẫu hoặc thiếu bằng chứng được để trống; không biến p95 không có mẫu thành 0. Percentile là **chỉ số riêng từng lượt**: `legitimate_p95_ms_run_median` nghĩa là median của các p95 từng lượt, tuyệt đối không phải p95 của trace đã gộp.

Mỗi lượt đọc summary/analysis/metadata/policy, Compose đã resolve, ID/nền tảng image, digest nền, nginx config, revision/trạng thái cây mã và trace. Các file revision/status nằm ở thư mục cha của case, theo cách bộ chạy hiện tại lưu. Fingerprint bỏ run_id và namespace, nhưng giữ phiên bản mẫu tải/phân bố key, nhãn mode/algorithm/fail policy, thông số policy, backend/topology/runtime/image. Việc khớp chỉ áp dụng **trong cùng một cấu hình**; công cụ không xác nhận hai cấu hình khác nhau là một phép so sánh có kiểm soát.

Thiếu bằng chứng hoặc sai định dạng, policy/công cụ phân tích/revision/run_id không khớp, cây mã có thay đổi, thiếu counter, lượt bị hủy, request bị bỏ, trace ID trùng, dữ liệu thô/summary không khớp hoặc clock có dấu hiệu bất thường đều làm lượt không hợp lệ để tổng hợp. Nếu cấu hình thiếu số lượt yêu cầu, nhãn lặp trùng, cấu hình khác hoặc có lượt không hợp lệ thì cấu hình giữ trạng thái/lý do và **không xuất thống kê tổng hợp**. Đây là kiểm tra thận trọng; công cụ không tự bỏ rồi thay một lượt, cũng không tự chọn các lượt có kết quả thuận lợi.

Kiểm tra clock tính `abs((sent_at − scheduled_at) theo wall clock − schedule_lag_ms theo monotonic)` cho từng request đã gửi và ghi độ lệch lớn nhất. Vượt ngưỡng được gắn nhãn `client_clock_discontinuity_suspected`; đây không phải bằng chứng chắc chắn có bước nhảy NTP, không kiểm tra đồng hồ server và không chứng minh clock luôn ổn định. Quyết định chưa rõ, lỗi truyền tải/timeout/5xx và lỗi limiter được gắn cờ riêng. Quá tải và lỗi trong outage có thể là kết quả được chủ ý tạo ra; không tự loại cả lượt chỉ vì chúng xuất hiện. Người viết báo cáo cần xác định theo protocol đã khóa phép so sánh nào bị giới hạn.

Tính hợp lệ của công cụ, tính đúng theo oracle và kết luận nghiên cứu là ba việc riêng. FW chưa đủ bằng chứng kết luận do cửa sổ chưa đầy đủ không tự làm lượt không hợp lệ; các vi phạm đã quan sát cũng được giữ nguyên để báo lỗi thực tế. CSV ghi trạng thái oracle, số vi phạm đã quan sát, cận dưới lớn nhất của envelope, số lõi CPU và memory của Redis, tỷ lệ availability của client hợp lệ trong từng pha outage và recovery ổn định/trạng thái nếu công cụ phân tích cung cấp. Không cộng các cận dưới rồi gọi đó là tổng overshoot, không coi oracle chưa đủ bằng chứng kết luận là đạt, và không thay recovery thiếu mẫu bằng thời điểm request thành công đầu tiên.

Báo cáo cuối vẫn cần đi theo mạch: vấn đề doanh nghiệp → khó khăn → tác động → yêu cầu kỹ thuật → giải pháp → thí nghiệm → đánh giá → phát triển tương lai. Liên kết từng RQ với manifest, bộ đếm/trace/oracle, biến thiên giữa các lượt và giới hạn phép đo. Giữ lại mọi lượt không hợp lệ cùng lý do; không quy goodput của backend mô phỏng thành doanh thu thực tế. Ba lượt và khoảng min–max không tự chứng minh ý nghĩa thống kê hoặc khả năng mở rộng production.

## Biểu đồ hiệu chỉnh ngoại tuyến

`scripts/plot-calibration.py` đọc cấu trúc `runs.json` của [lượt hiệu chỉnh ngày 13/10](../worklog/2026-10-13-calibration/runs.json), không tự tìm tệp bằng chứng và không chạy benchmark. Chọn chính xác từng `cell`/lượt bằng manifest riêng; danh sách phải ghi đủ các lượt cần trình bày, kể cả lượt có chất lượng kém. Mọi mục được giữ lại: thiếu lượt hoặc số liệu sẽ tạo khoảng trống trên biểu đồ, không âm thầm bỏ điểm.

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

Tên `cell` chỉ minh họa cách chọn; trước khi dùng cần đối chiếu với các tên trong tệp nguồn. Đường dẫn source tính tương đối từ manifest. Công cụ chỉ hỗ trợ profile `mixed` và yêu cầu mode thực tế khớp với mục đã chọn; nhãn trùng hoặc tệp nguồn có nhiều dòng cho cùng `cell` sẽ bị từ chối. Không thể chọn riêng từng pha vì cấu trúc dữ liệu hiệu chỉnh hiện không có số request hợp lệ thành công theo pha; không suy tỷ lệ theo pha từ tỷ lệ cả lượt.

```bash
# Chỉ stdlib, không import matplotlib hoặc tạo biểu đồ:
python3 scripts/plot-calibration.py plot-manifest.json --validate-only
python3 -m unittest discover -s scripts -p test_plot_calibration.py
# Chỉ chạy sau khi kết thúc measurements, bằng Python có matplotlib:
python3 scripts/plot-calibration.py plot-manifest.json --output artifacts/calibration-figures-new
```

Matplotlib là công cụ lập báo cáo ngoại tuyến tùy chọn; không thêm vào thư viện phụ thuộc runtime/repo và không cài trong lúc đo. Output mới gồm PNG, SVG riêng và `points.json` liên kết mỗi điểm với `cell`, oracle, mẫu số và cờ chất lượng. Hình có tiêu đề **Pilot — not formal benchmark**, gồm hai biểu đồ: số HTTP 2xx hợp lệ chia cho số request hợp lệ đã gửi, và delta bộ đếm backend quá tải. Mẫu số là tổng `sent` trong các pha client hợp lệ của lượt hiệu chỉnh; không dùng tổng HTTP sent hoặc scheduled. Nếu thiếu mẫu số, không có request hợp lệ đã gửi hoặc tử số không thể có, trường đó được ghi thiếu thay vì gán bằng 0.

Mỗi điểm là một lượt riêng; không nối các điểm thành đường, khớp xu hướng, gộp percentile hoặc khẳng định quan hệ nhân quả/ý nghĩa thống kê. Dấu × đỏ giữ số liệu của lượt có cờ chất lượng, gồm clock/lỗi; chỉ số thiếu tạo khoảng trống. Oracle chưa đủ bằng chứng kết luận vẫn được giữ trong tệp phụ, không tự coi là lượt không hợp lệ. Script dùng cờ chất lượng/độ trung thực do hiệu chỉnh cung cấp, đồng thời thêm cờ nếu có lỗi limiter, request bị bỏ, lỗi truyền tải/timeout hoặc thiếu chỉ số. Script không tự đọc trace để chứng minh clock ổn định và không kiểm tra policy/revision/image có khớp giữa các mode hay không. Các kiểm tra đó thuộc công cụ xuất báo cáo và protocol; biểu đồ không xác nhận phép so sánh có kiểm soát. Không tự động coi `http_5xx` do backend quá tải có chủ ý là lỗi công cụ.


## Image identity khi build cache tạo ID khác nhau

Bộ chạy mới lưu thêm `image-inspect.json` từ Docker trước khi tải, không sửa `images.json`. Công cụ xuất báo cáo/Console chỉ dùng inspect khi mỗi mục khớp đúng `.Id` với ID gốc trong manifest images. Khi có bằng chứng hợp lệ, dấu vân tay gồm **toàn bộ** `RootFS.Layers` theo thứ tự, toàn bộ `Config`, OS/architecture/variant và platform. Nếu các trường này giống nhau, image ID khác vẫn được coi là cùng nội dung; layer/config khác nhau thì bị từ chối. Revision trùng nhau không thay thế bằng chứng về image.

Lượt cũ thiếu file inspect tiếp tục dùng ID chính xác. Inspect sai định dạng hoặc không khớp ID được ghi lỗi; công cụ vẫn dùng ID chính xác làm phương án dự phòng nhưng không cho phép tổng hợp khi bằng chứng có lỗi. Không hồi tố chấp nhận ID bị thiếu chỉ vì revision trùng hoặc vì có inspect từ một lượt khác. Việc so khớp lượt có inspect với lượt không có inspect vẫn thận trọng và có thể từ chối ngay cả khi ID gốc trùng nhau; không bỏ bằng chứng để làm các cấu hình khớp.
