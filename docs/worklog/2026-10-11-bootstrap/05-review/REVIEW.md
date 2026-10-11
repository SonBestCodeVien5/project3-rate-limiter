# Review độc lập — 11/10/2026

## Phạm vi và căn cứ

Đọc AGENTS, Project Brief, Source Index, Roadmap → Proposal → Supplementary Research Context và kế hoạch `02-plan/PLAN.md`. Review source limiter, HTTP flow, generator, test, Compose/Nginx. Đây là review prototype và tính trung thực của phép đo, không xác nhận RQ1–RQ5 đã có kết luận.

## Findings gửi cho agent chính

| ID | Mức độ | Vị trí lúc review | Vấn đề / tác động | Đề nghị |
| --- | --- | --- | --- | --- |
| R1 | P1 | `internal/experiment/load.go:285` | Generator gửi GET qua `http.Transport` có keepalive. GET có thể được transport tự retry khi reused connection lỗi sau khi server đã nhận request; quota/backend có thể bị thực thi nhiều lần nhưng chỉ có một raw record. | Dùng POST cho generator → API, mở POST `/work`; không gắn idempotency key; kiểm thử lỗi connection sau khi server nhận request. |
| R2 | P2 | `internal/limiter/redis_test.go`, `TestRedisConcurrentSharedQuota` | Test đòi mỗi cửa sổ có allow phải đủ quota dù số request trong cửa sổ có thể ít hơn quota khi đợt concurrent đi qua biên phút. Test có thể fail dù limiter đúng. | Nhóm cả allow và reject theo `Decision.At`; assert allow = min(requests trong window, Limit). |
| R3 | P2 | `internal/server/server.go:68,73–83` | Timestamp fail-open/fail-closed được lấy trước khi chờ Redis timeout. Header `X-Decision-Time` có thể lệch 100ms hoặc thuộc cửa sổ quota khác so với quyết định fallback thật. | Lấy timestamp tại nhánh lỗi, sau khi limiter trả về; test delayed error. |

Các finding đã được gửi ngay cho agent chính; xem trạng thái sửa ở cuối tài liệu. Vị trí trong bảng là số dòng lúc phát hiện, có thể thay đổi sau sửa.

## Điểm kiểm tra không phát hiện lỗi chặn ở lần đọc đầu

- Local dùng mutex và Redis đưa read/decide/update vào một Lua script; policy và client được tách key.
- FW dựa trên epoch window, reject không tăng counter; TTL hướng tới boundary.
- TB trừ đúng một token khi allow, cap capacity, clamp thời gian rollback; TTL không tái tạo bucket đầy sớm hơn thời gian nạp đầy.
- Redis client ở server tắt command retry và có timeout; Nginx tắt upstream retry; API → backend dùng POST.
- Backend có capacity hữu hạn; transport error ghi arrival unknown, không tự khẳng định backend chưa nhận.
- Generator ghi schedule lag, generator drops, raw request, status và quyết định riêng; summary nêu rõ không phải quota oracle và backend-confirmed arrivals không thay thế counters backend.

## Giới hạn cần giữ khi viết báo cáo

- Cả hai TB dùng độ phân giải millisecond; không suy diễn độ chính xác dưới 1ms. Các pilot rate nhỏ hợp lý với độ phân giải này; rate rất cao cần đánh giá riêng.
- FW phụ thuộc wall clock; rollback/NTP là giới hạn chưa nghiên cứu. TB có xử lý clamp rollback nhưng không thay thế kiểm chứng clock fault đầy đủ.
- Redis TIME và API/generator wall clock khác nguồn; timestamp fallback và timestamp Redis không bảo đảm đồng bộ tuyệt đối giữa host.
- Client header chỉ là định danh của testbed. Quota mỗi client không bảo vệ backend trước số lượng client tùy ý; đây không phải hệ thống chống lạm dụng danh tính production.
- Request bị mất phản hồi Redis có thể đã tiêu quota. Tắt retry tránh lặp lệnh nhưng không chứng minh exactly-once; fail-open có thể chuyển tiếp dù Redis đã thực thi lệnh.
- Đã tách request-context cancellation khỏi `limiter_errors` sau review; Redis timeout vẫn không xác định được lệnh đã thực thi hay chưa. Không dùng counter này đơn độc để suy ra quota violation.
- Summary chưa tính overshoot, quota violation hoặc recovery. Phải dùng quota oracle/analysis riêng và counter backend trước/sau; observations smoke/pilot không phải kết quả nghiên cứu hoàn chỉnh.
- Goodput denominator gồm drain và tail latency hợp lệ chỉ tính response 2xx; cần giữ nhãn này khi so sánh, không đồng nhất với latency của toàn bộ request hợp lệ.

