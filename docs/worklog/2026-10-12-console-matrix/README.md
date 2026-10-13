# Console và ma trận pilot thực chạy ngày 12/10/2026

Hồ sơ được tổng hợp và đối chiếu ngày 13/10/2026. Console là lựa chọn kỹ thuật phục vụ demo; yêu cầu nghiên cứu vẫn theo [Roadmap nguồn](../../context/sources/00_Project3_Roadmap.md). Bộ này kiểm tra các tổ hợp cấu hình hiện có và thu dữ liệu pilot; protocol nghiên cứu chưa khóa.

## Tiến độ có bằng chứng

Runner tùy chỉnh được commit ở `a6d1720`, controller/giao diện ở `0e419d1`, tài liệu ở `018a0a2`. Metadata của cả 84 lượt ghi revision `018a0a2facc9fa56d3defa074c74bd01bc42e74a`; trạng thái Git tại thời điểm chạy được giữ trong archive. Có kiểm chứng Console bằng Playwright desktop/mobile ở vòng triển khai trước ma trận; ma trận sau đó gửi qua HTTP API của Console và runner Docker, không phải 84 thao tác form bằng Playwright.

84/84 lượt có trạng thái `completed`; mỗi lượt có trace, summary, analysis, policy, Compose resolved, metrics trước/sau, log và cấu hình yêu cầu. Counter backend arrivals/success và tổng API requests/rejected khớp số liệu phía generator ở cả 84 lượt. Trạng thái hoàn tất và sự nhất quán artifact không chứng minh correctness của mọi quyết định.

## Phương pháp và cấu hình thực tế

Ma trận gồm 4 profile × 7 tổ hợp limiter hợp lệ × 3 topology = 84 lượt, mỗi tổ hợp chạy một lần, thời lượng tạo tải 3 giây. Topology là 1/2/4 API cùng một backend. Bảy tổ hợp gồm none/Fixed Window/closed; local/Fixed Window/closed; local/Token Bucket/closed; Redis/Fixed Window/closed hoặc open; Redis/Token Bucket/closed hoặc open. Thuật toán ở mode none chỉ là nhãn tương thích request.

Policy: `Q=20`, `W=1000ms`, `B=20`, `r=20/s`; backend capacity 10 request đang xử lý đồng thời, service time 50ms. Generator dùng 5 client hợp lệ, một key bất thường, max-inflight 200, timeout 2s. Runner chờ 1 giây sau health check, không gửi tải warm-up; namespace và container mới theo từng lượt. Dùng `request.json`, `policy.json`, Compose resolved và metadata của từng Run ID để tái hiện chính xác.

| Profile | Workload đã cấu hình | Dự kiến mỗi lượt |
| --- | --- | ---: |
| Normal | Toàn bộ 120 RPS hợp lệ, chia 5 key | 360 |
| Mixed | Tổng 120 RPS: 20 hợp lệ + 100 bất thường | 360 |
| Burst | Nền giống mixed; luồng bất thường tăng lên 200 RPS từ giây 1 đến giây 2, tải hợp lệ vẫn 20 RPS | 460 |
| Concurrent | 100 request cùng key được lên lịch tại giây 2; legitimate RPS = 0; trường RPS chỉ là nhãn | 100 |

Không chủ động pause Redis trong bộ này. Tuy nhiên có lỗi thao tác Redis và fallback thực tế, được giữ trong kết quả dưới đây. Lượt đầu là `20261012T024459-b925d79d4ac9`, lượt cuối `20261012T031814-e1a422eb4f49`.

## Kết quả đo và ý nghĩa metric

| Profile (21 lượt mỗi nhóm) | Đã gửi | 2xx | 429 | 5xx | Backend arrivals | Backend overload | Generator drops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Normal | 7.560 | 7.274 | 286 | 0 | 7.274 | 0 | 0 |
| Mixed | 7.560 | 4.113 | 3.441 | 6 | 4.113 | 0 | 0 |
| Burst | 9.655 | 4.282 | 5.204 | 169 | 4.450 | 168 | 5 |
| Concurrent | 2.100 | 260 | 1.253 | 587 | 847 | 587 | 0 |
| **Tổng** | **26.875** | **15.929** | **10.184** | **762** | **16.684** | **755** | **5** |

