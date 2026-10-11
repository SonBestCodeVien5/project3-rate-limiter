# Sửa lỗi, kiểm thử lại và smoke toàn luồng

## Sửa theo review

| ID | Sửa | Kiểm chứng |
| --- | --- | --- |
| R1 | Generator/API dùng POST; upstream backend POST; Nginx tắt retry | Test method/redirect, review transport; 7 lượt smoke không có transport error |
| R2 | FW concurrent test so allow với min(số quyết định trong window, Q) | Redis thật + race test chạy lại PASS |
| R3 | Timestamp fallback sau khi limiter trả lỗi; tách request canceled | Delayed-error timestamp và cancellation test PASS |
| R4 | Timeout curl/Redis INFO/pause/unpause/logs/cleanup | Shell checks, mocked cleanup success/failure, outage thật PASS |

Review xác nhận đã đóng R1–R4; không còn finding chặn. Chưa test chủ động mất response HTTP sau lúc server nhận request; POST semantics được review nhưng ca regression network đó vẫn là giới hạn.

## Verify pipeline

Lệnh: `GOCACHE=/tmp/project3-go-cache REDIS_TEST_ADDR=127.0.0.1:16380 bash scripts/verify.sh`.

Kết quả **PASS**: gofmt, go vet, `go test -race ./...` (bao gồm Redis thật và HTTP), go build, bash syntax, cleanup tests, Compose validation. [Log](verify.log). Test Redis ban đầu dùng image `redis:7.4-alpine`, digest `sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499`; Compose smoke dùng `redis:7.4.2-alpine` và kiểm thử toàn luồng thực tế. [Image IDs/digests](image-digests.txt); Dockerfile base digests cũng nằm trong build log ở archive.

## Mixed smoke/pilot — số đo quan sát

Lệnh: `GOCACHE=/tmp/project3-go-cache bash scripts/pilot-matrix.sh artifacts/bootstrap-pilot`.

Mỗi case: 5s, tổng 300 RPS gồm 20 legitimate RPS/5 client và 280 RPS từ 1 client abusive, 2 API, backend capacity 10/service time 50ms. Policy mặc định Q=B=20, W=1s, r=20/s. Backend và state reset mỗi case. Không warm-up, không lặp; chưa phải so sánh thống kê công bằng giữa các pha biên cửa sổ.

| Cấu hình | Gửi | 2xx | 429 | 5xx | Backend arrivals | Legitimate goodput/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Không limiter | 1500 | 937 | 0 | 563 | 1500 | 9.31 |
| Local Fixed Window | 1500 | 239 | 1189 | 72 | 311 | 17.06 |
| Local Token Bucket | 1500 | 318 | 1162 | 20 | 338 | 19.34 |
| Redis Fixed Window | 1500 | 177 | 1280 | 43 | 220 | 18.99 |
| Redis Token Bucket | 1500 | 211 | 1281 | 8 | 219 | 19.76 |

Goodput dùng elapsed gồm final drain. Tất cả case không generator drop/transport error; mỗi API nhận 750 request. Số arrivals khớp backend counters. 429 là quota reject, không gộp với 5xx. Số đo cho thấy workload tạo được overload để pilot tiếp; không đủ để xếp hạng thuật toán hay kết luận mức bảo vệ tổng quát.

## Redis outage smoke

Lệnh: `GOCACHE=/tmp/project3-go-cache bash scripts/redis-outage.sh artifacts/bootstrap-outage`.

Mỗi case 10s/100 RPS, legitimate 20 RPS/5 client, FW; yêu cầu pause khoảng giây 3, sleep 2s rồi unpause. `outage-events.txt` lưu thời điểm request/completed của thao tác; thời gian Redis unavailable thực tế bao gồm chi phí lệnh và timeout, không mặc định đúng 2.000s.

| Policy | Gửi | Allow | Reject 429 | Fallback | 2xx | 5xx | Backend arrivals |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fail-open | 1000 | 337 | 427 | 236 | 569 | 4 | 573 |
| Fail-closed | 1000 | 331 | 435 | 234 | 328 | 237 | 331 |

Fallback fail-closed là 503, không phải quota reject. Sau unpause, 50 request cuối mỗi case đều trở lại allow/reject. Đây là quan sát phục hồi chức năng, chưa là chỉ số recovery theo ngưỡng ổn định, chưa tính quota violation hoặc outage availability theo pha. Redis pause giữ state; không mô phỏng mất dữ liệu/restart/failover.

## Toàn vẹn evidence và tái kiểm tra

- [artifact-check.log](artifact-check.log) xác nhận 9.500 record, request ID duy nhất trong mỗi run, số status/arrivals đúng, reject/closed không tới backend và có cả hai API.
- [check-artifacts.py](check-artifacts.py) là script kiểm tra các trace smoke cụ thể, không phải oracle correctness dùng cho mọi workload.
- [Mixed archive](evidence/bootstrap-pilot.tar.gz), [outage archive](evidence/bootstrap-outage.tar.gz) chứa JSONL, metadata, summary, config resolved, resource/logs/events; bỏ binary để repo nhỏ.
- [Checksum archive](evidence/archive-sha256.json) và [checksum source](evidence/source-sha256.json) nối số liệu với code thực chạy. Metadata giữ nguyên revision/dirty status tại thời điểm đo trước khi chuỗi commit hoàn tất; không sửa thành trạng thái sạch giả. Các commit sau chỉ tổ chức code/tài liệu đã đo.

Giải nén từ repo root (nên dùng thư mục mới nếu đã có artifacts):

```bash
tar -xzf docs/worklog/2026-10-11-bootstrap/06-retest/evidence/bootstrap-pilot.tar.gz
tar -xzf docs/worklog/2026-10-11-bootstrap/06-retest/evidence/bootstrap-outage.tar.gz
python3 docs/worklog/2026-10-11-bootstrap/06-retest/check-artifacts.py
```

Runner đã tự dọn project `project3-lab`; container Redis integration riêng cũng được xóa. Image build được giữ để lần sau chạy nhanh. Có warning Docker plugin ngoài repo bị thiếu binary; không ảnh hưởng exit code/build/run trong các lượt này. Không suy snapshots Redis CPU thành CPU utilization hoặc lấy pilot một lượt làm kết luận RQ1–RQ5.