## Kiểm chứng do reviewer chạy

- `go test ./...` ban đầu bị chặn vì Go build cache mặc định nằm ngoài vùng writable; chưa phải lỗi code.
- Chạy lại với `GOCACHE=/tmp/project3-review-go-cache`; kết quả cập nhật bên dưới.
- Lần chạy với cache writable: package limiter PASS (integration Redis skip khi không có `REDIS_TEST_ADDR`); HTTP/loadgen chưa chạy được trong sandbox vì `httptest` bind port bị `operation not permitted`. Phải dùng log chạy có quyền socket của agent chính, không diễn giải lỗi môi trường thành lỗi implementation.

## Review scripts

Runner dùng project Compose riêng, từ chối container đã tồn tại, đặt namespace mỗi case, pause chỉ Redis của lab, trap unpause trước khi down; lưu requested/completed timestamps và config đã resolve. Test cleanup mô phỏng cả exit thành công và exit lỗi.

Khuyến nghị R4 (P2, độ bền phép đo): `scripts/lab-common.sh` và `scripts/redis-outage.sh` gọi curl/Redis INFO chưa có wall-clock timeout. Thời gian pause được chặn ở 2s nhưng thu thập evidence có thể treo nếu dịch vụ không hồi phục. Thêm timeout cho các lệnh này hoặc ghi rõ chỉ fault window là bounded, không khẳng định toàn runner có deadline.

## Kết quả re-review sau sửa

| Finding | Trạng thái | Bằng chứng đọc lại |
| --- | --- | --- |
| R1 | Đã sửa | Generator dùng POST; API nhận POST `/work`; test mixed traffic kiểm tra method. Chưa có test tái hiện disconnect sau server nhận request. |
| R2 | Đã sửa | Test Redis nhóm tổng request và allow theo từng window, dùng `min(total, Limit)`. |
| R3 | Đã sửa | Nhánh lỗi lấy lại `time.Now()` sau limiter trả về; `TestAPILimiterDeadline` kiểm timestamp sau timeout; cancellation có counter/test riêng. |
| R4 | Đã sửa | curl `--max-time 5`; INFO có timeout 5s; pause/unpause/logs có timeout 10s; cleanup down có timeout 30s. Build và khởi tạo Compose vẫn không có global wall-clock deadline. |

Không còn finding implementation chặn commit được nhận diện sau lần đọc lại. Điều này không thay thế kiểm thử tích hợp và không chứng minh độ đúng của mọi workload; các giới hạn nghiên cứu ở trên vẫn còn.

Reviewer đã chạy thêm thành công sau sửa (cache writable):

- `go test -race ./internal/limiter`: PASS; Redis integration skip vì không đặt `REDIS_TEST_ADDR` ở lượt reviewer.
- Nhóm test server không cần socket: deadline/fallback timestamp, cancellation không fail-open, backend capacity/metrics, backend cancellation release, config validation: PASS.
- Nhóm test experiment không cần socket: status/goodput accounting, pre-canceled scheduling, bounded config validation: PASS.
- `bash scripts/test-scripts.sh`: PASS, xác nhận thứ tự unpause → down và giữ exit status 0/9.