26.880 request được lên lịch, 26.875 được gửi và nhận phản hồi HTTP; không có transport error hoặc timeout phía load generator. HTTP 2xx chiếm 59,27%, 429 chiếm 37,89%, 5xx chiếm 2,84% tổng đã gửi. Đây là tổng nhiều workload/cấu hình, không dùng làm bảng xếp hạng thuật toán.

| Metric | Định nghĩa và nguồn tham chiếu |
| --- | --- |
| Backend arrivals | Backend đã nhận request, đếm trước admission. Dùng `backend-after.json.arrivals - backend-before.json.arrivals`. |
| Backend success | Request được admission và hoàn thành service time; lấy delta `success` phía backend. |
| Backend overload | Request đã tới backend nhưng hết slot xử lý đồng thời, bị từ chối admission và trả HTTP 503; lấy delta `overload`. |
| Backend canceled | Request đã admission nhưng context bị hủy trước hoàn thành; lấy delta `canceled`. Bộ này có delta bằng 0. |
| HTTP 429 | Kết quả quota reject phía client; đối chiếu tổng delta `rejected` của mọi API. Request này không gọi backend. |
| HTTP 5xx | Kết quả lỗi HTTP phía client; cần attribution theo backend/API counters và trace, không thay cho overload. |
| Fail-open/fail-closed | Tổng delta `fail_open`/`fail_closed` trên **mọi API instance**, không chỉ API1. |
| Goodput/P95 hợp lệ | Goodput dùng thời gian thực gồm drain; P95 dùng request hợp lệ thành công. Không có mẫu thì không có latency hợp lệ. |

Nguồn semantics là [backend handler](../../../internal/server/server.go) và [thiết kế](../../IMPLEMENTATION.md). Các số liệu dẫn xuất trong CSV đều lấy delta snapshot trước/sau. Trong bộ này, `16.684 arrivals = 15.929 success + 755 overload`, và `762 HTTP 5xx = 755 overload + 7 fail-closed`. Hai đẳng thức được đối chiếu từng lượt; chúng không phải quy tắc attribution chung khi có mất phản hồi/transport error.

Goodput hợp lệ trung bình giữa các lượt: normal 113,8/s, mixed 19,9/s, burst 19,4/s; trung bình P95 của từng lượt tương ứng 53,8/54,2/54,9ms. Đây không phải percentile gộp từ tất cả trace. Concurrent không có client hợp lệ, nên goodput/P95 hợp lệ là không áp dụng; số 0 trong summary nghĩa là không có mẫu.

## Kết quả cần giữ và điều tra

* Hai lượt burst có `schedule_backlog`: lượt 50 (local Token Bucket, 2 API) bỏ 4 request; lượt 58 (Redis Token Bucket closed, 1 API) bỏ 1. Giữ dữ liệu để phân tích tooling, không coi offered load đạt đủ cho phép so sánh chính thức.
* Cộng mọi API cho thấy **19 limiter errors**, gồm **12 fail-open và 7 fail-closed**. Các lượt 13, 21, 37, 58, 62 có lỗi limiter; logs ghi Redis I/O timeout. Nguyên nhân timeout chưa được kết luận; đây không phải lỗi transport phía load generator.
* Analyzer ghi 12 `not_applicable`, 30 `no_violation_observed_within_trace`, 40 `inconclusive`, **2 `observed_violations`**. Hai lượt local Token Bucket là lượt 29 (mixed, 2 API, `20261012T025545-ea44194c1d29`) và lượt 49 (burst, 1 API, `20261012T030353-a2b3f479b6a3`). Finding là `token_bucket_decision_mismatch` với expected allow nhưng observed reject. Cần đối chiếu semantics/precision/timestamp giữa limiter và oracle trước khi quy nguyên nhân; không diễn giải finding này thành overshoot đã xác nhận.

