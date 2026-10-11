# Rà soát độc lập tooling đo lường — 11/10/2026

## Phạm vi và trạng thái

Đã đọc đặc tả thí nghiệm, mã load generator, runner Compose, topology renderer, analyzer và các test liên quan. Đây là rà soát logic và tính đủ của bằng chứng cho pilot, không phải kết luận nghiên cứu. Không lặp lại lượt chạy Docker; agent topology chịu trách nhiệm `verify` và pilot 11 ca. Load generator đã qua `GOCACHE=/tmp/project3-go-cache go test ./internal/experiment ./cmd/loadgen` với quyền mở socket cục bộ; `git diff --check` đã qua.

## Phát hiện và cách xử lý

| Vấn đề thấy khi rà soát | Trạng thái xử lý |
| --- | --- |
| Trace raw thiếu bản ghi vẫn có thể khiến Token Bucket báo không thấy vi phạm, do oracle không dùng tính đầy đủ của summary. | Analyzer yêu cầu `summary.json`, đối chiếu `scheduled`/`sent`/`generator_dropped` với raw; trace lệch bị từ chối. Trạng thái replay cũng phụ thuộc `trace_complete`. |
| Chuyển timestamp sang epoch mili giây bằng số thực có thể phân nhóm sai sát biên cửa sổ. | Analyzer dùng phép tính `datetime` nguyên cho mili giây. |
| Token Bucket với một client toàn `reject` tạo danh sách allow rỗng rồi gọi `min`/`max`. Trường hợp mọi request bị generator drop cũng thiếu bằng chứng để kết luận đúng. | Trường hợp toàn reject tạo envelope 0 allow; trace toàn drop được đánh dấu inconclusive. Có test hồi quy. |
| Recovery dùng `end_at` của response cuối để xác định cửa sổ đầy đủ, có thể lấy cả thời gian drain sau khi ngừng tải. | Giới hạn cửa sổ bằng `summary.started_at + config.duration_ns`; lượt bị hủy không được kết luận recovery ổn định. |
| JSON snapshot sai kiểu hoặc trường tùy chọn của raw sai kiểu có thể gây exception không kiểm soát. | Analyzer kiểm tra object của snapshot và kiểu các trường có thể tham gia oracle; đầu vào lỗi được báo như lỗi bằng chứng. |
| Runner chỉ chụp counter API sau lượt chạy, nên không có delta theo instance. | Runner chụp `apiN-before.json` cho từng topology 1/2/4; analyzer tìm các cặp snapshot theo tên động. |
| Lịch periodic chậm vẫn có thể tạo đợt gửi bù; goroutine đã giữ slot còn có thể bắt đầu HTTP quá trễ. | Generator ghi `schedule_backlog` khi lịch mới hơn đã đến hạn, và kiểm tra lại `schedule_lag` ngay trước HTTP. Batch cùng một mốc dự kiến không bị quy tắc backlog loại. |
| `normal -rps 10` với mặc định `-legitimate-rps 20` có nguy cơ bị validator từ chối dù profile không dùng split. | Validator chỉ yêu cầu `legitimate-rps <= rps` cho mixed/burst; thêm test cho normal/concurrent. |

## Đánh giá giới hạn kết luận

FW dùng timestamp quyết định phía server, nhóm theo key và instance khi state local. Overshoot quan sát được trên quota là cận dưới chắc chắn. Với state reset độc lập và trace đầy đủ, số quyết định allow/reject trong một cửa sổ có thể được đối chiếu với `min(số request quan sát, quota)`; **độ phủ toàn bộ cửa sổ vẫn chưa được chứng minh** và được ghi `window_complete=false`. Mất header quyết định, timeout không rõ state, fallback, outage, run bị hủy hoặc state ban đầu chưa biết làm replay inconclusive. Token Bucket kiểm tra batch các quyết định có cùng mili giây bằng tổng số allow, vì thứ tự trong mili giây không thể suy từ trace client. TB không dùng quota Fixed Window.

`concurrent` dùng chung key và thời điểm **lên lịch**; `sent_at`, `schedule_lag_ms`, số drop và timestamp quyết định thể hiện tải thực tế. Không suy đồng thời đến server hoặc trúng biên Fixed Window từ thời điểm client. Normal dùng tất cả `-rps` như traffic hợp lệ, chia vòng qua các client key. Burst dùng mức abusive RPS tuyệt đối trong khoảng hữu hạn; nhãn `base`/`burst` áp dụng cho cả client hợp lệ theo thời điểm lên lịch. Metadata có workload version và toàn bộ cờ, còn nhãn policy của generator chỉ là khai báo; `policy.json` do runner lấy từ Compose đã resolve là bằng chứng cấu hình server.

Analyzer tách 429 khỏi timeout/5xx; backend arrival header chỉ là xác nhận phía client, còn delta counter backend là nguồn đo arrivals. Kết quả Redis CPU là giây CPU và số lõi CPU trung bình qua khoảng mẫu, không phải phần trăm CPU máy. Outage availability dùng request hợp lệ đã gửi làm mẫu số và giữ riêng pha pause/unpause; recovery ổn định cần ngưỡng p95 và đủ cửa sổ sạch. Lượt pilot sáu giây và giá trị tải trong runner là ứng viên để hiệu chuẩn; chưa khóa protocol, ngưỡng chấp nhận, số lần lặp hoặc suy kết quả thành production readiness.

## Bằng chứng còn cần từ pilot

Trước khi dùng một ca để so sánh, kiểm tra generator drops, schedule lag, timeout, trace/summary khớp, health, snapshot trước/sau, tải thực gửi, backend arrivals và resource Redis. Một ca có mất bản ghi hoặc không đạt offered load cần được đánh dấu không hợp lệ cho phép so sánh đó. Lượt pilot 11 ca và kiểm tra artifact do agent topology thực hiện sau bản rà soát này; cập nhật kết quả thực chạy riêng, không coi các test đơn vị là bằng chứng hiệu năng.

## Review khi tiếp quản và hiệu chỉnh pilot

Subagent dừng do giới hạn sử dụng khi pilot đang chuyển sang case concurrent-redis. Phiên chính xác nhận runner cũ không còn sống và lab chỉ còn container đã dừng; dọn đúng project trước khi chạy tiếp. Không xóa lượt không đầy đủ.

Kiểm tra raw sau chạy phát hiện mixed-redis 300 RPS có 3 schedule_backlog drops, lượt chạy lại có 2 drops. Trace/summary/counters khớp, nhưng chưa đạt offered load theo tiêu chí pilot. Không sửa generator để che drops; bổ sung `MIXED_RPS` và hiệu chỉnh cả nhóm mixed-none/local/redis ở 120 RPS với cùng backend capacity4/service50ms. Các trường hợp không đạt giữ trong evidence, không chọn riêng kết quả đẹp và không gộp hai cấu hình backend khác nhau để so sánh.
