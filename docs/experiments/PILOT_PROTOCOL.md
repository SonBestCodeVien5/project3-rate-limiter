# Giao thức pilot đo lường ứng viên (11/10/2026)

Đây là pilot kỹ thuật để chọn giao thức nghiên cứu về sau, chưa phải thí nghiệm đã khóa hay kết luận cho RQ1–RQ5. [Roadmap](../context/sources/00_Project3_Roadmap.md) và [Proposal](../context/sources/01_Project3_Proposal.md) xác định các phép so sánh thuật toán, state cục bộ/chung, số API instance, quyết định dưới tải concurrent, mức bảo vệ backend và Redis outage có giới hạn. Các con số bên dưới là mặc định để thử nghiệm; có thể điều chỉnh sau khi kiểm tra load generator có đạt tải đề ra và backend có quá tải như dự kiến. [Đặc tả thí nghiệm](EXPERIMENT_SPEC.md) vẫn là baseline rộng hơn.

## Ma trận ứng viên

`research-pilot.sh` dùng Compose project riêng `project3-research-lab`, một backend dùng chung (`BACKEND_CAPACITY=10`, `BACKEND_SERVICE_TIME=50ms` nếu môi trường không ghi đè) và Nginx chỉ lắng nghe trên loopback. Mỗi case gửi tải trong 6 giây, mặc định một lượt và tối đa ba lượt. Từng lượt tạo container mới và namespace riêng. Sau khi health check đạt, runner chờ 1 giây để ổn định startup; nó không gửi `/work` trong khoảng này, nên không có warm-up tiêu thụ quota. Policy mặc định lấy từ Compose đã resolve: `LIMIT=20`, `WINDOW=1s`, `CAPACITY=20`, `RATE=20`. Runner luôn chọn `FAIL_POLICY=closed` cho ma trận này và lưu policy thực tế tại `policy.json`.

| Case | Số API | State / thuật toán | Profile | Tải đề ra |
| --- | ---: | --- | --- | --- |
| `normal` | 2 | Redis / Fixed Window | normal | 10 RPS hợp lệ |
| `burst-fw`, `burst-tb` | 2 | Redis / từng thuật toán | burst | 10 RPS hợp lệ, 10 RPS bất thường nền; tăng luồng bất thường lên 100 RPS từ giây 2 đến giây 4 |
| `concurrent-local`, `concurrent-redis` | 2 | local / Redis Fixed Window | concurrent | 100 request cùng key được lên lịch tại mốc giây 2 |
| `scale-1`, `scale-2`, `scale-4` | 1, 2, 4 | Redis / Fixed Window | mixed | Tổng 100 RPS, gồm 20 RPS hợp lệ |
| `mixed-none`, `mixed-local`, `mixed-redis` | 2 | none / local / Redis Fixed Window | mixed | Tổng 300 RPS, gồm 20 RPS hợp lệ |

Ba case scaling giữ nguyên một container backend và capacity của nó, chỉ đổi số API. Ba case mixed giữ nguyên tải đề ra và backend. Batch concurrent có cùng **thời điểm lên lịch**, không bảo đảm các request đến server cùng lúc; phải xem `schedule_lag_ms` và thời điểm gửi thực tế trước khi diễn giải. Trace local cho thấy quota phân tách theo instance so với quota chung qua Redis; ma trận này chưa có đối chứng Redis không atomic. Pilot outage có giới hạn vẫn nằm ở `redis-outage.sh`, cần phân tích riêng theo pha và không tự động nhân vào ma trận trên.

## Chạy và lưu bằng chứng

Chạy một tập con bằng `bash scripts/research-pilot.sh --case normal --case scale-1 --case scale-2 --case scale-4 --repetitions 2 --analyze`; bỏ `--case` để chạy cả 11 case. `--output` phải trỏ đến folder chưa tồn tại. Có thể bỏ `--analyze` để chỉ thu dữ liệu thô. Runner từ chối project đã có container, dọn container do lượt chạy tạo khi hoàn tất hoặc lỗi, và giữ lại file đã ghi. Các lệnh build, Compose, HTTP và generator đều có timeout. Renderer 1/2/4 đọc `docker compose config --format json`; nhãn CLI của workload không được xem là bằng chứng cấu hình server. Nginx upstream và health dependencies chứa đúng số API đã chọn, kể cả trường hợp chỉ có một API.

Mỗi case lưu Compose gốc đã resolve, Compose sau render, Nginx, policy, ba file generator `metadata.json`/`requests.jsonl`/`summary.json`, metrics trước/sau của từng API và backend, mẫu Redis INFO, log container và image ID/digest. Folder gốc lưu Git revision/status cùng phiên bản Docker/Compose. Image build cục bộ có thể không có repository digest; khi đó cần xem image ID cùng revision nguồn và trạng thái thay đổi của cây làm việc. `policy.json.state_reset=true` dựa trên container mới và namespace riêng do runner tạo; thao tác render độc lập mặc định ghi `false`.

## Điều kiện dùng kết quả và quyết định tiếp theo

Trước khi so sánh, kiểm tra `generator_dropped`, độ trễ lịch gửi, lỗi transport và timestamp từng request. Lượt có request bị bỏ, độ trễ gửi đáng kể so với khoảng cách tải đề ra, dữ liệu thô thiếu, lỗi ngoài dự kiến, health check lỗi hoặc thiếu snapshot trước/sau không đủ căn cứ để khẳng định tải và tính đúng. HTTP 429 là quyết định reject của limiter, cần tách khỏi timeout và 5xx. Đối chiếu tải gửi/hoàn tất đo được và counter request tới backend với trạng thái dưới tải/quá tải mong muốn. Nếu case mixed không đưa backend gần mức giới hạn, điều chỉnh tải pilot hoặc thời gian xử lý backend rồi chạy lại tập case có kiểm soát trước khi khóa tham số.

Lặp lại các case hợp lệ để xem độ dao động của goodput, p95/p99, quyết định quota và chênh lệch tài nguyên Redis. Không dùng một lượt 6 giây để khẳng định latency hay throughput ổn định. Redis CPU INFO là counter tích lũy: tính chênh lệch theo thời gian, không gọi giá trị thô là phần trăm CPU. Tính đúng Fixed Window cần cửa sổ theo key có đủ bằng chứng; Token Bucket cần oracle theo semantics token riêng. Thứ tự timestamp phía client không xác định thứ tự quyết định ở server. Tham số báo cáo cuối cùng, số lần lặp, ngưỡng chấp nhận và cửa sổ recovery sau outage sẽ được khóa sau pilot.