`quality_flags` trong CSV đánh dấu drops, limiter errors và oracle findings; các lượt còn lại vẫn có thể mang oracle `inconclusive`. Số liệu trước đây chỉ cộng API1 thấy 14 limiter errors; hồ sơ này dùng tổng của tất cả API và cập nhật thành 19. Tổng 755 overload và 7 fail-closed không đổi.

## Tham chiếu và tái kiểm tra

* [CSV 84 lượt](matrix-report.csv): Run ID, cấu hình, HTTP metrics, backend delta, tổng API counters, oracle status và quality flags.
* [JSON tổng hợp](matrix-report.json): phạm vi, tổng toàn bộ, tổng theo profile và từng lượt.
* [Archive dữ liệu gốc](evidence/console-matrix-artifacts.tar.gz): giữ các thư mục `artifacts/console/<Run ID>/` của 84 lượt, bao gồm request/status, metadata/JSONL, metrics/config/policy/logs/analysis; bỏ binary loadgen.
* [Manifest SHA256](evidence/manifest.json): revision lúc đo, checksum archive và input dùng để đối chiếu. Archive và bảng tổng hợp được lưu cùng worklog trong Git để tham chiếu sau khi dọn `artifacts/`.

Từ repo root, giải nén archive vào workspace thử nghiệm rồi phân tích lại từng case bằng analyzer hiện hữu:

```bash
tar -xzf docs/worklog/2026-10-12-console-matrix/evidence/console-matrix-artifacts.tar.gz
python3 scripts/analyze.py artifacts/console/20261012T025545-ea44194c1d29/result/custom-repeat-1
```

Analyzer ghi lại `analysis.*`; dùng bản giải nén để giữ evidence đã archive. Checksum lưu trong manifest cho phép xác nhận input gốc trước khi phân tích lại. CSV/JSON là bảng dẫn xuất, raw snapshots/trace/config mới là bằng chứng đo ban đầu.

Kiểm tra hồ sơ ngày 13/10: checksum archive và 1.148 input được xác nhận; CSV trong archive khớp bản worklog, tổng JSON khớp 84 dòng CSV, các đẳng thức backend/HTTP/fallback được kiểm tra từng lượt và các liên kết tài liệu local tồn tại. Không chạy lại benchmark trong lần cập nhật tài liệu này.

## Giới hạn và bước tiếp theo

Một lượt 3 giây mỗi tổ hợp kiểm tra phạm vi cấu hình, chưa đánh giá độ dao động, throughput scaling hay trả lời đầy đủ RQ1–RQ5. Không lấy nhóm có số lượt khác nhau hoặc khác thuật toán/policy làm phép so sánh nhân quả bằng tổng counts. `normal` trong generator chỉ nghĩa toàn bộ traffic hợp lệ: 120 RPS / 5 key = 24 RPS/key vượt tốc độ FW 20/key/s, nên 429 tại normal có thể phù hợp quota; đây chưa phải baseline tải dưới quota. Mixed 120 RPS với capacity10/service50ms không tạo backend overload; cần nhóm hiệu chỉnh capacity4 trong [pilot vòng 2](../2026-10-11-measurement/06-retest/RETEST.md) để tham khảo bài toán overload trước khi khóa tham số mới.

Cần điều tra hai oracle mismatch và Redis timeouts, hiệu chỉnh generator cho burst, chọn baseline dưới quota và tải mixed gây overload có kiểm soát, rồi khóa số lượt lặp/thời lượng/warm-up. Outage phải dùng thí nghiệm riêng với timestamp pause/unpause và tiêu chí recovery chọn trước. Bộ này có thể dẫn trong báo cáo như kết quả pilot có giới hạn; chưa xác nhận benchmark nghiên cứu chính thức.
